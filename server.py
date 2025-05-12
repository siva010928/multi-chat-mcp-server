# server.py
import httpx
import sys
import argparse
from typing import List, Dict

from fastmcp import FastMCP
from google_chat import list_chat_spaces, DEFAULT_CALLBACK_URL, set_token_path
from server_auth import run_auth_server

# Create an MCP server
mcp = FastMCP("Demo")

@mcp.tool()
async def get_chat_spaces() -> List[Dict]:
    """List all Google Chat spaces the bot has access to.
    
    Uses the Google Chat API spaces.list method to retrieve all available spaces
    (e.g., rooms, direct messages) that the authenticated user has access to. A space
    is a container for messages and may represent a persistent conversation or a one-off
    meeting. Each space has a unique identifier (name) that follows the pattern 'spaces/{id}'.
    
    This tool requires OAuth authentication. On first run, it will open a browser window
    for you to log in with your Google account. Make sure you have credentials.json
    downloaded from Google Cloud Console in the current directory.
    
    Returns:
        A list of dictionaries, each representing a space with the following properties:
        - name: The resource name of the space (string, format: "spaces/{space_id}")
        - type: The type of space (string, e.g., "ROOM", "DM", "GROUP_DM")
        - displayName: The display name of the space (string)
        - Other optional properties that may be included
    
    API Reference:
        https://developers.google.com/chat/api/reference/rest/v1/spaces/list
    """
    return await list_chat_spaces()

@mcp.tool()
async def get_space_messages(space_name: str, 
                           start_date: str,
                           end_date: str = None,
                           include_sender_info: bool = False,
                           page_size: int = 25,
                           page_token: str = None,
                           filter_str: str = None,
                           order_by: str = None,
                           show_deleted: bool = False) -> Dict:
    """List messages from a specific Google Chat space with optional time filtering.
    
    Uses the Google Chat API spaces.messages.list method to retrieve messages from a specific space.
    Messages can be filtered by time range, sorted, and paginated. This function allows you to
    view historical messages in a conversation, find specific content, or analyze communication patterns.
    
    This tool requires OAuth authentication. The space_name should be in the format
    'spaces/your_space_id'. Dates should be in YYYY-MM-DD format (e.g., '2024-03-22').
    
    When only start_date is provided, it will query messages for that entire day.
    When both dates are provided, it will query messages from start_date 00:00:00Z
    to end_date 23:59:59Z.
    
    Args:
        space_name: The resource name of the space to fetch messages from 
                   (string, format: "spaces/{space_id}")
        start_date: Required start date in YYYY-MM-DD format (e.g., "2024-05-01")
        end_date: Optional end date in YYYY-MM-DD format (e.g., "2024-05-05")
        include_sender_info: Whether to include detailed sender information in the returned messages.
                            When true, each message will include a sender_info object with details
                            like email, display_name, and profile_photo. (default: False)
        page_size: Maximum number of messages to return in a single request. 
                  Ranges from 1 to 1000. (default: 25, max: 1000)
        page_token: Page token from a previous request for pagination. Use the nextPageToken 
                   from a previous response to get the next page of results.
        filter_str: Optional filter string in the format specified by Google Chat API.
                   For example: 'createTime > "2023-04-21T11:30:00-04:00"'
                   See API reference for full filter syntax options.
        order_by: How messages are ordered, format: "<field> <direction>", 
                 e.g., "createTime DESC" (default: "createTime ASC")
        show_deleted: Whether to include deleted messages in the results (default: False)
    
    Returns:
        Dictionary containing:
        - messages: List of message objects, each with properties like:
          - name: Resource name of the message (string, format: "spaces/{space_id}/messages/{message_id}")
          - text: Content of the message (string)
          - sender: Information about who sent the message
          - createTime: When the message was created (timestamp)
          - sender_info: Additional sender details if include_sender_info=True
          - Other message properties like attachments, annotations, etc.
        - nextPageToken: Token for retrieving the next page of results, or null if no more results
    
    Raises:
        ValueError: If the date format is invalid or dates are in wrong order
    
    API Reference:
        https://developers.google.com/chat/api/reference/rest/v1/spaces.messages/list
    """
    from google_chat import list_space_messages
    from datetime import datetime, timezone

    try:
        # Parse start date and set to beginning of day (00:00:00Z)
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d').replace(
            hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
        )
        
        # Parse end date if provided and set to end of day (23:59:59Z)
        end_datetime = None
        if end_date:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d').replace(
                hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc
            )
            
            # Validate date range
            if start_datetime > end_datetime:
                raise ValueError("start_date must be before end_date")
    except ValueError as e:
        if "strptime" in str(e):
            raise ValueError("Dates must be in YYYY-MM-DD format (e.g., '2024-03-22')")
        raise e
    
    # Call the updated list_space_messages function
    return await list_space_messages(
        space_name, 
        start_datetime, 
        end_datetime, 
        include_sender_info=include_sender_info,
        page_size=page_size, 
        page_token=page_token,
        filter_str=filter_str,
        order_by=order_by,
        show_deleted=show_deleted
    )

