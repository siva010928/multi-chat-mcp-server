from datetime import datetime, timezone

from src.providers.google_chat.api.spaces import list_chat_spaces, manage_space_members
from src.providers.google_chat.api.summary import get_conversation_participants, summarize_conversation
from src.mcp_instance import mcp


@mcp.tool()
async def get_chat_spaces_tool() -> list[dict]:
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
async def get_conversation_participants_tool(space_name: str,
                                        max_messages: int = 100,
                                        days_window: int = 3,
                                        offset: int = 0) -> list[dict]:
    """Get information about participants in a conversation or space.

    Identifies all unique users who have sent messages in a specific Google Chat space
    within the specified time range. This is useful for analyzing conversation participants,
    creating user lists for notifications, or gathering metrics about space activity.

    This tool works by retrieving messages from the space and extracting unique sender
    information, then fetches detailed profile information for each unique sender.

    COMMON USE CASES:
    - Identifying active team members in a project discussion
    - Creating a list of stakeholders who participated in a conversation
    - Finding who to follow up with about a specific topic
    - Understanding team engagement patterns

    This tool requires OAuth authentication with appropriate space and people permissions.

    DATE FILTERING BEHAVIOR:
    The date range is calculated automatically based on days_window and offset parameters:
    - end_date = current date minus offset days
    - start_date = end_date minus days_window days

    For example:
    - With days_window=3, offset=0: Messages from the last 3 days
    - With days_window=7, offset=0: Messages from the last 7 days
    - With days_window=3, offset=7: Messages from 10 to 7 days ago

    Args:
        space_name: The resource name of the space to analyze.
                   Format: 'spaces/{space_id}' (e.g., 'spaces/AAQAtjsc9v4')
                   
                   IMPORTANT: You can get space IDs using the get_chat_spaces_tool.
                   
        max_messages: Maximum number of messages to analyze for finding participants.
                     Higher values provide more complete participant lists but use more
                     API resources. (default: 100)
                     
                     SIZING GUIDELINES:
                     - 50-100: Good for regular team chats (better performance)
                     - 200-500: For large spaces with many members
                     - 1000+: For comprehensive analysis of very active spaces
                     
        days_window: Number of days to look back for messages (default: 3).
                    This parameter controls the date range for message retrieval.
                    For example, if days_window=3, messages from the last 3 days will be retrieved.
                    
                    USAGE STRATEGY:
                    - 1-3 days: Active current participants
                    - 7 days: Weekly participation patterns
                    - 30 days: Monthly activity analysis
                    
        offset: Number of days to offset the end date from today (default: 0). 
               For example, if offset=3, the end date will be 3 days before today,
               and with days_window=3, messages from 6 to 3 days ago will be retrieved.
               
               COMMON PATTERNS:
               - Recent activity: offset=0 (default)
               - Previous week: offset=7, days_window=7
               - Compare different time periods by using different offsets

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
    
    Examples:
    
    1. Get current active participants (last 3 days):
       ```python
       get_conversation_participants_tool(
           space_name="spaces/AAQAtjsc9v4"
       )
       ```
       
    2. Comprehensive participant analysis (last 30 days, looking at up to 500 messages):
       ```python
       get_conversation_participants_tool(
           space_name="spaces/AAQAtjsc9v4",
           max_messages=500,
           days_window=30
       )
       ```
       
    3. Compare participation between different time periods:
       ```python
       # Get participants from this week
       current_week_participants = get_conversation_participants_tool(
           space_name="spaces/AAQAtjsc9v4",
           days_window=7
       )
       
       # Get participants from last week
       previous_week_participants = get_conversation_participants_tool(
           space_name="spaces/AAQAtjsc9v4",
           days_window=7,
           offset=7  # Skip the most recent 7 days
       )
       ```
       
    4. Extract emails for all active participants in the last month:
       ```python
       participants = get_conversation_participants_tool(
           space_name="spaces/AAQAtjsc9v4", 
           days_window=30,
           max_messages=300
       )
       
       # Extract emails (excluding None values)
       email_list = [p["email"] for p in participants if p.get("email")]
       ```
       
    5. Identify the most recently active participants:
       ```python
       recent_participants = get_conversation_participants_tool(
           space_name="spaces/AAQAtjsc9v4",
           days_window=1,  # Just the last day
           max_messages=50  # Focus on the most recent messages
       )
       ```

    Raises:
        ValueError: If date formats are invalid or dates are in wrong order
    """

    return await get_conversation_participants(
        space_name,
        max_messages,
        days_window,
        offset
    )


@mcp.tool()
async def manage_space_members_tool(space_name: str, operation: str, user_emails: list[str]) -> dict:
    """Manage space membership - add or remove members.

    This tool requires OAuth authentication. It adds or removes members from a space.

    Args:
        space_name: The name/identifier of the space (e.g., 'spaces/AAQAtjsc9v4')
        operation: Either 'add' or 'remove'
        user_emails: List of user email addresses to add or remove

    Returns:
        Response with information about successful and failed operations
    """
    return await manage_space_members(space_name, operation, user_emails)


@mcp.tool()
async def summarize_conversation_tool(space_name: str,
                                 message_limit: int = 10,
                                 page_token: str = None,
                                 filter_str: str = None,
                                 days_window: int = 3,
                                 offset: int = 0) -> dict:
    """Generate a summary of a conversation in a Google Chat space.

    Creates a comprehensive overview of a conversation in a Google Chat space, including
    space details, participant information, and recent messages. This is particularly useful
    for quickly understanding the context and content of a conversation.

    This tool combines several Google Chat API methods (spaces.get, spaces.messages.list)
    and participant analysis to provide a complete conversation snapshot.

    This tool requires OAuth authentication with access to space, messages, and people data.

    DATE FILTERING BEHAVIOR:
    The date range is calculated automatically based on days_window and offset parameters:
    - end_date = current date minus offset days
    - start_date = end_date minus days_window days

    For example:
    - With days_window=3, offset=0: Messages from the last 3 days
    - With days_window=7, offset=0: Messages from the last 7 days
    - With days_window=3, offset=7: Messages from 10 to 7 days ago

    Args:
        space_name: The resource name of the space to summarize.
                   Format: 'spaces/{space_id}' (e.g., 'spaces/AAQAtjsc9v4')
        message_limit: Maximum number of messages to include in the summary. (default: 10)
                      This affects the number of messages returned, not the participant analysis.
        page_token: Optional page token for pagination. Use the nextPageToken from a 
                   previous response to get the next page of results.
        filter_str: Optional filter string in the format specified by Google Chat API.
                   For example: 'createTime > "2023-04-21T11:30:00-04:00"'
                   Used to further restrict which messages are included in the summary.
        days_window: Number of days to look back for messages (default: 3).
                    This parameter controls the date range for message retrieval.
                    For example, if days_window=3, messages from the last 3 days will be retrieved.
        offset: Number of days to offset the end date from today (default: 0). 
               For example, if offset=3, the end date will be 3 days before today,
               and with days_window=3, messages from 6 to 3 days ago will be retrieved.

    Returns:
        dictionary containing comprehensive conversation information:
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

    return await summarize_conversation(
        space_name,
        message_limit,
        page_token,
        filter_str,
        days_window,
        offset
    )
