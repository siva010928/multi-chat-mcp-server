from datetime import datetime, timezone

from src.google_chat.spaces import list_chat_spaces, manage_space_members
from src.google_chat.summary import get_conversation_participants, summarize_conversation
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
                                        start_date: str = None,
                                        end_date: str = None,
                                        max_messages: int = 100) -> list[dict]:
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
                                 start_date: str = None,
                                 end_date: str = None,
                                 page_token: str = None,
                                 filter_str: str = None) -> dict:
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