@mcp.tool()
async def send_message(space_name: str, text: str) -> Dict:
    """Send a text message to a Google Chat space.
    
    Uses the Google Chat API spaces.messages.create method to send a new text message
    to a specified space. This is the most basic form of message sending, allowing
    you to post simple text communications to a space.
    
    This tool requires OAuth authentication. It will send a text-only message 
    to the specified space.
    
    Args:
        space_name: The resource name of the space to send the message to.
                   Can be either a full resource name (e.g., 'spaces/AAQAtjsc9v4')
                   or just the ID portion ('AAQAtjsc9v4'). If only the ID is provided,
                   it will be automatically prefixed with 'spaces/'.
        text: Text content of the message. Can include plain text or limited markdown formatting,
              including bold, italic, strikethrough, and inline code. Supports up to 4,096 characters.
              Emojis (Unicode) are also supported.
    
    Returns:
        The created message object with properties such as:
        - name: Resource name of the created message (string)
        - text: The text content of the message (string)
        - sender: Information about who sent the message (object)
        - createTime: When the message was created (timestamp)
        - thread: Thread information if the message is part of a thread (object)
        - Other properties as applicable
        
    API Reference:
        https://developers.google.com/chat/api/reference/rest/v1/spaces.messages/create
    """
    from google_chat import create_message
    
    if not space_name.startswith('spaces/'):
        space_name = f"spaces/{space_name}"
        
    return await create_message(space_name, text)

# @mcp.tool()
# async def send_card_message(space_name: str, text: str, card_title: str, card_description: str = None) -> Dict:
#     """Send a message with a card to a Google Chat space.
    
#     This tool requires OAuth authentication. It will send a message with both 
#     text and a simple card with a title and optional description.
    
#     Args:
#         space_name: The name/identifier of the space to send the message to (e.g., 'spaces/AAQAtjsc9v4')
#         text: Text content of the message
#         card_title: Title for the card
#         card_description: Optional description for the card
    
#     Returns:
#         The created message object with message ID and other details
#     """
#     from google_chat import create_message
    
#     if not space_name.startswith('spaces/'):
#         space_name = f"spaces/{space_name}"
    
#     # Create a simple card
#     card = {
#         "card": {
#             "header": {
#                 "title": card_title
#             }
#         }
#     }
    
#     # Add description if provided
#     if card_description:
#         card["card"]["sections"] = [{
#             "widgets": [{
#                 "textParagraph": {
#                     "text": card_description
#                 }
#             }]
#         }]
    
#     return await create_message(space_name, text, [card])

# @mcp.tool()
# async def send_interactive_card(
#     space_name: str,
#     card_title: str,
#     card_subtitle: str = None,
#     card_image_url: str = None,
#     button_text: str = None,
#     button_url: str = None,
#     button_action_function: str = None,
#     section_header: str = None,
#     section_content: str = None
# ) -> Dict:
#     """Send an interactive card message to a Google Chat space.
    
#     This tool requires OAuth authentication. It creates a card with optional
#     interactive elements like buttons and sections with formatted text.
    
#     Args:
#         space_name: The name/identifier of the space to send the message to (e.g., 'spaces/AAQAtjsc9v4')
#         card_title: Title for the card
#         card_subtitle: Optional subtitle for the card
#         card_image_url: Optional image URL to display in the card header
#         button_text: Optional text for a button
#         button_url: Optional URL for the button to open when clicked
#         button_action_function: Optional function name to call when button is clicked
#         section_header: Optional header for a text section
#         section_content: Optional text content for a section
    
#     Returns:
#         The created message object with message ID and other details
#     """
#     from google_chat import create_interactive_card_message
    
#     if not space_name.startswith('spaces/'):
#         space_name = f"spaces/{space_name}"
    
#     # Build sections if content provided
#     sections = []
#     if section_header or section_content:
#         section = {}
#         if section_header:
#             section["header"] = section_header
        
#         widgets = []
#         if section_content:
#             widgets.append({
#                 "textParagraph": {
#                     "text": section_content
#                 }
#             })
        
#         if widgets:
#             section["widgets"] = widgets
#             sections.append(section)
    
