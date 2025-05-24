import os
from datetime import datetime, timezone

from src.providers.google_chat.api.attachments import send_file_message, upload_attachment, send_file_content
from src.providers.google_chat.api.messages import (
    list_space_messages, create_message, reply_to_thread, get_message, delete_message,
    update_message, add_emoji_reaction, batch_send_messages, list_messages_with_sender_info,
    get_message_with_sender_info
)

from src.providers.google_chat.mcp_instance import mcp, tool


@tool()
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

                   IMPORTANT: You can get space IDs using the get_chat_spaces_tool.

        text: Text content of the message. Can include plain text or limited markdown formatting,
              including bold, italic, strikethrough, and inline code. Supports up to 4,096 characters.
              Emojis (Unicode) are also supported.

              FORMATTING TIPS:
              - Use *asterisks* for bold text
              - Use _underscores_ for italic text
              - Use ~tildes~ for strikethrough text
              - Use `backticks` for inline code
              - Multiple paragraphs are supported (use blank lines)
              - URLs will be automatically hyperlinked
              - Use Unicode emoji symbols directly: "👍 Great work!"
              - Supports numbered and bulleted lists

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

    Examples:

    1. Basic message:
       ```python
       send_message_tool(
           space_name="spaces/AAQAtjsc9v4",
           text="Hello team! This is a simple message."
       )
       ```

    2. Message with formatting:
       ```python
       send_message_tool(
           space_name="AAQAtjsc9v4",  # Space ID without 'spaces/' prefix
           text="*Important Update*\n\nThe meeting scheduled for tomorrow has been _rescheduled_ to Friday at 2pm.\n\nPlease update your calendars accordingly."
       )
       ```

    3. Technical message with code formatting:
       ```python
       send_message_tool(
           space_name="spaces/AAQAtjsc9v4", 
           text="The API is returning a `404` error when accessing `/api/users`. Please check if the endpoint is correctly configured."
       )
       ```

    4. Status update with emoji:
       ```python
       send_message_tool(
           space_name="spaces/AAQAtjsc9v4",
           text="🚀 Deployment completed successfully!\n\n✅ All tests passed\n✅ Database migration successful\n✅ New features enabled"
       )
       ```
    """

    if not space_name.startswith('spaces/'):
        space_name = f"spaces/{space_name}"

    return await create_message(space_name, text)

# @tool()
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

# @tool()
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

@tool()
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


@tool()
async def reply_to_message_thread_tool(space_name: str, thread_key: str, text: str, file_path: str = None) -> dict:
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

                   IMPORTANT: You can get space IDs using the get_chat_spaces_tool.

        thread_key: The identifier for the thread to reply to. This can be:
                   - A thread key (e.g., 'thread123')
                   - A thread name (e.g., 'spaces/AAQAtjsc9v4/threads/thread123')
                   - A message ID (the system will attempt to find its thread)

                   IMPORTANT: When replying to a message, you can extract the thread_key from 
                   the original message's 'name' field, which has the format:
                   'spaces/{space_id}/messages/{message_id}'

                   THREAD RETRIEVAL STRATEGIES:
                   1. Use search_messages_tool to find messages with specific content
                   2. Extract thread_key from message objects in the search results
                   3. Use that thread_key with this tool to continue the conversation

                   CREATING NEW THREADS VS REPLYING:
                   - To start a new thread, use send_message_tool
                   - To continue an existing thread, use this tool

        text: Text content of the reply. Can include plain text or limited markdown formatting,
              including bold, italic, strikethrough, and inline code. Supports up to 4,096 characters.

              FORMATTING TIPS:
              - Use *asterisks* for bold text
              - Use _underscores_ for italic text
              - Use ~tildes~ for strikethrough text
              - Use `backticks` for inline code
              - Multiple paragraphs are supported (use blank lines)
              - URLs will be automatically hyperlinked
              - Use Unicode emoji symbols directly: "👍 Great work!"
              - Supports numbered and bulleted lists

        file_path: Optional path to a file to attach to the reply. If provided, the file will be
                  read and its contents included in the message. For text files, the content will
                  be included directly. For binary files, a message indicating it's a binary file
                  will be included.

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

    Examples:

    1. Basic reply to a thread:
       ```python
       reply_to_message_thread_tool(
           space_name="spaces/AAQAtjsc9v4",
           thread_key="spaces/AAQAtjsc9v4/threads/thread123",
           text="Thanks for the update! I'll review this today."
       )
       ```

    2. Reply using just the message ID:
       ```python
       reply_to_message_thread_tool(
           space_name="AAQAtjsc9v4", 
           thread_key="UBHHVc_AAAA.UBHHVc_AAAA",
           text="I've completed the task. Here's what I found..."
       )
       ```

    3. Reply with a file attachment:
       ```python
       reply_to_message_thread_tool(
           space_name="spaces/AAQAtjsc9v4",
           thread_key="UBHHVc_AAAA.UBHHVc_AAAA",
           text="Here's the report you requested.",
           file_path="/path/to/report.txt"
       )
       ```

    4. Reply from search results (workflow):
       ```python
       # First, search for the message you want to reply to
       search_results = search_messages_tool(
           query="update on project status",
           spaces=["spaces/AAQAtjsc9v4"]
       )

       # Get the first message and extract its ID
       if search_results["messages"]:
           message = search_results["messages"][0]
           message_name = message["name"]  # Format: spaces/{space}/messages/{message}
           space_id = message_name.split('/')[1]
           message_id = message_name.split('/')[-1]

           # Reply to the thread
           reply_to_message_thread_tool(
               space_name=space_id,
               thread_key=message_id,
               text="Thanks for the project update. I have a few questions..."
           )
       ```

    5. Technical discussion reply with formatted code:
       ```python
       reply_to_message_thread_tool(
           space_name="spaces/AAQAtjsc9v4",
           thread_key="UBHHVc_AAAA.UBHHVc_AAAA",
           text="I think we need to update this function:\n\n```python\ndef process_data(input):\n    # Add validation here\n    result = transform(input)\n    return result\n```"
       )
       ```
    """
    if not space_name.startswith('spaces/'):
        space_name = f"spaces/{space_name}"

    return await reply_to_thread(space_name, thread_key, text, file_path=file_path)


