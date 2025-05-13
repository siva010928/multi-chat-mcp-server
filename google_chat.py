import os
import json
import datetime
from typing import List, Dict, Optional, Tuple
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from pathlib import Path
from googleapiclient.http import MediaFileUpload
import mimetypes

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/chat.spaces.readonly',
    'https://www.googleapis.com/auth/chat.messages',
    'https://www.googleapis.com/auth/chat.messages.create',
    'https://www.googleapis.com/auth/chat.spaces',
    'https://www.googleapis.com/auth/userinfo.profile',  # For user profile info
    'https://www.googleapis.com/auth/userinfo.email',    # For user email
    'openid'                                            # OpenID Connect
]
DEFAULT_CALLBACK_URL = "http://localhost:8000/auth/callback"
DEFAULT_TOKEN_PATH = 'token.json'

# Store credentials info
token_info = {
    'credentials': None,
    'last_refresh': None,
    'token_path': DEFAULT_TOKEN_PATH
}

def set_token_path(path: str) -> None:
    """Set the global token path for OAuth storage.
    
    Args:
        path: Path where the token should be stored
    """
    token_info['token_path'] = path

def save_credentials(creds: Credentials, token_path: Optional[str] = None) -> None:
    """Save credentials to file and update in-memory cache.
    
    Args:
        creds: The credentials to save
        token_path: Path to save the token file
    """
    # Use configured token path if none provided
    if token_path is None:
        token_path = token_info['token_path']
    
    # Save to file
    token_path = Path(token_path)
    with open(token_path, 'w') as token:
        token.write(creds.to_json())
    
    # Update in-memory cache
    token_info['credentials'] = creds
    token_info['last_refresh'] = datetime.datetime.utcnow()

def get_credentials(token_path: Optional[str] = None) -> Optional[Credentials]:
    """Gets valid user credentials from storage or memory.
    
    Args:
        token_path: Optional path to token file. If None, uses the configured path.
    
    Returns:
        Credentials object or None if no valid credentials exist
    """
    if token_path is None:
        token_path = token_info['token_path']
    
    creds = token_info['credentials']
    
    # If no credentials in memory, try to load from file
    if not creds:
        token_path = Path(token_path)
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
            token_info['credentials'] = creds
    
    # If we have credentials that need refresh
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            save_credentials(creds, token_path)
        except Exception:
            return None
    
    return creds if (creds and creds.valid) else None

async def refresh_token(token_path: Optional[str] = None) -> Tuple[bool, str]:
    """Attempt to refresh the current token.
    
    Args:
        token_path: Path to the token file. If None, uses the configured path.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    if token_path is None:
        token_path = token_info['token_path']
        
    try:
        creds = token_info['credentials']
        if not creds:
            token_path = Path(token_path)
            if not token_path.exists():
                return False, "No token file found"
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        
        if not creds.refresh_token:
            return False, "No refresh token available"
        
        creds.refresh(Request())
        save_credentials(creds, token_path)
        return True, "Token refreshed successfully"
    except Exception as e:
        return False, f"Failed to refresh token: {str(e)}"

# MCP functions
async def list_chat_spaces() -> List[Dict]:
    """Lists all Google Chat spaces the bot has access to."""
    try:
        creds = get_credentials()
        if not creds:
            raise Exception("No valid credentials found. Please authenticate first.")
            
        service = build('chat', 'v1', credentials=creds)
        spaces = service.spaces().list(pageSize=30).execute()
        return spaces.get('spaces', [])
    except Exception as e:
        raise Exception(f"Failed to list chat spaces: {str(e)}") 

async def list_space_messages(space_name: str, 
                            start_date: Optional[datetime.datetime] = None,
                            end_date: Optional[datetime.datetime] = None,
                            include_sender_info: bool = False,
                            page_size: int = 25,
                            page_token: Optional[str] = None,
                            filter_str: Optional[str] = None,
                            order_by: Optional[str] = None,
                            show_deleted: bool = False) -> Dict:
    """Lists messages from a specific Google Chat space with optional time filtering.
    
    Args:
        space_name: The name/identifier of the space to fetch messages from
        start_date: Optional start datetime for filtering messages. If provided without end_date,
                   will query messages for the entire day of start_date
        end_date: Optional end datetime for filtering messages. Only used if start_date is also provided
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
            if end_date:
                # Format for date range query
                filter_str = f"createTime > \"{start_date.isoformat()}\" AND createTime < \"{end_date.isoformat()}\""
            else:
                # For single day query, set range from start of day to end of day
                day_start = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day_start + datetime.timedelta(days=1)
                filter_str = f"createTime > \"{day_start.isoformat()}\" AND createTime < \"{day_end.isoformat()}\""
        
        # Prepare request parameters
        request_params = {
            'parent': space_name,
            'pageSize': min(page_size, 1000)  # Enforce API limit of 1000
        }
        
        # Add optional parameters if provided
        if filter_str:
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