#     # Build button if provided
#     buttons = []
#     if button_text:
#         button = {
#             "text": button_text
#         }
        
#         # Add either URL or action function
#         if button_url:
#             button["onClick"] = {
#                 "openLink": {
#                     "url": button_url
#                 }
#             }
#         elif button_action_function:
#             button["onClick"] = {
#                 "action": {
#                     "function": button_action_function
#                 }
#             }
        
#         buttons.append(button)
    
#     return await create_interactive_card_message(
#         space_name, 
#         card_title,
#         card_subtitle,
#         card_image_url,
#         sections,
#         buttons
#     )

@mcp.tool()
async def update_chat_message(message_name: str, new_text: str = None) -> Dict:
    """Update an existing message in a Google Chat space.
    
    This tool requires OAuth authentication. It can update the text content of an existing message.
    
    Args:
        message_name: The full resource name of the message to update (spaces/*/messages/*)
        new_text: New text content for the message
    
    Returns:
        The updated message object
    """
    from google_chat import update_message
    
    if not message_name.startswith('spaces/'):
        raise ValueError("message_name must be a full resource name (spaces/*/messages/*)")
        
    return await update_message(message_name, new_text)

@mcp.tool()
async def reply_to_message_thread(space_name: str, thread_key: str, text: str) -> Dict:
    """Reply to a message thread in a Google Chat space.
    
    Uses the Google Chat API spaces.messages.create method with thread information to send a reply
    to an existing thread in a space. In Google Chat, threads group related messages together,
    making conversations easier to follow.
    
    This tool requires OAuth authentication. It will send a text message as a reply 
    to an existing thread in the specified space.
    
    Args:
        space_name: The resource name of the space containing the thread.
                   Can be either a full resource name (e.g., 'spaces/AAQAtjsc9v4')
                   or just the ID portion ('AAQAtjsc9v4'). If only the ID is provided,
                   it will be automatically prefixed with 'spaces/'.
        thread_key: The identifier for the thread to reply to. This can be:
                   - A thread key (e.g., 'thread123')
                   - A thread name (e.g., 'spaces/AAQAtjsc9v4/threads/thread123')
                   - A message ID (the system will attempt to find its thread)
        text: Text content of the reply. Can include plain text or limited markdown formatting,
              including bold, italic, strikethrough, and inline code. Supports up to 4,096 characters.
    
    Returns:
        The created message object with properties such as:
        - name: Resource name of the created message (string)
        - text: The text content of the message (string)
        - sender: Information about who sent the message (object)
        - createTime: When the message was created (timestamp)
        - thread: Thread information including the thread's name (object)
        - Other properties as applicable
    
    API Reference:
        https://developers.google.com/chat/api/reference/rest/v1/spaces.messages/create
    """
    from google_chat import reply_to_thread
    
    if not space_name.startswith('spaces/'):
        space_name = f"spaces/{space_name}"
        
    return await reply_to_thread(space_name, thread_key, text)

@mcp.tool()
async def get_my_mentions(days: int = 7, space_id: str = None, include_sender_info: bool = True,
                      page_size: int = 50, page_token: str = None) -> Dict:
    """Get messages that mention the authenticated user from all spaces or a specific space.
    
    Searches for messages where the authenticated user is mentioned (by name or @mention)
    across all accessible spaces or within a specific space. This is useful for finding
    messages that require your attention or tracking conversations you've been included in.
    
    This tool uses a combination of the Google Chat API spaces.messages.list method and
    text filtering to identify mentions. It first retrieves messages based on the time
    period and then filters them for mentions of the current user's name or email.
    
    This tool requires OAuth authentication. It will retrieve messages where the 
    authenticated user was mentioned by username across all accessible spaces or in a specific space.
    
    Args:
        days: Number of days to look back for mentions (default: 7). 
              Specifies the time period to search within, from now back this many days.
        space_id: Optional space ID to check for mentions in a specific space. 
                 If provided, searches only this space. If null (default), searches all accessible spaces.
                 Can be either a full resource name (e.g., 'spaces/AAQAtjsc9v4') or just the ID portion.
        include_sender_info: Whether to include detailed sender information in the returned messages.
                            When true, each message will include a sender_info object with details
                            like email, display_name, and profile_photo. (default: True)
        page_size: Maximum number of messages to return per space (default: 50)
                  Only applies when space_id is provided; otherwise, all matching mentions are returned.
        page_token: Optional page token for pagination (only applicable when space_id is provided)
                   Use the nextPageToken from a previous response to get the next page of results.
    
    Returns:
        Dictionary containing:
        - messages: List of message objects where the current user is mentioned, each with properties like:
          - name: Resource name of the message (string, format: "spaces/{space_id}/messages/{message_id}")
          - text: Content of the message (string) containing the mention
          - sender: Information about who sent the message (object)
          - createTime: When the message was created (timestamp)
          - space_info: Added information about the space the message is from
          - sender_info: Additional sender details if include_sender_info=True
          - Other standard message properties
        - nextPageToken: Token for retrieving the next page of results, or null if no more results
                        (Only present when searching with a specific space_id)
    """
    from google_chat import get_user_mentions
    
    return await get_user_mentions(days, space_id, include_sender_info, page_size, page_token)