@tool()
async def get_space_messages_tool(space_name: str,
                             include_sender_info: bool = False,
                             page_size: int = 25,
                             page_token: str = None,
                             filter_str: str = None,
                             order_by: str = None,
                             show_deleted: bool = False,
                             days_window: int = 3,
                             offset: int = 0) -> dict:
    """List messages from a specific Google Chat space with optional time filtering.

    Uses the Google Chat API spaces.messages.list method to retrieve messages from a specific space.
    Messages can be filtered by time range, sorted, and paginated. This function allows you to
    view historical messages in a conversation, find specific content, or analyze communication patterns.

    NOTE: Use this tool only when you need raw message history without filtering by content.
    If you're looking for specific messages by content, use search_messages instead.
    DO NOT call this after search_messages - search_messages already provides complete message data.

    WHEN TO USE THIS TOOL vs. SEARCH_MESSAGES_TOOL:
    - Use get_space_messages_tool when you need the complete conversation history and context
    - Use search_messages_tool when looking for specific content or keywords
    - get_space_messages_tool is better for exploring recent conversations chronologically
    - search_messages_tool is better for finding specific messages across longer time periods

    This tool requires OAuth authentication. The space_name should be in the format
    'spaces/your_space_id'.

    DATE FILTERING BEHAVIOR:
    The date range is calculated automatically based on days_window and offset parameters:
    - end_date = current date minus offset days
    - start_date = end_date minus days_window days

    For example:
    - With days_window=3, offset=0: Messages from the last 3 days
    - With days_window=7, offset=0: Messages from the last 7 days
    - With days_window=3, offset=7: Messages from 10 to 7 days ago

    Messages are always returned in descending order by creation time (newest first)
    unless a different order_by is specified.

    Args:
        space_name: The resource name of the space to fetch messages from
                   (string, format: "spaces/{space_id}")

                   IMPORTANT: You can get space IDs using the get_chat_spaces_tool.

        include_sender_info: Whether to include detailed sender information in the returned messages.
                            When true, each message will include a sender_info object with details
                            like email, display_name, and profile_photo. (default: False)

                            Set to True when you need to analyze who sent which messages.

        page_size: Maximum number of messages to return in a single request.
                  Ranges from 1 to 1000. (default: 25, max: 1000)

                  USAGE STRATEGY:
                  - Small values (25-50) for quick checks and better performance
                  - Larger values (100-1000) for comprehensive analysis or extracting full context

        page_token: Page token from a previous request for pagination. Use the nextPageToken
                   from a previous response to get the next page of results.

                   Use this for systematically processing large message histories.

        filter_str: Optional filter string in the format specified by Google Chat API.
                   For example: 'createTime > "2023-04-21T11:30:00-04:00"'
                   See API reference for full filter syntax options.

                   ADVANCED FILTERING:
                   - Date-based: 'createTime > "2023-04-21T11:30:00-04:00"'
                   - Combined filters: 'createTime > "2023-04-21T00:00:00Z" AND createTime < "2023-04-22T00:00:00Z"'

                   Usually not needed as days_window and offset provide simpler date filtering.

        order_by: How messages are ordered, format: "<field> <direction>",
                 e.g., "createTime DESC" (default: "createTime desc" - newest first)

                 OPTIONS:
                 - "createTime desc" (newest first - DEFAULT)
                 - "createTime asc" (oldest first - for chronological analysis)

        show_deleted: Whether to include deleted messages in the results (default: False)
                     Set to True if you need to see messages that were deleted.

        days_window: Number of days to look back for messages (default: 3).
                    This parameter controls the date range for message retrieval.
                    For example, if days_window=3, messages from the last 3 days will be retrieved.

                    SIZING GUIDELINES:
                    - 1-3 days: Recent conversations
                    - 7 days: Weekly review
                    - 30 days: Monthly review
                    - Larger values may impact performance

        offset: Number of days to offset the end date from today (default: 0). 
               For example, if offset=3, the end date will be 3 days before today,
               and with days_window=3, messages from 6 to 3 days ago will be retrieved.

               INCREMENTAL SEARCH STRATEGY:
               To efficiently analyze historical messages in chunks:
               1. Start with recent messages: days_window=3, offset=0
               2. Move backward in time by increasing offset:
                  - Second batch: days_window=3, offset=3
                  - Third batch: days_window=3, offset=6
               3. Always track nextPageToken to ensure complete coverage

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
        - message_count: Number of messages returned (integer)

    Raises:
        ValueError: If the date format is invalid or dates are in wrong order

    Examples:

    1. Get recent messages from a space:
       ```python
       get_space_messages_tool(
           space_name="spaces/AAQAtjsc9v4",
           page_size=50
       )
       ```

    2. Get messages with detailed sender information:
       ```python
       get_space_messages_tool(
           space_name="spaces/AAQAtjsc9v4",
           include_sender_info=True,
           page_size=50
       )
       ```

    3. Get messages from one week ago (non-overlapping with recent messages):
       ```python
       get_space_messages_tool(
           space_name="spaces/AAQAtjsc9v4",
           days_window=7,
           offset=7,  # Skip the last 7 days
           page_size=100
       )
       ```

    4. Retrieve messages chronologically (oldest first):
       ```python
       get_space_messages_tool(
           space_name="spaces/AAQAtjsc9v4",
           order_by="createTime asc",
           days_window=30,  # Last month
           page_size=100
       )
       ```

    5. Pagination example for handling large message histories:
       ```python
       # Get first page of messages
       first_page = get_space_messages_tool(
           space_name="spaces/AAQAtjsc9v4",
           page_size=100
       )

       # Process messages from first page
       messages = first_page.get("messages", [])

       # If there are more pages, get the next page
       next_page_token = first_page.get("nextPageToken")
       if next_page_token:
           second_page = get_space_messages_tool(
               space_name="spaces/AAQAtjsc9v4",
               page_size=100,
               page_token=next_page_token
           )
           # Add messages from second page
           messages.extend(second_page.get("messages", []))
       ```

    API Reference:
        https://developers.google.com/chat/api/reference/rest/v1/spaces.messages/list
    """

    if not space_name.startswith('spaces/'):
        space_name = f"spaces/{space_name}"

    # Always use 'createTime desc' (newest first) if not specified
    if order_by is None:
        order_by = "createTime desc"

    # Get messages with date filtering
    result = await list_space_messages(
        space_name,
        include_sender_info=include_sender_info,
        page_size=page_size,
        page_token=page_token,
        filter_str=filter_str,
        order_by=order_by,
        show_deleted=show_deleted,
        days_window=days_window,
        offset=offset
    )

    # Add source field for identification
    result["source"] = "get_space_messages"

    # Add message count to the result
    result["message_count"] = len(result.get("messages", []))

    return result