async def get_current_user_info() -> Dict:
    """Gets information about the currently authenticated user.
    
    Returns:
        Dictionary containing user details
        
    Raises:
        Exception: If authentication fails or user info retrieval fails
    """
    try:
        creds = get_credentials()
        if not creds:
            raise Exception("No valid credentials found. Please authenticate first.")
            
        # Use the People API to get user information
        people_service = build('people', 'v1', credentials=creds)
        
        # Get profile data for the authenticated user
        profile = people_service.people().get(
            resourceName='people/me',
            personFields='names,emailAddresses'
        ).execute()
        
        # Extract the user's display name and email
        names = profile.get('names', [])
        emails = profile.get('emailAddresses', [])
        
        user_info = {
            "email": emails[0].get("value") if emails else None,
            "display_name": names[0].get("displayName") if names else None,
            "given_name": names[0].get("givenName") if names else None,
            "family_name": names[0].get("familyName") if names else None
        }
        
        return user_info
        
    except Exception as e:
        raise Exception(f"Failed to get user info: {str(e)}")

async def get_user_mentions(days: int = 7, space_id: Optional[str] = None, include_sender_info: bool = True,
                      page_size: int = 50, page_token: Optional[str] = None) -> Dict:
    """Gets messages that mention the authenticated user from all spaces or a specific space.
    
    Args:
        days: Number of days to look back for mentions (default: 7)
        space_id: Optional space ID to check for mentions in a specific space
        include_sender_info: Whether to include sender information in the returned messages (default: True)
        page_size: Maximum number of messages to return per space (default: 50)
        page_token: Optional page token for pagination (only applicable when space_id is provided)
        
    Returns:
        Dictionary with 'messages' list of messages where the user was mentioned and optional 'nextPageToken'
        
    Raises:
        Exception: If authentication fails or API request fails
    """
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
            # If we can't get the user info, we'll look for the email in the text
            username = creds.id_token.get('email', '')
        
        if not username:
            raise Exception("Could not determine username for mentions")
        
        # Calculate date range (now - days)
        end_date = datetime.datetime.now(datetime.timezone.utc)
        start_date = end_date - datetime.timedelta(days=days)
        date_filter = f"createTime > \"{start_date.isoformat()}\""
            
        # If space_id is provided, we can use pagination and just get messages from one space
        if space_id:
            if not space_id.startswith('spaces/'):
                space_id = f"spaces/{space_id}"
                
            # Get messages from the specific space
            messages_result = await list_space_messages(
                space_id, 
                include_sender_info=include_sender_info,
                page_size=page_size,
                page_token=page_token,
                filter_str=date_filter
            )
            messages = messages_result.get('messages', [])
            next_page_token = messages_result.get('nextPageToken')
            
            # Filter messages that mention the user by username
            mention_messages = []
            for msg in messages:
                text = msg.get("text", "")
                # Check if the username is in the text (could be in the form @username or just username)
                if username.lower() in text.lower() or f"@{username.lower()}" in text.lower():
                    # Add the space information to the message
                    msg["space_info"] = {
                        "name": space_id
                    }
                    # Try to get the space display name
                    try:
                        space_details = service.spaces().get(name=space_id).execute()
                        msg["space_info"]["displayName"] = space_details.get("displayName", "Unknown Space")
                    except:
                        msg["space_info"]["displayName"] = "Unknown Space"
                    
                    mention_messages.append(msg)
            
            return {
                'messages': mention_messages,
                'nextPageToken': next_page_token
            }
            
        # If no space_id is provided, we need to search across all spaces
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
                    # Get messages from this space
                    messages_result = await list_space_messages(
                        space_name,
                        include_sender_info=include_sender_info,
                        page_size=page_size,
                        filter_str=date_filter
                    )
                    messages = messages_result.get('messages', [])
                    
                    # Filter messages that mention the user by username
                    for msg in messages:
                        text = msg.get("text", "")
                        # Check if the username is in the text (could be in the form @username or just username)
                        if username.lower() in text.lower() or f"@{username.lower()}" in text.lower():
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
                                
                            all_mentions.append(msg)
                except Exception:
                    # If we fail to get messages from one space, continue with others
                    continue
            
            return {
                'messages': all_mentions,
                'nextPageToken': None  # No pagination when searching across all spaces
            }
                
    except Exception as e:
        raise Exception(f"Failed to get user mentions: {str(e)}")

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