@mcp.tool()
async def get_my_user_info() -> Dict:
    """Get information about the currently authenticated user.
    
    Uses the Google People API (people.get method) to retrieve profile information
    about the currently authenticated user. This is useful for personalizing interactions,
    displaying user information, or determining user permissions.
    
    This tool requires OAuth authentication with people.* scope permissions.
    It retrieves user details including display name, email, and name components.
    
    Returns:
        Dictionary containing user details such as:
        - email: The primary email address of the authenticated user (string)
        - display_name: The full display name of the user (string)
        - given_name: The user's first or given name (string)
        - family_name: The user's last or family name (string)
        
    Note that all fields might not be available depending on the user's privacy settings
    and the permissions granted to the application.
    
    API Reference:
        https://developers.google.com/people/api/rest/v1/people/get
    """
    from google_chat import get_current_user_info
    
    return await get_current_user_info()

@mcp.tool()
async def get_chat_message(message_name: str, include_sender_info: bool = False) -> Dict:
    """Get a specific message by its resource name.
    
    Uses the Google Chat API spaces.messages.get method to retrieve detailed information
    about a specific message. This is useful for examining message content, metadata,
    and retrieving the full context of a message when you have its identifier.
    
    This tool requires OAuth authentication with appropriate messages access permissions.
    
    Args:
        message_name: The resource name of the message to retrieve. Must be the complete
                    resource name with format: 'spaces/{space_id}/messages/{message_id}'
                    Example: 'spaces/AAQAtjsc9v4/messages/UBHHVc_AAAA.UBHHVc_AAAA'
        include_sender_info: Whether to include detailed sender information in the returned message.
                            When true, the message will include a sender_info object with details
                            like email, display_name, and profile_photo. (default: False)
    
    Returns:
        The complete message object with properties such as:
        - name: Resource name of the message (string)
        - text: Content of the message (string)
        - sender: Information about who sent the message (object)
        - createTime: When the message was created (timestamp)
        - thread: Thread information if the message is part of a thread (object)
        - attachments: Any file attachments included with the message (array)
        - annotations: Any annotations like smart replies or link previews (array)
        - sender_info: Additional sender details if include_sender_info=True (object)
        - And other properties as applicable
    
    Raises:
        ValueError: If the message_name doesn't follow the required format
        Exception: If authentication fails or the message doesn't exist/can't be accessed
    
    API Reference:
        https://developers.google.com/chat/api/reference/rest/v1/spaces.messages/get
    """
    from google_chat import get_message
    
    if not message_name.startswith('spaces/'):
        raise ValueError("message_name must be a full resource name (spaces/*/messages/*)")
        
    return await get_message(message_name, include_sender_info)

@mcp.tool()
async def delete_chat_message(message_name: str) -> Dict:
    """Delete a message by its resource name.
    
    This tool requires OAuth authentication. It deletes a specific message.
    
    Args:
        message_name: The resource name of the message to delete (spaces/*/messages/*)
    
    Returns:
        Empty response on success
    """
    from google_chat import delete_message
    
    if not message_name.startswith('spaces/'):
        raise ValueError("message_name must be a full resource name (spaces/*/messages/*)")
        
    return await delete_message(message_name)

# Enhanced Google Chat operations