@tool()
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


@tool()
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


@tool()
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


@tool()
async def list_messages_with_sender_info_tool(space_name: str,
                                         limit: int = 10,
                                         page_token: str = None,
                                         days_window: int = 3,
                                         offset: int = 0) -> dict:
    """list messages from a specific Google Chat space with sender information.

    Retrieves messages from a space and automatically enriches them with detailed
    sender information for each message. This is a convenience function that combines
    the spaces.messages.list API call with additional People API lookups for each sender.

    This tool requires OAuth authentication with both messages and people access permissions.

    DATE FILTERING BEHAVIOR:
    The date range is calculated automatically based on days_window and offset parameters:
    - end_date = current date minus offset days
    - start_date = end_date minus days_window days

    For example:
    - With days_window=3, offset=0: Messages from the last 3 days
    - With days_window=7, offset=0: Messages from the last 7 days
    - With days_window=3, offset=7: Messages from 10 to 7 days ago

    Messages are always returned in descending order by creation time (newest first).

    Args:
        space_name: The resource name of the space to fetch messages from.
                   Format: 'spaces/{space_id}' (e.g., 'spaces/AAQAtjsc9v4')
        limit: Maximum number of messages to return (default: 10)
               Controls the page size of the request.
        page_token: Optional page token for pagination. Use the nextPageToken from a
                   previous response to get the next page of results.
        days_window: Number of days to look back for messages (default: 3).
                    This parameter controls the date range for message retrieval.
                    For example, if days_window=3, messages from the last 3 days will be retrieved.
        offset: Number of days to offset the end date from today (default: 0). 
               For example, if offset=3, the end date will be 3 days before today,
               and with days_window=3, messages from 6 to 3 days ago will be retrieved.

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
        - message_count: Number of messages returned (integer)

    Raises:
        ValueError: If date formats are invalid or dates are in wrong order

    API References:
        - https://developers.google.com/chat/api/reference/rest/v1/spaces.messages/list
        - https://developers.google.com/people/api/rest/v1/people/get
    """

    # Call list_space_messages with days_window and offset
    result = await list_space_messages(
        space_name,
        include_sender_info=True,
        page_size=limit,
        page_token=page_token,
        order_by="createTime desc",  # Default to newest first
        days_window=days_window,
        offset=offset
    )

    # Add message count if not already present
    if "message_count" not in result:
        result["message_count"] = len(result.get("messages", []))

    return result


