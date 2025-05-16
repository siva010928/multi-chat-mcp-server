from typing import List, Dict, Optional

from googleapiclient.discovery import build

from src.google_chat.auth import get_credentials, get_user_info_by_id
from src.google_chat.spaces import list_chat_spaces


async def list_space_messages(space_name: str,
                              start_date: Optional[str] = None,
                              end_date: Optional[str] = None,
                              include_sender_info: bool = False,
                              page_size: int = 25,
                              page_token: Optional[str] = None,
                              filter_str: Optional[str] = None,
                              order_by: Optional[str] = None,
                              show_deleted: bool = False) -> Dict:
    """Lists messages from a specific Google Chat space with optional time filtering.

    Args:
        space_name: The name/identifier of the space to fetch messages from
        start_date: Optional start date in YYYY-MM-DD format for filtering messages. 
                   If provided without end_date, will query messages for the entire day of start_date
        end_date: Optional end date in YYYY-MM-DD format for filtering messages.
                 Only used if start_date is also provided
        include_sender_info: Whether to include sender information in the returned messages (default: False)
        page_size: Maximum number of messages to return (default: 25, max: 1000)
        page_token: Page token from a previous request for pagination
        filter_str: Optional filter string in the format specified by Google Chat API
                   For example: "createTime > \"2023-04-21T11:30:00-04:00\""
        order_by: How messages are ordered, format: "<field> <direction>",
                 e.g., "createTime DESC" (default: "createTime ASC")
        show_deleted: Whether to include deleted messages (default: False)

    Returns:
        Dictionary with 'messages' list and optional 'nextPageToken'

    Raises:
        Exception: If authentication fails or API request fails
    """
    try:
        creds = get_credentials()
        if not creds:
            raise Exception("No valid credentials found. Please authenticate first.")

        service = build('chat', 'v1', credentials=creds)

        # If filter not provided but start_date is, construct a filter string
        if not filter_str and start_date:
            import logging
            import datetime
            logger = logging.getLogger("messages")
            logger.info(f"Creating date filter from start_date={start_date}, end_date={end_date}")
            
            # Parse start_date
            start_datetime = datetime.datetime.strptime(start_date, '%Y-%m-%d').replace(
                hour=0, minute=0, second=0, microsecond=0, tzinfo=datetime.timezone.utc
            )
            logger.debug(f"Parsed start_datetime: {start_datetime}")
            
            if end_date:
                # Parse end_date
                end_datetime = datetime.datetime.strptime(end_date, '%Y-%m-%d').replace(
                    hour=23, minute=59, second=59, microsecond=999999, tzinfo=datetime.timezone.utc
                )
                logger.debug(f"Parsed end_datetime: {end_datetime}")
                
                # Format with proper fractional seconds
                start_time_str = start_datetime.strftime("%Y-%m-%dT%H:%M:%S.%f").rstrip('0').rstrip('.') + 'Z'
                end_time_str = end_datetime.strftime("%Y-%m-%dT%H:%M:%S.%f").rstrip('0').rstrip('.') + 'Z'
                logger.debug(f"Formatted time strings: start={start_time_str}, end={end_time_str}")
                
                # Format for date range query
                filter_str = f'createTime > "{start_time_str}" AND createTime < "{end_time_str}"'
            else:
                # For single day query, set range from start of day to end of day
                end_datetime = start_datetime.replace(hour=23, minute=59, second=59, microsecond=999999)
                logger.debug(f"End of day datetime: {end_datetime}")
                
                # Format with proper fractional seconds
                start_time_str = start_datetime.strftime("%Y-%m-%dT%H:%M:%S.%f").rstrip('0').rstrip('.') + 'Z'
                end_time_str = end_datetime.strftime("%Y-%m-%dT%H:%M:%S.%f").rstrip('0').rstrip('.') + 'Z'
                logger.debug(f"Formatted time strings: start={start_time_str}, end={end_time_str}")
                
                filter_str = f'createTime > "{start_time_str}" AND createTime < "{end_time_str}"'
            
            logger.info(f"Date filter created: {filter_str}")

        # Prepare request parameters
        request_params = {
            'parent': space_name,
            'pageSize': min(page_size, 1000)  # Enforce API limit of 1000
        }

        # Add optional parameters if provided
        if filter_str:
            import logging
            logger = logging.getLogger("messages")
            logger.debug(f"Using filter string: {filter_str}")
            request_params['filter'] = filter_str
        if page_token:
            request_params['pageToken'] = page_token
        if order_by:
            request_params['orderBy'] = order_by
        if show_deleted:
            request_params['showDeleted'] = show_deleted

        # Make API request
        response = service.spaces().messages().list(**request_params).execute()

        # Extract messages and next page token
        messages = response.get('messages', [])
        next_page_token = response.get('nextPageToken')

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