@mcp.tool()
async def search_messages(query: str, spaces: List[str] = None, max_results: int = 50, 
                    include_sender_info: bool = False, page_token: str = None,
                    filter_str: str = None, order_by: str = None) -> Dict:
    """Search for messages across all spaces or specified spaces.
    
    Performs a text-based search for messages containing the specified query text 
    across all accessible spaces or a defined list of spaces. This is useful for 
    finding specific messages or topics discussed in any conversation.
    
    This tool works by retrieving messages from each relevant space and filtering them 
    to find matches containing the query text. The search is case-insensitive.
    
    This tool requires OAuth authentication with appropriate space and message access permissions.
    
    Args:
        query: The search query string. Text to search for within messages. The search is 
              case-insensitive and finds messages where this text appears anywhere in the message content.
        spaces: Optional list of space names to search in. Each space name should be in the format
               'spaces/{space_id}'. If None (default), searches across all accessible spaces.
        max_results: Maximum number of results to return in total (default: 50).
                    When searching multiple spaces, results are collected until this limit is reached.
                    When searching a single space, this is used as the page size.
        include_sender_info: Whether to include detailed sender information in the returned messages.
                            When true, each message will include a sender_info object with details
                            like email, display_name, and profile_photo. (default: False)
        page_token: Optional page token for pagination (only applicable when searching a single space).
                   Use the nextPageToken from a previous response to get the next page of results.
        filter_str: Optional filter string in the format specified by Google Chat API.
                   For example: 'createTime > "2023-04-21T11:30:00-04:00"'
                   Used to restrict message retrieval before text-based filtering is applied.
        order_by: How messages are ordered before filtering, format: "<field> <direction>",
                 e.g., "createTime DESC". Default is typically chronological (createTime ASC).
        
    Returns:
        Dictionary containing:
        - messages: List of message objects matching the search query, each with properties like:
          - name: Resource name of the message (string)
          - text: Content of the message (string) containing the query
          - sender: Information about who sent the message (object)
          - createTime: When the message was created (timestamp)
          - space_info: Added information about the space the message is from
          - sender_info: Additional sender details if include_sender_info=True
          - Other standard message properties
        - nextPageToken: Token for retrieving the next page of results, or null if no more results
                        (Only present when searching with a single space)
    
    API Reference:
        https://developers.google.com/chat/api/reference/rest/v1/spaces.messages/list
        (The search functionality is built on top of the list method with text filtering)
    """
    from google_chat import search_messages
    
    return await search_messages(
        query, 
        spaces, 
        max_results, 
        include_sender_info, 
        page_token,
        filter_str,
        order_by
    )

@mcp.tool()
async def manage_space_members(space_name: str, operation: str, user_emails: List[str]) -> Dict:
    """Manage space membership - add or remove members.
    
    This tool requires OAuth authentication. It adds or removes members from a space.
    
    Args:
        space_name: The name/identifier of the space (e.g., 'spaces/AAQAtjsc9v4')
        operation: Either 'add' or 'remove'
        user_emails: List of user email addresses to add or remove
        
    Returns:
        Response with information about successful and failed operations
    """
    from google_chat import manage_space_members
    return await manage_space_members(space_name, operation, user_emails)

@mcp.tool()
async def add_emoji_reaction(message_name: str, emoji: str) -> Dict:
    """Add an emoji reaction to a message.
    
    This tool requires OAuth authentication. It adds an emoji reaction to a message.
    
    Args:
        message_name: The resource name of the message (spaces/*/messages/*)
        emoji: The emoji to add as a reaction (e.g. '👍', '❤️', etc.)
        
    Returns:
        Response with information about the added reaction
    """
    from google_chat import add_emoji_reaction
    return await add_emoji_reaction(message_name, emoji)

@mcp.tool()
async def upload_attachment(space_name: str, file_path: str, message_text: str = None) -> Dict:
    """Upload a file attachment to a Google Chat space.
    
    This tool requires OAuth authentication. It uploads a file as an attachment
    to a message in a Google Chat space.
    
    Args:
        space_name: The name/identifier of the space to send the attachment to
        file_path: Path to the file to upload (must be accessible to the server)
        message_text: Optional text message to accompany the attachment
        
    Returns:
        The created message object with the attachment
    """
    from google_chat import upload_attachment
    return await upload_attachment(space_name, file_path, message_text)

@mcp.tool()
async def batch_send_messages(messages: List[Dict]) -> Dict:
    """Send multiple messages in batch to different spaces.
    
    This tool requires OAuth authentication. It sends multiple messages to
    different spaces in one operation.
    
    Args:
        messages: List of message objects, each containing:
            - space_name: The name/identifier of the space to send to
            - text: Text content of the message
            - thread_key: Optional thread key to reply to
            - cards_v2: Optional card content
            
    Returns:
        Dictionary with results for each message, showing which were successful and which failed
    """
    from google_chat import batch_send_messages
    return await batch_send_messages(messages)

@mcp.tool()
async def send_file_message(space_name: str, file_path: str, message_text: str = None) -> Dict:
    """Send a message with file contents as a workaround for attachments.
    
    This tool requires OAuth authentication. Instead of using true file attachments, 
    this tool reads the file and includes its text content in the message body.
    
    Args:
        space_name: The name/identifier of the space to send the file content to
        file_path: Path to the file whose contents will be included in the message
        message_text: Optional text message to accompany the file contents
        
    Returns:
        The created message object
    """
    from google_chat import send_file_message
    return await send_file_message(space_name, file_path, message_text)

