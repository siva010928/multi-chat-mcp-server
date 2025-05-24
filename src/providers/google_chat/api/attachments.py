import os
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import mimetypes

from src.providers.google_chat.api.auth import get_credentials
from src.providers.google_chat.api.messages import create_message


async def upload_attachment(space_name: str, file_path: str, message_text: str = None, thread_key: str = None) -> dict:
    """Upload a file attachment to a Google Chat space.

    Args:
        space_name: The name/identifier of the space to send the attachment to
        file_path: Path to the file to upload
        message_text: Optional text message to accompany the attachment
        thread_key: Optional thread key to reply to. If provided, the attachment
                   will be sent as a reply to the specified thread.

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

        # Add thread information if thread_key is provided
        if thread_key:
            # Try multiple approaches for thread identification to improve reliability
            if thread_key.startswith("spaces/") and "/threads/" in thread_key:
                # Full thread name provided (spaces/*/threads/*) - use it directly
                message_body["thread"] = {"name": thread_key}
            elif thread_key.startswith("threads/"):
                # Thread key starts with "threads/" - extract the ID
                thread_id = thread_key.replace("threads/", "")
                message_body["thread"] = {"threadKey": thread_id}
            else:
                # Simple thread key or ID - try to use it directly
                message_body["thread"] = {"threadKey": thread_key}

        # Send the message with attachment
        response = service.spaces().messages().create(
            parent=space_name,
            messageReplyOption="REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD" if thread_key else None,
            body=message_body
        ).execute()

        return response

    except Exception as e:
        raise Exception(f"Failed to upload attachment: {str(e)}")


async def send_file_message(space_name: str, file_path: str, message_text: str = None, thread_key: str = None) -> dict:
    """Send a message with file contents (simplified attachment alternative).

    This is a simplified alternative to file attachments that reads the file
    and sends its contents in the message text. The file content can be sent
    as a new message or as a reply to an existing thread.

    Args:
        space_name: The name/identifier of the space to send the message to
        file_path: Path to the file whose contents will be included in the message
        message_text: Optional text message to accompany the file contents
        thread_key: Optional thread key to reply to. If provided, the file content
                   will be sent as a reply to the specified thread.

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

        # If thread_key is provided, send as a reply to the thread
        if thread_key:
            from src.providers.google_chat.api.messages import reply_to_thread
            return await reply_to_thread(space_name, thread_key, full_message)
        else:
            # Send as a new message
            return await create_message(space_name, full_message)

    except Exception as e:
        raise Exception(f"Failed to send file message: {str(e)}")


async def send_file_content(space_name: str, file_path: str = None, thread_key: str = None) -> dict:
    """Send file content as a message (workaround for attachments).

    This is a simplified alternative to file attachments that reads the file
    and sends its contents in the message text. The file content can be sent
    as a new message or as a reply to an existing thread.

    Args:
        space_name: The space to send the message to
        file_path: Optional path to the file to send. If not provided, will use sample_attachment.txt
        thread_key: Optional thread key to reply to. If provided, the file content
                   will be sent as a reply to the specified thread.

    Returns:
        The created message object

    Raises:
        Exception: If authentication fails or message creation fails
    """
    import os

    try:
        # Default to sample_attachment.txt if no file specified
        if not file_path:
            file_path = "sample_attachment.txt"

        # Create sample file if it doesn't exist
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                f.write("This is a sample attachment file created for testing the Google Chat MCP tools.\n")
                f.write("Line 2: This demonstrates our workaround for file sharing.\n")
                f.write("Line 3: The actual attachment upload API needs more work.\n")

        # Read file contents
        try:
            with open(file_path, 'r') as f:
                file_contents = f.read(4000)  # Limit to 4000 chars
        except Exception:
            file_contents = "[Error reading file]"

        # Format the message
        message = f"📄 **File Content: {os.path.basename(file_path)}**\n\n```\n{file_contents}\n```"

        if not space_name.startswith('spaces/'):
            space_name = f"spaces/{space_name}"

        # If thread_key is provided, send as a reply to the thread
        if thread_key:
            from src.providers.google_chat.api.messages import reply_to_thread
            return await reply_to_thread(space_name, thread_key, message)
        else:
            # Send as a new message
            return await create_message(space_name, message)

    except Exception as e:
        raise Exception(f"Failed to send file content: {str(e)}")
