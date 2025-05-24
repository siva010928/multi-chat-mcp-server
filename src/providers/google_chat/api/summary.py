import datetime
from typing import Optional, Dict, List

from googleapiclient.discovery import build

from src.providers.google_chat.api.auth import get_credentials, get_current_user_info
from src.providers.google_chat.api.messages import list_space_messages
from src.providers.google_chat.api.spaces import list_chat_spaces
from src.providers.google_chat.utils import rfc3339_format


async def get_my_mentions(days: int = 7, spaces: Optional[List[str]] = None, include_sender_info: bool = True,
                          page_size: int = 50, page_token: Optional[str] = None, offset: int = 0) -> Dict:
    """Gets messages that mention the authenticated user from all spaces or specific spaces.

    Args:
        days: Number of days to look back for mentions (default: 7)
        spaces: Optional list of space IDs to check for mentions in specific spaces.
                If provided, searches only these spaces. If None (default), searches all accessible spaces.
                For a single space, provide a list with one element, e.g., ["spaces/AAQAtjsc9v4"]
        include_sender_info: Whether to include sender information in the returned messages (default: True)
        page_size: Maximum number of messages to return per space (default: 50)
        page_token: Optional page token for pagination (only applicable when searching a single space)
        offset: Number of days to offset the end date from today (default: 0)

    Returns:
        Dictionary containing messages where the user is mentioned
    """
    # Validate parameters
    if days <= 0:
        raise ValueError("days must be positive")

    if offset < 0:
        raise ValueError("offset cannot be negative")

    try:
        creds = get_credentials()
        if not creds:
            raise Exception("No valid credentials found. Please authenticate first.")

        service = build('chat', 'v1', credentials=creds)

        # Get user information to find the username
        try:
            user_info = await get_current_user_info()
            username = user_info.get('display_name')
            if not username:
                # Fall back to email if no display name
                username = user_info.get('email')
        except Exception as e:
            # If we can't get the user info, try to get email from credentials
            try:
                # Check if id_token is a dictionary that we can use get() on
                if hasattr(creds, 'id_token') and isinstance(creds.id_token, dict):
                    username = creds.id_token.get('email', '')
                # If id_token is a string, we can't use get() method
                elif hasattr(creds, 'id_token') and isinstance(creds.id_token, str):
                    username = creds.id_token  # Just use the string as is
                else:
                    # Last resort fallback
                    username = "current_user"  # Generic fallback username
            except Exception:
                username = "current_user"  # Generic fallback username

        if not username:
            raise Exception("Could not determine username for mentions")

        # Helper function to process messages from a space and filter for mentions
        async def process_space_messages(space_name, include_page_token=False):
            if not space_name.startswith('spaces/'):
                space_name = f"spaces/{space_name}"

            # Get messages from the specific space
            messages_result = await list_space_messages(
                space_name,
                include_sender_info=include_sender_info,
                page_size=page_size,
                page_token=page_token if include_page_token else None,
                order_by="createTime desc",  # Default to newest first
                days_window=days,
                offset=offset
            )
            messages = messages_result.get('messages', [])
            next_page_token = messages_result.get('nextPageToken') if include_page_token else None

            # Filter messages that mention the user by username
            mention_messages = []
            for msg in messages:
                text = msg.get("text", "")
                # Check if the username is in the text (could be in the form @username or just username)
                # Also check for common mention patterns and annotations
                is_mention = False

                # Check for username in text (case insensitive)
                if username.lower() in text.lower() or f"@{username.lower()}" in text.lower():
                    is_mention = True

                # Check for annotations that might indicate mentions
                annotations = msg.get("annotations", [])
                for annotation in annotations:
                    # Check if this annotation is a user mention
                    if annotation.get("type") == "USER_MENTION":
                        # If we have user info, check if it matches current user
                        mentioned_user = annotation.get("userMention", {})
                        if mentioned_user:
                            # If we have a direct match on user ID
                            if "user" in mentioned_user and mentioned_user.get("user", {}).get("name") == user_info.get("name"):
                                is_mention = True
                                break

                # Only include messages that are actual mentions
                # is_mention is already set based on the checks above

                if is_mention:
                    # Add the space information to the message
                    msg["space_info"] = {
                        "name": space_name
                    }
                    # Try to get the space display name
                    try:
                        space_details = service.spaces().get(name=space_name).execute()
                        msg["space_info"]["displayName"] = space_details.get("displayName", "Unknown Space")
                    except:
                        msg["space_info"]["displayName"] = "Unknown Space"

                    mention_messages.append(msg)

            return mention_messages, next_page_token

        # If spaces list is provided with a single space, we can use pagination
        if spaces and len(spaces) == 1:
            mention_messages, next_page_token = await process_space_messages(spaces[0], include_page_token=True)

            return {
                'messages': mention_messages,
                'nextPageToken': next_page_token
            }

        # If spaces list is provided with multiple spaces
        elif spaces and len(spaces) > 1:
            all_mentions = []

            # Process each space in the provided list
            for space_name in spaces:
                if not space_name:
                    continue

                try:
                    mentions, _ = await process_space_messages(space_name)
                    all_mentions.extend(mentions)
                except Exception as e:
                    # If we fail to get messages from one space, continue with others
                    continue

            return {
                'messages': all_mentions,
                'nextPageToken': None  # No pagination when searching across multiple spaces
            }

        # If neither space_id nor spaces is provided, search across all spaces
        else:
            # Get all spaces
            spaces_response = await list_chat_spaces()
            spaces_to_search = [space.get("name") for space in spaces_response if space.get("name")]

            all_mentions = []

            # For each space, get messages and filter for mentions
            for space_name in spaces_to_search:
                if not space_name:
                    continue

                try:
                    # Use the helper function to process messages from this space
                    mentions, _ = await process_space_messages(space_name)
                    all_mentions.extend(mentions)
                except Exception:
                    # If we fail to get messages from one space, continue with others
                    continue

            return {
                'messages': all_mentions,
                'nextPageToken': None  # No pagination when searching across all spaces
            }

    except Exception as e:
        raise Exception(f"Failed to get user mentions: {str(e)}")