async def create_interactive_card_message(space_name: str, 
                                        card_title: str, 
                                        card_subtitle: str = None,
                                        card_image_url: str = None,
                                        sections: List[Dict] = None,
                                        buttons: List[Dict] = None) -> Dict:
    """Creates a message with an interactive card in a Google Chat space.
    
    Args:
        space_name: The name/identifier of the space to send the message to
        card_title: Title for the card
        card_subtitle: Optional subtitle for the card
        card_image_url: Optional image URL to display in the card header
        sections: Optional list of sections for the card, each section is a dict with:
            - header: Optional header text for the section
            - widgets: List of widgets in the section
        buttons: Optional list of buttons to add to the card, each button is a dict with:
            - text: Button text
            - onClick: Action to perform when clicked (e.g. openLink or action)
        
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
        
        # Build card header
        card_header = {"title": card_title}
        if card_subtitle:
            card_header["subtitle"] = card_subtitle
        if card_image_url:
            card_header["imageUrl"] = card_image_url
            card_header["imageType"] = "SQUARE"  # Default to SQUARE, can be CIRCLE or RECTANGLE
        
        # Build card sections
        card_sections = []
        
        if sections:
            card_sections.extend(sections)
        
        # Add buttons as a separate section with buttonList widget if provided
        if buttons:
            button_section = {
                "widgets": [{
                    "buttonList": {
                        "buttons": buttons
                    }
                }]
            }
            card_sections.append(button_section)
        
        # Build the complete card
        card = {
            "card": {
                "header": card_header,
                "sections": card_sections
            }
        }
        
        # Build message body (no text, just the card)
        message_body = {"cardsV2": [card]}
        
        # Make API request
        response = service.spaces().messages().create(
            parent=space_name,
            body=message_body
        ).execute()
        
        return response
        
    except Exception as e:
        raise Exception(f"Failed to create interactive card message: {str(e)}")
    
# Enhanced Google Chat Operations

async def search_messages(query: str, spaces: List[str] = None, max_results: int = 50, 
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

async def manage_space_members(space_name: str, operation: str, user_emails: List[str]) -> Dict:
    """Manage space membership - add or remove members.
    
    Args:
        space_name: The name/identifier of the space
        operation: Either 'add' or 'remove'
        user_emails: List of user email addresses to add or remove
        
    Returns:
        Response with information about the operation
        
    Raises:
        Exception: If authentication fails or operation fails
    """
    try:
        creds = get_credentials()
        if not creds:
            raise Exception("No valid credentials found. Please authenticate first.")
            
        service = build('chat', 'v1', credentials=creds)
        
        if not space_name.startswith('spaces/'):
            space_name = f"spaces/{space_name}"
            
        if operation.lower() not in ['add', 'remove']:
            raise ValueError("Operation must be either 'add' or 'remove'")
        
        results = {
            "operation": operation,
            "space": space_name,
            "successful": [],
            "failed": []
        }
        
        for email in user_emails:
            try:
                if operation.lower() == 'add':
                    # Add member to space
                    member_body = {
                        "member": {
                            "name": f"users/{email}",
                            "type": "HUMAN"
                        }
                    }
                    service.spaces().members().create(
                        parent=space_name,
                        body=member_body
                    ).execute()
                    results["successful"].append(email)
                else:
                    # Remove member from space
                    member_name = f"{space_name}/members/users/{email}"
                    service.spaces().members().delete(name=member_name).execute()
                    results["successful"].append(email)
            except Exception as e:
                results["failed"].append({
                    "email": email,
                    "error": str(e)
                })
                
        return results
        
    except Exception as e:
        raise Exception(f"Failed to manage space members: {str(e)}")
        
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

async def upload_attachment(space_name: str, file_path: str, message_text: str = None) -> Dict:
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
    
async def send_file_message(space_name: str, file_path: str, message_text: str = None) -> Dict:
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

async def get_user_info_by_id(user_id: str) -> Dict:
    """Gets information about a specific user by their user ID.
    
    Args:
        user_id: The ID of the user to get information for (e.g., 'users/1234567890')
        
    Returns:
        Dictionary containing user details if available
        
    Raises:
        Exception: If authentication fails or user info retrieval fails
    """
    try:
        creds = get_credentials()
        if not creds:
            raise Exception("No valid credentials found. Please authenticate first.")
            
        # Use the People API to get user information
        people_service = build('people', 'v1', credentials=creds)
        
        # Extract user resource name from user_id if needed
        if not user_id.startswith('people/'):
            # Convert from Chat API format (users/123) to People API format (people/123)
            if user_id.startswith('users/'):
                user_resource = f"people/{user_id.split('/')[1]}"
            else:
                user_resource = f"people/{user_id}"
        else:
            user_resource = user_id
            
        try:
            # Try to get profile data for the user
            profile = people_service.people().get(
                resourceName=user_resource,
                personFields='names,emailAddresses,photos'
            ).execute()
            
            # Extract user information
            names = profile.get('names', [])
            emails = profile.get('emailAddresses', [])
            photos = profile.get('photos', [])
            
            user_info = {
                "id": user_id,
                "email": emails[0].get("value") if emails else None,
                "display_name": names[0].get("displayName") if names else None,
                "given_name": names[0].get("givenName") if names else None,
                "family_name": names[0].get("familyName") if names else None,
                "profile_photo": photos[0].get("url") if photos else None
            }
            
            return user_info
        except Exception as e:
            # If we can't get detailed info, return basic info
            return {
                "id": user_id,
                "display_name": f"User {user_id.split('/')[-1]}",
                "error": str(e)
            }
        
    except Exception as e:
        raise Exception(f"Failed to get user info: {str(e)}")

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
                                        start_date: Optional[datetime.datetime] = None,
                                        end_date: Optional[datetime.datetime] = None,
                                        limit: int = 10,
                                        page_token: Optional[str] = None) -> Dict:
    """Lists messages from a specific Google Chat space with sender information.
    
    Args:
        space_name: The name/identifier of the space to fetch messages from
        start_date: Optional start datetime for filtering messages
        end_date: Optional end datetime for filtering messages
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

