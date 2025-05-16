import os
from datetime import datetime, timezone

from src.google_chat.attachments import send_file_message, upload_attachment
from src.google_chat.messages import (
    list_space_messages, create_message, reply_to_thread, get_message, delete_message,
    update_message, add_emoji_reaction, batch_send_messages, list_messages_with_sender_info,
    get_message_with_sender_info
)

from src.mcp_instance import mcp


@mcp.tool()
async def send_message_tool(space_name: str, text: str) -> dict:
    print("Registering send_message tool")

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

    if not space_name.startswith('spaces/'):
        space_name = f"spaces/{space_name}"

    return await create_message(space_name, text)

# @mcp.tool()
# async def send_card_message_tool(space_name: str, text: str, card_title: str, card_description: str = None) -> dict:
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
# async def send_interactive_card_tool(
#     space_name: str,
#     card_title: str,
#     card_subtitle: str = None,
#     card_image_url: str = None,
#     button_text: str = None,
#     button_url: str = None,
#     button_action_function: str = None,
#     section_header: str = None,
#     section_content: str = None
# ) -> dict:
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
async def update_chat_message_tool(message_name: str, new_text: str = None) -> dict:
    """Update an existing message in a Google Chat space.

    This tool requires OAuth authentication. It can update the text content of an existing message.

    Args:
        message_name: The full resource name of the message to update (spaces/*/messages/*)
        new_text: New text content for the message

    Returns:
        The updated message object
    """

    if not message_name.startswith('spaces/'):
        raise ValueError("message_name must be a full resource name (spaces/*/messages/*)")

    return await update_message(message_name, new_text)


@mcp.tool()
async def reply_to_message_thread_tool(space_name: str, thread_key: str, text: str) -> dict:
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

    if not space_name.startswith('spaces/'):
        space_name = f"spaces/{space_name}"

    return await reply_to_thread(space_name, thread_key, text)


@mcp.tool()
async def get_space_messages_tool(space_name: str,
                             start_date: str,
                             end_date: str = None,
                             include_sender_info: bool = False,
                             page_size: int = 25,
                             page_token: str = None,
                             filter_str: str = None,
                             order_by: str = None,
                             show_deleted: bool = False) -> dict:
    """List messages from a specific Google Chat space with optional time filtering.

    Uses the Google Chat API spaces.messages.list method to retrieve messages from a specific space.
    Messages can be filtered by time range, sorted, and paginated. This function allows you to
    view historical messages in a conversation, find specific content, or analyze communication patterns.

    NOTE: Use this tool only when you need raw message history without filtering by content.
    If you're looking for specific messages by content, use search_messages instead.
    DO NOT call this after search_messages - search_messages already provides complete message data.

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
        - source: "get_space_messages" (to help differentiate from other message retrieval tools)

    Raises:
        ValueError: If the date format is invalid or dates are in wrong order

    API Reference:
        https://developers.google.com/chat/api/reference/rest/v1/spaces.messages/list
    """

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
    result = await list_space_messages(
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

    # Add source marker to help LLMs understand this is from get_space_messages
    if isinstance(result, dict):
        result["source"] = "get_space_messages"

    return result

@mcp.tool()
async def get_chat_message_tool(message_name: str, include_sender_info: bool = False) -> dict:
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

    if not message_name.startswith('spaces/'):
        raise ValueError("message_name must be a full resource name (spaces/*/messages/*)")

    return await get_message(message_name, include_sender_info)


@mcp.tool()
async def delete_chat_message_tool(message_name: str) -> dict:
    """Delete a message by its resource name.

    This tool requires OAuth authentication. It deletes a specific message.

    Args:
        message_name: The resource name of the message to delete (spaces/*/messages/*)

    Returns:
        Empty response on success
    """

    if not message_name.startswith('spaces/'):
        raise ValueError("message_name must be a full resource name (spaces/*/messages/*)")

    return await delete_message(message_name)


@mcp.tool()
async def get_message_with_sender_info_tool(message_name: str) -> dict:
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

    if not message_name.startswith('spaces/'):
        raise ValueError("message_name must be a full resource name (spaces/*/messages/*)")

    return await get_message_with_sender_info(message_name)


@mcp.tool()
async def list_messages_with_sender_info_tool(space_name: str,
                                         start_date: str = None,
                                         end_date: str = None,
                                         limit: int = 10,
                                         page_token: str = None) -> dict:
    """list messages from a specific Google Chat space with sender information.

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
        dictionary containing:
        - messages: list of message objects, each with standard properties plus:
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
async def add_emoji_reaction_tool(message_name: str, emoji: str) -> dict:
    """Add an emoji reaction to a message.

    This tool requires OAuth authentication. It adds an emoji reaction to a message.

    Args:
        message_name: The resource name of the message (spaces/*/messages/*)
        emoji: The emoji to add as a reaction (e.g. '👍', '❤️', etc.)

    Returns:
        Response with information about the added reaction
    """
    return await add_emoji_reaction(message_name, emoji)


@mcp.tool()
async def upload_attachment_tool(space_name: str, file_path: str, message_text: str = None) -> dict:
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
    return await upload_attachment(space_name, file_path, message_text)


@mcp.tool()
async def batch_send_messages_tool(messages: list[dict]) -> dict:
    """Send multiple messages in batch to different spaces.

    This tool requires OAuth authentication. It sends multiple messages to
    different spaces in one operation.

    Args:
        messages: list of message objects, each containing:
            - space_name: The name/identifier of the space to send to
            - text: Text content of the message
            - thread_key: Optional thread key to reply to
            - cards_v2: Optional card content

    Returns:
        dictionary with results for each message, showing which were successful and which failed
    """
    return await batch_send_messages(messages)


@mcp.tool()
async def send_file_message_tool(space_name: str, file_path: str, message_text: str = None) -> dict:
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
    return await send_file_message(space_name, file_path, message_text)


@mcp.tool()
async def send_file_content_tool(space_name: str, file_path: str = None) -> dict:
    """Send file content as a message (workaround for attachments).

    This tool requires OAuth authentication. Instead of true attachments,
    this sends the file content as a formatted message.

    Args:
        space_name: The space to send the message to
        file_path: Optional path to the file to send. If not provided, will use sample_attachment.txt

    Returns:
        The created message object
    """

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