@mcp.tool()
async def send_file_content(space_name: str, file_path: str = None) -> Dict:
    """Send file content as a message (workaround for attachments).
    
    This tool requires OAuth authentication. Instead of true attachments,
    this sends the file content as a formatted message.
    
    Args:
        space_name: The space to send the message to
        file_path: Optional path to the file to send. If not provided, will use sample_attachment.txt
        
    Returns:
        The created message object
    """
    from google_chat import create_message
    import os
    
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
    except:
        file_contents = "[Error reading file]"
    
    # Format the message
    message = f"📄 **File Content: {os.path.basename(file_path)}**\n\n```\n{file_contents}\n```"
    
    if not space_name.startswith('spaces/'):
        space_name = f"spaces/{space_name}"
        
    return await create_message(space_name, message)

# Add new helper functions for sender information
@mcp.tool()
async def get_user_info_by_id(user_id: str) -> Dict:
    """Get information about a specific user by their user ID.
    
    Uses the Google People API to retrieve detailed profile information about a specific user
    identified by their ID. This helps to show user details when displaying messages or mentions,
    enabling personalized interactions in the Chat interface.
    
    This tool requires OAuth authentication with appropriate people.* scope permissions.
    It attempts to convert user IDs from Chat API format to People API format if necessary.
    
    Args:
        user_id: The ID of the user to get information for. This can be in several formats:
               - Google Chat format: 'users/1234567890'
               - People API format: 'people/1234567890'
               - Raw ID: '1234567890'
               The function will attempt to convert between formats as needed.
    
    Returns:
        Dictionary containing user details such as:
        - id: The original user ID provided (string)
        - email: The user's primary email address, if available (string or null)
        - display_name: The full display name of the user (string)
        - given_name: The user's first name, if available (string or null)
        - family_name: The user's last name, if available (string or null)
        - profile_photo: URL to the user's profile photo, if available (string or null)
        - error: Error description if user info retrieval fails but basic info is returned
    
    Note: If detailed information cannot be retrieved due to permissions or other issues,
    basic information will still be returned with the user ID and a generic display name.
    
    API Reference:
        https://developers.google.com/people/api/rest/v1/people/get
    """
    from google_chat import get_user_info_by_id
    return await get_user_info_by_id(user_id)

@mcp.tool()
async def get_message_with_sender_info(message_name: str) -> Dict:
    """Get a specific message with additional sender information.
    
    Retrieves a message by its resource name and automatically adds detailed sender
    information to the response. This is a convenience function that combines
    the spaces.messages.get API call with additional People API lookups for the sender.
    
    This tool requires OAuth authentication with both messages and people access permissions.
    
    Args:
        message_name: The resource name of the message to retrieve. Must be the complete
                    resource name with format: 'spaces/{space_id}/messages/{message_id}'
                    Example: 'spaces/AAQAtjsc9v4/messages/UBHHVc_AAAA.UBHHVc_AAAA'
    
    Returns:
        The message object with all standard properties plus enhanced sender information:
        - name: Resource name of the message (string)
        - text: Content of the message (string)
        - sender: Information about who sent the message from the Chat API (object)
        - sender_info: Additional details about the sender from the People API:
          - id: Sender's user ID (string)
          - email: Sender's email address, if available (string or null)
          - display_name: Sender's full name (string)
          - given_name: Sender's first name, if available (string or null)
          - family_name: Sender's last name, if available (string or null)
          - profile_photo: URL to sender's profile photo, if available (string or null)
        - Other standard message properties (createTime, thread, attachments, etc.)
    
    Raises:
        ValueError: If the message_name doesn't follow the required format
    
    API References:
        - https://developers.google.com/chat/api/reference/rest/v1/spaces.messages/get
        - https://developers.google.com/people/api/rest/v1/people/get
    """
    from google_chat import get_message_with_sender_info
    
    if not message_name.startswith('spaces/'):
        raise ValueError("message_name must be a full resource name (spaces/*/messages/*)")
        
    return await get_message_with_sender_info(message_name)