async def get_conversation_participants(space_name: str, 
                                  start_date: Optional[datetime.datetime] = None,
                                  end_date: Optional[datetime.datetime] = None,
                                  page_size: int = 100) -> List[Dict]:
    """Gets information about participants in a conversation or space.
    
    Args:
        space_name: The name/identifier of the space
        start_date: Optional start datetime for filtering messages
        end_date: Optional end datetime for filtering messages
        page_size: Maximum number of messages to check for participants (default: 100)
        
    Returns:
        List of unique participants with their information
        
    Raises:
        Exception: If authentication fails or API request fails
    """
    try:
        # Get messages with sender info
        result = await list_space_messages(
            space_name, 
            start_date, 
            end_date, 
            include_sender_info=True,
            page_size=page_size
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
                              start_date: Optional[datetime.datetime] = None,
                              end_date: Optional[datetime.datetime] = None,
                              page_token: Optional[str] = None,
                              filter_str: Optional[str] = None) -> Dict:
    """Generates a summary of a conversation in a space.
    
    Args:
        space_name: The name/identifier of the space
        message_limit: Maximum number of messages to include in summary
        start_date: Optional start datetime for filtering messages
        end_date: Optional end datetime for filtering messages
        page_token: Optional page token for pagination
        filter_str: Optional filter string in the format specified by Google Chat API
        
    Returns:
        Dictionary containing space information, participants, and recent messages
        
    Raises:
        Exception: If authentication fails or API request fails
    """
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
            start_date, 
            end_date, 
            include_sender_info=True,
            page_size=message_limit,
            page_token=page_token,
            filter_str=filter_str
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
    