async def get_conversation_participants(space_name: str,
                                        max_messages: int = 100,
                                        days_window: int = 3,
                                        offset: int = 0) -> List[Dict]:
    """Gets information about participants in a conversation or space.

    Args:
        space_name: The name/identifier of the space
        max_messages: Maximum number of messages to check for participants (default: 100)
        days_window: Number of days to look back for messages (default: 3).
                    This parameter controls the date range for message retrieval.
                    For example, if days_window=3, messages from the last 3 days will be retrieved.
        offset: Number of days to offset the end date from today (default: 0). 
               For example, if offset=3, the end date will be 3 days before today,
               and with days_window=3, messages from 6 to 3 days ago will be retrieved.

    Returns:
        List of unique participants with their information

    Raises:
        Exception: If authentication fails or API request fails
    """
    # Validate parameters
    if days_window <= 0:
        raise ValueError("days_window must be positive")

    if offset < 0:
        raise ValueError("offset cannot be negative")

    try:
        # Get messages with sender info
        result = await list_space_messages(
            space_name,
            include_sender_info=True,
            page_size=max_messages,
            order_by="createTime desc",  # Default to newest first
            days_window=days_window,
            offset=offset
        )
        messages = result.get('messages', [])

        # Extract unique participants with info
        participants = {}
        for message in messages:
            if "sender_info" in message and "id" in message["sender_info"]:
                sender_id = message["sender_info"]["id"]
                if sender_id not in participants:
                    participants[sender_id] = message["sender_info"]

        return list(participants.values())

    except Exception as e:
        raise Exception(f"Failed to get conversation participants: {str(e)}")


async def summarize_conversation(space_name: str,
                                 message_limit: int = 10,
                                 page_token: Optional[str] = None,
                                 filter_str: Optional[str] = None,
                                 days_window: int = 3,
                                 offset: int = 0) -> Dict:
    """Generates a summary of a conversation in a space.

    Args:
        space_name: The name/identifier of the space
        message_limit: Maximum number of messages to include in summary
        page_token: Optional page token for pagination
        filter_str: Optional filter string in the format specified by Google Chat API
        days_window: Number of days to look back for messages (default: 3).
                    This parameter controls the date range for message retrieval.
                    For example, if days_window=3, messages from the last 3 days will be retrieved.
        offset: Number of days to offset the end date from today (default: 0). 
               For example, if offset=3, the end date will be 3 days before today,
               and with days_window=3, messages from 6 to 3 days ago will be retrieved.

    Returns:
        Dictionary containing space information, participants, and recent messages

    Raises:
        Exception: If authentication fails or API request fails
    """
    # Validate parameters
    if days_window <= 0:
        raise ValueError("days_window must be positive")

    if offset < 0:
        raise ValueError("offset cannot be negative")

    try:
        # Get space details
        creds = get_credentials()
        if not creds:
            raise Exception("No valid credentials found. Please authenticate first.")

        service = build('chat', 'v1', credentials=creds)
        space_details = service.spaces().get(name=space_name).execute()

        # Get messages with sender info
        result = await list_space_messages(
            space_name,
            include_sender_info=True,
            page_size=message_limit,
            page_token=page_token,
            filter_str=filter_str,
            order_by="createTime desc",  # Default to newest first
            days_window=days_window,
            offset=offset
        )
        messages = result.get('messages', [])
        next_page_token = result.get('nextPageToken')

        # Extract unique participants with info
        participants = {}
        for message in messages:
            if "sender_info" in message and "id" in message["sender_info"]:
                sender_id = message["sender_info"]["id"]
                if sender_id not in participants:
                    participants[sender_id] = message["sender_info"]

        # Build summary
        summary = {
            "space": {
                "name": space_details.get("name"),
                "display_name": space_details.get("displayName", "Unknown Space"),
                "type": space_details.get("type", "Unknown Type")
            },
            "participants": list(participants.values()),
            "participant_count": len(participants),
            "messages": messages,
            "message_count": len(messages),
            "nextPageToken": next_page_token
        }

        return summary

    except Exception as e:
        raise Exception(f"Failed to summarize conversation: {str(e)}")