@mcp.tool()
async def list_messages_with_sender_info(space_name: str, 
                                       start_date: str = None,
                                       end_date: str = None,
                                       limit: int = 10,
                                       page_token: str = None) -> Dict:
    """List messages from a specific Google Chat space with sender information.
    
    Retrieves messages from a space and automatically enriches them with detailed
    sender information for each message. This is a convenience function that combines
    the spaces.messages.list API call with additional People API lookups for each sender.
    
    This tool requires OAuth authentication with both messages and people access permissions.
    
    Args:
        space_name: The resource name of the space to fetch messages from.
                   Format: 'spaces/{space_id}' (e.g., 'spaces/AAQAtjsc9v4')
        start_date: Optional start date in YYYY-MM-DD format (e.g., '2024-05-01')
                   If provided, only includes messages from this date forward (inclusive)
        end_date: Optional end date in YYYY-MM-DD format (e.g., '2024-05-05')
                 If provided, only includes messages up to this date (inclusive)
        limit: Maximum number of messages to return (default: 10)
               Controls the page size of the request.
        page_token: Optional page token for pagination. Use the nextPageToken from a
                   previous response to get the next page of results.
    
    Returns:
        Dictionary containing:
        - messages: List of message objects, each with standard properties plus:
          - sender_info: Additional details about the message sender:
            - id: Sender's user ID (string)
            - email: Sender's email address, if available (string or null)
            - display_name: Sender's full name (string)
            - given_name: Sender's first name, if available (string or null)
            - family_name: Sender's last name, if available (string or null)
            - profile_photo: URL to sender's profile photo, if available (string or null)
          - Other standard message properties (name, text, createTime, etc.)
        - nextPageToken: Token for retrieving the next page of results, or null if no more results
    
    Raises:
        ValueError: If date formats are invalid or dates are in wrong order
    
    API References:
        - https://developers.google.com/chat/api/reference/rest/v1/spaces.messages/list
        - https://developers.google.com/people/api/rest/v1/people/get
    """
    from google_chat import list_messages_with_sender_info
    from datetime import datetime, timezone
    
    # Parse dates if provided
    start_datetime = None
    end_datetime = None
    
    if start_date:
        try:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d').replace(
                hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
            )
        except ValueError:
            raise ValueError("start_date must be in YYYY-MM-DD format (e.g., '2024-03-22')")
    
    if end_date:
        try:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d').replace(
                hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc
            )
        except ValueError:
            raise ValueError("end_date must be in YYYY-MM-DD format (e.g., '2024-03-22')")
    
    if start_datetime and end_datetime and start_datetime > end_datetime:
        raise ValueError("start_date must be before end_date")
    
    return await list_messages_with_sender_info(
        space_name, 
        start_datetime, 
        end_datetime,
        limit,
        page_token
    )

@mcp.tool()
async def get_conversation_participants(space_name: str, 
                                       start_date: str = None,
                                       end_date: str = None,
                                       max_messages: int = 100) -> List[Dict]:
    """Get information about participants in a conversation or space.
    
    Identifies all unique users who have sent messages in a specific Google Chat space
    within the specified time range. This is useful for analyzing conversation participants, 
    creating user lists for notifications, or gathering metrics about space activity.
    
    This tool works by retrieving messages from the space and extracting unique sender 
    information, then fetches detailed profile information for each unique sender.
    
    This tool requires OAuth authentication with appropriate space and people permissions.
    
    Args:
        space_name: The resource name of the space to analyze.
                   Format: 'spaces/{space_id}' (e.g., 'spaces/AAQAtjsc9v4')
        start_date: Optional start date in YYYY-MM-DD format (e.g., '2024-05-01')
                   If provided, only considers messages from this date forward (inclusive)
        end_date: Optional end date in YYYY-MM-DD format (e.g., '2024-05-05')
                 If provided, only considers messages up to this date (inclusive)
        max_messages: Maximum number of messages to analyze for finding participants.
                     Higher values provide more complete participant lists but use more
                     API resources. (default: 100)
    
    Returns:
        List of dictionaries, each containing information about a unique participant:
        - id: The user's ID (string)
        - email: The user's email address, if available (string or null)
        - display_name: The user's full name (string)
        - given_name: The user's first name, if available (string or null)
        - family_name: The user's last name, if available (string or null)
        - profile_photo: URL to the user's profile image, if available (string or null)
        
    Note: The participant list is constructed based on message senders, so users who 
    have only read messages but never sent any in the time period will not be included.
    
    Raises:
        ValueError: If date formats are invalid or dates are in wrong order
    """
    from google_chat import get_conversation_participants
    from datetime import datetime, timezone
    
    # Parse dates if provided
    start_datetime = None
    end_datetime = None
    
    if start_date:
        try:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d').replace(
                hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
            )
        except ValueError:
            raise ValueError("start_date must be in YYYY-MM-DD format (e.g., '2024-03-22')")
    
    if end_date:
        try:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d').replace(
                hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc
            )
        except ValueError:
            raise ValueError("end_date must be in YYYY-MM-DD format (e.g., '2024-03-22')")
    
    if start_datetime and end_datetime and start_datetime > end_datetime:
        raise ValueError("start_date must be before end_date")
    
    return await get_conversation_participants(
        space_name, 
        start_datetime, 
        end_datetime,
        max_messages
    )

