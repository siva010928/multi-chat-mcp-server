import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone, timedelta

from googleapiclient.discovery import build

from src.providers.google_chat.api.auth import get_credentials, get_user_info_by_id
from src.providers.google_chat.utils import create_date_filter

# Set up logging
logger = logging.getLogger("messages")


async def list_space_messages(space_name: str,
                              include_sender_info: bool = False,
                              page_size: int = 25,
                              page_token: Optional[str] = None,
                              filter_str: Optional[str] = None,
                              order_by: Optional[str] = None,
                              show_deleted: bool = False,
                              days_window: int = 3,
                              offset: int = 0) -> Dict:
    """Lists messages from a specific Google Chat space with optional time filtering.

    Args:
        space_name: The name/identifier of the space to fetch messages from
        include_sender_info: Whether to include sender info in the results (default: False)
        page_size: Maximum number of messages to return (default: 25)
        page_token: Optional page token for pagination
        filter_str: Optional filter string in the Google Chat API format
                   (see API reference for format)
        order_by: How to order the messages, e.g., "createTime desc"
        show_deleted: Whether to include deleted messages (default: False)
        days_window: Number of days to look back (default: 3)
        offset: Number of days to offset the end date from today (default: 0)

    Returns:
        Dictionary containing messages and other metadata
    """
    # Validate parameters
    if days_window <= 0:
        raise ValueError("days_window must be positive")
    
    if offset < 0:
        raise ValueError("offset cannot be negative")

    # Calculate date range
    today = datetime.now(timezone.utc)
    
    # Calculate end date by subtracting offset days from today
    end_date = today - timedelta(days=offset)
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    # Calculate start date by going back days_window days from the end date
    start_date = end_date - timedelta(days=days_window)
    start_date_str = start_date.strftime('%Y-%m-%d')
    
    logger.info(f"Using calculated date range: {start_date_str} to {end_date_str} " +
                f"(window: {days_window} days, offset: {offset} days)")

    try:
        # Get credentials
        creds = get_credentials()
        service = build('chat', 'v1', credentials=creds)

        # Create date filter
        try:
            # Format dates for the Google Chat API
            date_filter = create_date_filter(start_date_str, end_date_str)

            logger.info(f"Using date filter: {date_filter}")

            # If we already have a filter, append the date filter
            if filter_str:
                filter_str = f"{filter_str} AND ({date_filter})"
            else:
                filter_str = date_filter
        except ValueError as e:
            logger.error(f"Invalid date format: {str(e)}")
            raise ValueError(f"Invalid date format: {str(e)}")

        # Prepare request parameters
        request_params = {'parent': space_name, 'pageSize': min(page_size, 1000)}  # Enforce API limit

        # Add optional parameters if provided
        if filter_str:
            request_params['filter'] = filter_str
        if page_token:
            request_params['pageToken'] = page_token
        if order_by:
            request_params['orderBy'] = order_by
        else:
            # Default to newest messages first if not specified
            request_params['orderBy'] = 'createTime desc'
        if show_deleted:
            request_params['showDeleted'] = show_deleted

        # Make API request
        logger.info(f"Making API request with params: {request_params}")
        response = service.spaces().messages().list(**request_params).execute()

        # Extract messages and next page token
        messages = response.get('messages', [])
        next_page_token = response.get('nextPageToken')

        # Log timestamp details of retrieved messages for debugging date filter issues
        if start_date_str and len(messages) > 0:
            logger.info(f"Date filtering: First message createTime: {messages[0].get('createTime', 'unknown')}")
            logger.info(f"Date filtering: Looking for messages on/after: {start_date_str}")
            if end_date_str:
                logger.info(f"Date filtering: Looking for messages on/before: {end_date_str}")
        elif start_date_str and len(messages) == 0:
            logger.warning(f"Date filtering: No messages found for filter: {filter_str}")
            logger.warning(f"API response keys: {list(response.keys())}")
            logger.warning(f"API response snippet: {str(response)[:200]}...")

        logger.info(f"Retrieved {len(messages)} messages from space {space_name}")

        # Add sender information if requested
        if include_sender_info:
            for message in messages:
                if "sender" in message and "name" in message["sender"]:
                    sender_id = message["sender"]["name"]
                    try:
                        sender_info = await get_user_info_by_id(sender_id)
                        message["sender_info"] = sender_info
                    except Exception:
                        # If we fail to get sender info, continue with basic info
                        message["sender_info"] = {
                            "id": sender_id,
                            "display_name": f"User {sender_id.split('/')[-1]}"
                        }

        return {
            'messages': messages,
            'nextPageToken': next_page_token
        }

    except Exception as e:
        if isinstance(e, ValueError):
            raise

        logger.error(f"Failed to list messages in space: {str(e)}")

        raise Exception(f"Failed to list messages in space: {str(e)}")