@tool()
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


@tool()
async def upload_attachment_tool(space_name: str, file_path: str, message_text: str = None, thread_key: str = None) -> dict:
    """Upload a file attachment to a Google Chat space.

    This tool requires OAuth authentication. It uploads a file as an attachment
    to a message in a Google Chat space. The file can be sent as a new message
    or as a reply to an existing thread.

    Args:
        space_name: The name/identifier of the space to send the attachment to
        file_path: Path to the file to upload (must be accessible to the server)
        message_text: Optional text message to accompany the attachment
        thread_key: Optional thread key to reply to. If provided, the attachment
                   will be sent as a reply to the specified thread.

    Returns:
        The created message object with the attachment
    """
    return await upload_attachment(space_name, file_path, message_text, thread_key)


@tool()
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


@tool()
async def send_file_message_tool(space_name: str, file_path: str, message_text: str = None, thread_key: str = None) -> dict:
    """Send a message with file contents as a workaround for attachments.

    This tool requires OAuth authentication. Instead of using true file attachments,
    this tool reads the file and includes its text content in the message body.
    The file content can be sent as a new message or as a reply to an existing thread.

    Args:
        space_name: The name/identifier of the space to send the file content to
        file_path: Path to the file whose contents will be included in the message
        message_text: Optional text message to accompany the file contents
        thread_key: Optional thread key to reply to. If provided, the file content
                   will be sent as a reply to the specified thread.

    Returns:
        The created message object
    """
    return await send_file_message(space_name, file_path, message_text, thread_key)


@tool()
async def send_file_content_tool(space_name: str, file_path: str = None, thread_key: str = None) -> dict:
    """Send file content as a message (workaround for attachments).

    This tool requires OAuth authentication. Instead of true attachments,
    this sends the file content as a formatted message. The file content can be sent
    as a new message or as a reply to an existing thread.

    Args:
        space_name: The space to send the message to
        file_path: Optional path to the file to send. If not provided, will use sample_attachment.txt
        thread_key: Optional thread key to reply to. If provided, the file content
                   will be sent as a reply to the specified thread.

    Returns:
        The created message object
    """
    return await send_file_content(space_name, file_path, thread_key)
