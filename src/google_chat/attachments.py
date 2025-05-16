import os
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import mimetypes

from src.google_chat.auth import get_credentials
from src.google_chat.messages import create_message


async def upload_attachment(space_name: str, file_path: str, message_text: str = None) -> dict:
    """Upload a file attachment to a Google Chat space.

    Args:
        space_name: The name/identifier of the space to send the attachment to
        file_path: Path to the file to upload
        message_text: Optional text message to accompany the attachment

    Returns:
        The created message object

    Raises:
        Exception: If authentication fails or upload fails
    """
    try:
        creds = get_credentials()
        if not creds:
            raise Exception("No valid credentials found. Please authenticate first.")

        service = build('chat', 'v1', credentials=creds)

        if not space_name.startswith('spaces/'):
            space_name = f"spaces/{space_name}"

        # Validate file exists
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Get mimetype
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = 'application/octet-stream'

        # Create media upload
        media = MediaFileUpload(
            str(file_path),
            mimetype=mime_type,
            resumable=True
        )

        # First, upload the file to get attachment data
        upload_response = service.media().upload(
            parent=space_name,
            body={'filename': os.path.basename(str(file_path))},
            media_body=media
        ).execute()

        # Then create a message with the attachment
        message_body = {}
        if message_text:
            message_body["text"] = message_text

        message_body["attachment"] = [upload_response]

        # Send the message with attachment
        response = service.spaces().messages().create(
            parent=space_name,
            body=message_body
        ).execute()

        return response

    except Exception as e:
        raise Exception(f"Failed to upload attachment: {str(e)}")


async def send_file_message(space_name: str, file_path: str, message_text: str = None) -> dict:
    """Send a message with file contents (simplified attachment alternative).

    This is a simplified alternative to file attachments that reads the file
    and sends its contents in the message text.

    Args:
        space_name: The name/identifier of the space to send the message to
        file_path: Path to the file whose contents will be included in the message
        message_text: Optional text message to accompany the file contents

    Returns:
        The created message object

    Raises:
        Exception: If authentication fails or message creation fails
    """
    try:
        creds = get_credentials()
        if not creds:
            raise Exception("No valid credentials found. Please authenticate first.")

        # Validate file exists
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Read file contents (limit to first 5000 characters)
        try:
            with open(file_path, 'r') as f:
                file_contents = f.read(5000)
                if len(file_contents) >= 5000:
                    file_contents += "\n... [content truncated] ..."
        except UnicodeDecodeError:
            # Handle binary files
            file_contents = "[Binary file content not shown]"

        # Build message text
        full_message = ""
        if message_text:
            full_message += f"{message_text}\n\n"

        full_message += f"📄 *File: {file_path.name}*\n"
        full_message += "```\n"
        full_message += file_contents
        full_message += "\n```"

        # Send message
        return await create_message(space_name, full_message)

    except Exception as e:
        raise Exception(f"Failed to send file message: {str(e)}")