async def create_message(space_name: str, text: str, cards_v2=None) -> Dict:
    """Creates a new message in a Google Chat space.

    Args:
        space_name: The name/identifier of the space to send the message to
        text: Text content of the message
        cards_v2: Optional card content for the message (list of card objects)

    Returns:
        The created message object

    Raises:
        Exception: If authentication fails or message creation fails
    """
    try:
        creds = get_credentials()
        if not creds:
            raise Exception("No valid credentials found. Please authenticate first.")

        service = build('chat', 'v1', credentials=creds)

        # Build message body
        message_body = {"text": text}
        if cards_v2:
            message_body["cardsV2"] = cards_v2

        # Make API request
        response = service.spaces().messages().create(
            parent=space_name,
            body=message_body
        ).execute()

        return response

    except Exception as e:
        raise Exception(f"Failed to create message: {str(e)}")


async def update_message(message_name: str, text: str = None, cards_v2=None) -> Dict:
    """Updates an existing message in a Google Chat space.

    Args:
        message_name: The resource name of the message to update (spaces/*/messages/*)
        text: New text content for the message (optional)
        cards_v2: New card content for the message (optional)

    Returns:
        The updated message object

    Raises:
        Exception: If authentication fails or message update fails
    """
    try:
        creds = get_credentials()
        if not creds:
            raise Exception("No valid credentials found. Please authenticate first.")

        service = build('chat', 'v1', credentials=creds)

        # Build message and update mask
        message_body = {"name": message_name}
        update_mask = []

        if text is not None:
            message_body["text"] = text
            update_mask.append("text")

        if cards_v2 is not None:
            message_body["cardsV2"] = cards_v2
            update_mask.append("cardsV2")

        if not update_mask:
            raise ValueError("At least one of text or cards_v2 must be provided")

        # Make API request
        response = service.spaces().messages().patch(
            name=message_name,
            updateMask=','.join(update_mask),
            body=message_body
        ).execute()

        return response

    except ValueError:
        raise

    except Exception as e:
        raise Exception(f"Failed to update message: {str(e)}")


async def batch_send_messages(messages: List[Dict]) -> Dict:
    """Send multiple messages in batch to different spaces.

    Args:
        messages: List of message objects, each containing:
            - space_name: The name/identifier of the space to send to
            - text: Text content of the message
            - thread_key: Optional thread key to reply to
            - cards_v2: Optional card content

    Returns:
        Dictionary with results for each message

    Raises:
        Exception: If authentication fails
    """
    try:
        results = {
            "successful": [],
            "failed": []
        }

        for idx, msg in enumerate(messages):
            space_name = msg.get("space_name")
            text = msg.get("text", "")
            thread_key = msg.get("thread_key")
            cards_v2 = msg.get("cards_v2")

            if not space_name:
                results["failed"].append({
                    "index": idx,
                    "error": "Missing space_name"
                })
                continue

            try:
                if thread_key:
                    # Reply to thread
                    response = await reply_to_thread(space_name, thread_key, text, cards_v2)
                else:
                    # Create new message
                    response = await create_message(space_name, text, cards_v2)

                results["successful"].append({
                    "index": idx,
                    "message_name": response.get("name"),
                    "space_name": space_name
                })
            except Exception as e:
                results["failed"].append({
                    "index": idx,
                    "space_name": space_name,
                    "error": str(e)
                })

        return results

    except Exception as e:
        raise Exception(f"Failed to batch send messages: {str(e)}")

async def reply_to_thread(space_name: str, thread_key: str, text: str, cards_v2=None) -> Dict:
    """Replies to a thread in a Google Chat space.

    Args:
        space_name: The name/identifier of the space containing the thread
        thread_key: The thread key to reply to. Can be a simple ID, a threadKey, or a full thread name
        text: Text content of the reply
        cards_v2: Optional card content for the reply (list of card objects)

    Returns:
        The created message object

    Raises:
        Exception: If authentication fails or message creation fails
    """
    try:
        creds = get_credentials()
        if not creds:
            raise Exception("No valid credentials found. Please authenticate first.")

        service = build('chat', 'v1', credentials=creds)

        # Build message body
        message_body = {
            "text": text
        }

        # Try multiple approaches for thread identification to improve reliability
        # This uses a tiered approach to thread identification

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

            # Additionally try to find the original message to get its thread name
            try:
                # Try to get the message directly first
                direct_msg = None
                try:
                    direct_msg = service.spaces().messages().get(
                        name=f"{space_name}/messages/{thread_key}.{thread_key}"
                    ).execute()
                except Exception:
                    pass

                # If direct lookup failed, try finding from space messages
                if not direct_msg:
                    space_messages = service.spaces().messages().list(
                        parent=space_name,
                        pageSize=100
                    ).execute().get('messages', [])

                    # Look for messages with matching thread name or threadKey
                    for msg in space_messages:
                        if msg.get("name", "").endswith(thread_key):
                            direct_msg = msg
                            break
                        if "thread" in msg and msg["thread"].get("name", "").endswith(thread_key):
                            direct_msg = msg
                            break

                # If we found a message, use its thread information
                if direct_msg and "thread" in direct_msg and "name" in direct_msg["thread"]:
                    message_body["thread"] = {"name": direct_msg["thread"]["name"]}
            except Exception as e:
                # If thread lookup fails, continue with the simple threadKey approach
                print(f"Thread lookup failed: {str(e)}")

        if cards_v2:
            message_body["cardsV2"] = cards_v2

        # Make API request with appropriate thread options
        response = service.spaces().messages().create(
            parent=space_name,
            messageReplyOption="REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD",
            body=message_body
        ).execute()

        return response

    except Exception as e:
        raise Exception(f"Failed to reply to thread: {str(e)}")