async def exact_search_messages(query: str, spaces: List[str] = None, max_results: int = 50,
                                include_sender_info: bool = False, page_token: Optional[str] = None,
                                filter_str: Optional[str] = None, order_by: Optional[str] = None) -> Dict:
    """Search for messages across all spaces or specified spaces.

    Args:
        query: The search query string
        spaces: Optional list of space names to search in. If None, searches all spaces.
        max_results: Maximum number of results to return per space (default: 50)
        include_sender_info: Whether to include sender information in the returned messages (default: False)
        page_token: Optional page token for pagination (only applicable when searching a single space)
        filter_str: Optional filter string in the format specified by Google Chat API
        order_by: How messages are ordered, format: "<field> <direction>"

    Returns:
        Dictionary with 'messages' list of matching messages and optional 'nextPageToken'

    Raises:
        Exception: If authentication fails or search fails
    """
    try:
        creds = get_credentials()
        if not creds:
            raise Exception("No valid credentials found. Please authenticate first.")

        service = build('chat', 'v1', credentials=creds)

        # Get spaces to search
        spaces_to_search = spaces
        if not spaces_to_search:
            # Get all spaces if none specified
            spaces_response = await list_chat_spaces()
            spaces_to_search = [space.get("name") for space in spaces_response if space.get("name")]

        # If only searching one space and we have a page token, we can do direct pagination
        if len(spaces_to_search) == 1 and page_token:
            space_name = spaces_to_search[0]

            # Get messages from the space with pagination
            result = await list_space_messages(
                space_name,
                include_sender_info=include_sender_info,
                page_size=max_results,
                page_token=page_token,
                filter_str=filter_str,
                order_by=order_by
            )
            messages = result.get('messages', [])
            next_page_token = result.get('nextPageToken')

            # Filter messages by query - using regex for more robust matching
            import re
            try:
                # Try to compile as regex first
                pattern = re.compile(query, re.IGNORECASE)
                matched_messages = []
                for msg in messages:
                    text = msg.get("text", "")
                    if text and pattern.search(text):
                        # Add space information to the message
                        msg["space_info"] = {"name": space_name}
                        matched_messages.append(msg)
            except re.error:
                # Fallback to substring search if regex fails
                matched_messages = []
                query_lower = query.lower()
                for msg in messages:
                    text = msg.get("text", "").lower()
                    if query_lower in text:
                        # Add space information to the message
                        msg["space_info"] = {"name": space_name}
                        matched_messages.append(msg)

            return {
                'messages': matched_messages,
                'nextPageToken': next_page_token
            }

        # Otherwise, search across all specified spaces
        all_results = []

        # Search in each space
        for space_name in spaces_to_search:
            try:
                # Get messages from this space
                result = await list_space_messages(
                    space_name,
                    include_sender_info=include_sender_info,
                    page_size=max_results,
                    filter_str=filter_str,
                    order_by=order_by
                )
                messages = result.get('messages', [])

                # Filter messages by query - using regex for more robust matching
                import re
                try:
                    # Try to compile as regex first
                    pattern = re.compile(query, re.IGNORECASE)
                    for msg in messages:
                        text = msg.get("text", "")
                        if text and pattern.search(text):
                            # Add space information to the message
                            msg["space_info"] = {"name": space_name}
                            all_results.append(msg)

                            if len(all_results) >= max_results:
                                return {
                                    'messages': all_results[:max_results],
                                    'nextPageToken': None  # No pagination when limited by max_results
                                }
                except re.error:
                    # Fallback to substring search if regex fails
                    query_lower = query.lower()
                    for msg in messages:
                        text = msg.get("text", "").lower()
                        if query_lower in text:
                            # Add space information to the message
                            msg["space_info"] = {"name": space_name}
                            all_results.append(msg)

                            if len(all_results) >= max_results:
                                return {
                                    'messages': all_results[:max_results],
                                    'nextPageToken': None  # No pagination when limited by max_results
                                }
            except Exception as e:
                # If we fail to search one space, continue with others
                continue

        return {
            'messages': all_results,
            'nextPageToken': None  # No pagination when searching across multiple spaces
        }

    except Exception as e:
        raise Exception(f"Failed to search messages: {str(e)}")


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
                                         start_date: Optional[str] = None,
                                         end_date: Optional[str] = None,
                                         limit: int = 10,
                                         page_token: Optional[str] = None) -> Dict:
    """Lists messages from a specific Google Chat space with sender information.

    Args:
        space_name: The name/identifier of the space to fetch messages from
        start_date: Optional start date in YYYY-MM-DD format
        end_date: Optional end date in YYYY-MM-DD format
        limit: Maximum number of messages to return (default: 10)
        page_token: Optional page token for pagination

    Returns:
        Dictionary with 'messages' list (with sender info) and optional 'nextPageToken'

    Raises:
        Exception: If authentication fails or message retrieval fails
    """
    result = await list_space_messages(
        space_name,
        start_date,
        end_date,
        include_sender_info=True,
        page_size=limit,
        page_token=page_token
    )
    return result