@mcp.tool()
async def summarize_conversation(space_name: str, 
                              message_limit: int = 10,
                              start_date: str = None,
                              end_date: str = None,
                              page_token: str = None,
                              filter_str: str = None) -> Dict:
    """Generate a summary of a conversation in a Google Chat space.
    
    Creates a comprehensive overview of a conversation in a Google Chat space, including
    space details, participant information, and recent messages. This is particularly useful
    for quickly understanding the context and content of a conversation.
    
    This tool combines several Google Chat API methods (spaces.get, spaces.messages.list)
    and participant analysis to provide a complete conversation snapshot.
    
    This tool requires OAuth authentication with access to space, messages, and people data.
    
    Args:
        space_name: The resource name of the space to summarize.
                   Format: 'spaces/{space_id}' (e.g., 'spaces/AAQAtjsc9v4')
        message_limit: Maximum number of messages to include in the summary. (default: 10)
                      This affects the number of messages returned, not the participant analysis.
        start_date: Optional start date in YYYY-MM-DD format (e.g., '2024-05-01')
                   If provided, only includes messages from this date forward (inclusive)
        end_date: Optional end date in YYYY-MM-DD format (e.g., '2024-05-05')
                 If provided, only includes messages up to this date (inclusive)
        page_token: Optional page token for pagination. Use the nextPageToken from a 
                   previous response to get the next page of results.
        filter_str: Optional filter string in the format specified by Google Chat API.
                   For example: 'createTime > "2023-04-21T11:30:00-04:00"'
                   Used to further restrict which messages are included in the summary.
    
    Returns:
        Dictionary containing comprehensive conversation information:
        - space: Details about the space itself
          - name: Resource name of the space (string)
          - display_name: Display name of the space (string)
          - type: Type of space (e.g., "ROOM", "DM") (string)
        - participants: List of users who have sent messages in the space, each with details like:
          - id: User ID (string)
          - display_name: User's full name (string)
          - email: User's email if available (string or null)
          - profile_photo: URL to profile photo if available (string or null)
        - participant_count: Number of unique participants found (integer)
        - messages: List of message objects included in the summary, each with standard message properties
        - message_count: Number of messages included (integer)
        - nextPageToken: Token for retrieving the next page of messages, or null if no more messages
    
    Raises:
        ValueError: If date formats are invalid or dates are in wrong order
    """
    from google_chat import summarize_conversation
    from datetime import datetime, timezone
    
    # Parse dates if provided
    start_datetime = None
    end_datetime = None
    
    if start_date:
        try:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d').replace(
                hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
            )
        except ValueError:
            raise ValueError("start_date must be in YYYY-MM-DD format (e.g., '2024-03-22')")
    
    if end_date:
        try:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d').replace(
                hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc
            )
        except ValueError:
            raise ValueError("end_date must be in YYYY-MM-DD format (e.g., '2024-03-22')")
    
    if start_datetime and end_datetime and start_datetime > end_datetime:
        raise ValueError("start_date must be before end_date")
    
    return await summarize_conversation(
        space_name,
        message_limit,
        start_datetime,
        end_datetime,
        page_token,
        filter_str
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='MCP Server with Google Chat Authentication')
    parser.add_argument('-local-auth', action='store_true', help='Run the local authentication server')
    parser.add_argument('--host', default='localhost', help='Host to bind the server to (default: localhost)')
    parser.add_argument('--port', type=int, default=8000, help='Port to run the server on (default: 8000)')
    parser.add_argument('--token-path', default='token.json', help='Path to store OAuth token (default: token.json)')
    
    args = parser.parse_args()
    
    # Set the token path for OAuth storage
    set_token_path(args.token_path)
    
    if args.local_auth:
        print(f"\nStarting local authentication server at http://{args.host}:{args.port}")
        print("Available endpoints:")
        print("  - /auth   : Start OAuth authentication flow")
        print("  - /status : Check authentication status")
        print("  - /auth/callback : OAuth callback endpoint")
        print(f"\nDefault callback URL: {DEFAULT_CALLBACK_URL}")
        print(f"Token will be stored at: {args.token_path}")
        print("\nPress CTRL+C to stop the server")
        print("-" * 50)
        run_auth_server(port=args.port, host=args.host)
    else:
        mcp.run()