async def get_message(message_name: str, include_sender_info: bool = False) -> Dict:
    """Gets a specific message by its resource name.

    Args:
        message_name: The resource name of the message (spaces/*/messages/*)
        include_sender_info: Whether to include sender information in the returned message (default: False)

    Returns:
        The message object

    Raises:
        Exception: If authentication fails or message retrieval fails
    """
    try:
        creds = get_credentials()
        if not creds:
            raise Exception("No valid credentials found. Please authenticate first.")

        service = build('chat', 'v1', credentials=creds)

        # Make API request
        message = service.spaces().messages().get(name=message_name).execute()

        # Add sender information if requested
        if include_sender_info and "sender" in message and "name" in message["sender"]:
            sender_id = message["sender"]["name"]
            try:
                sender_info = await get_user_info_by_id(sender_id)
                message["sender_info"] = sender_info
            except Exception:
                # If we fail to get sender info, continue with basic info
                message["sender_info"] = {
                    "id": sender_id,
                    "display_name": f"User {sender_id.split('/')[-1]}"
                }

        return message

    except Exception as e:
        raise Exception(f"Failed to get message: {str(e)}")


async def delete_message(message_name: str) -> Dict:
    """Deletes a message by its resource name.

    Args:
        message_name: The resource name of the message (spaces/*/messages/*)

    Returns:
        Empty response on success

    Raises:
        Exception: If authentication fails or message deletion fails
    """
    try:
        creds = get_credentials()
        if not creds:
            raise Exception("No valid credentials found. Please authenticate first.")

        service = build('chat', 'v1', credentials=creds)

        # Make API request
        response = service.spaces().messages().delete(name=message_name).execute()

        return response

    except Exception as e:
        raise Exception(f"Failed to delete message: {str(e)}")


async def add_emoji_reaction(message_name: str, emoji: str) -> Dict:
    """Add an emoji reaction to a message.

    Args:
        message_name: The resource name of the message (spaces/*/messages/*)
        emoji: The emoji to add as a reaction (e.g. '👍', '❤️', etc.)

    Returns:
        Response with information about the added reaction

    Raises:
        Exception: If authentication fails or reaction fails
    """
    try:
        creds = get_credentials()
        if not creds:
            raise Exception("No valid credentials found. Please authenticate first.")

        service = build('chat', 'v1', credentials=creds)

        if not message_name.startswith('spaces/'):
            raise ValueError("message_name must be a full resource name (spaces/*/messages/*)")

        # Add reaction
        reaction_body = {
            "emoji": {
                "unicode": emoji
            }
        }

        response = service.spaces().messages().reactions().create(
            parent=message_name,
            body=reaction_body
        ).execute()

        return response

    except Exception as e:
        raise Exception(f"Failed to add emoji reaction: {str(e)}")


async def get_message_with_sender_info(message_name: str) -> Dict:
    """Gets a specific message by its resource name and adds sender information.

    Args:
        message_name: The resource name of the message (spaces/*/messages/*)

    Returns:
        The message object with additional sender information

    Raises:
        Exception: If authentication fails or message retrieval fails
    """
    return await get_message(message_name, include_sender_info=True)


async def list_messages_with_sender_info(space_name: str,
                                         limit: int = 10,
                                         page_token: Optional[str] = None,
                                         days_window: int = 3,
                                         offset: int = 0) -> Dict:
    """Lists messages from a specific Google Chat space with sender information.

    Args:
        space_name: The name/identifier of the space to fetch messages from
        limit: Maximum number of messages to return (default: 10)
        page_token: Optional page token for pagination
        days_window: Number of days to look back for messages (default: 3)
                    This parameter controls the date range for message retrieval.
                    For example, if days_window=3, messages from the last 3 days will be retrieved.
        offset: Number of days to offset the end date from today (default: 0). 
               For example, if offset=3, the end date will be 3 days before today,
               and with days_window=3, messages from 6 to 3 days ago will be retrieved.

    Returns:
        Dictionary with 'messages' list (with sender info) and optional 'nextPageToken'

    Raises:
        Exception: If authentication fails or message retrieval fails
    """
    result = await list_space_messages(
        space_name,
        include_sender_info=True,
        page_size=limit,
        page_token=page_token,
        order_by="createTime desc",  # Default to newest first
        days_window=days_window,
        offset=offset
    )
    return result
