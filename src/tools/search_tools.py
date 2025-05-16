from src.google_chat.advanced_search import advanced_search_messages
from src.google_chat.summary import get_my_mentions
from src.mcp_instance import mcp


@mcp.tool()
async def search_messages_tool(query: str,
                          search_mode: str = None,
                          spaces: list[str] = None,
                          max_results: int = 50,
                          include_sender_info: bool = False,
                          start_date: str = None,
                          end_date: str = None,
                          filter_str: str = None) -> dict:
    """Search for messages across all spaces or specified spaces.

    This tool performs advanced search for messages in Google Chat spaces using various search strategies.
    It's the primary tool for finding specific content in conversations by supporting multiple search modes
    including regex pattern matching, semantic search, and exact substring matching.

    Args:
        query: The search query string. Format depends on the search_mode:
               - For "regex" (default): Regular expression pattern like "ci[ /\\-_]?cd" to find "CI/CD" in any format
               - For "semantic": Natural language description like "continuous integration pipeline"
               - For "exact": Simple substring like "meeting notes"

               IMPORTANT NOTES:
               - Regex searches are case-insensitive by default ("cicd" will match "CICD")
               - For finding specific terms with variations, use regex search
               - For concept/meaning-based search, use semantic search
               - When using regex special characters like []/()-+*?, escape them with \\ (e.g., "CI\\/CD")

        search_mode: The search strategy to use. One of:
                    - "regex" (DEFAULT): Pattern-based search that supports wildcards and symbols
                    - "semantic": Meaning-based search that can find conceptually related messages
                    - "exact": Simple substring search (fastest but least flexible)
                    - "hybrid": Combines multiple search approaches

                    If not specified, "regex" is used as the default mode.

        spaces: Optional list of space names to search in. Format: ["spaces/SPACE_ID1", "spaces/SPACE_ID2"]
                If None, searches across all accessible spaces.

        max_results: Maximum number of results to return (default: 50).

        include_sender_info: When True, adds detailed sender information to each message including
                            email address, display name, and profile photo URL (default: False).

        start_date: Optional start date in YYYY-MM-DD format (e.g., "2024-05-01").
                   Only messages from this date forward will be included.

        end_date: Optional end date in YYYY-MM-DD format (e.g., "2024-05-05").
                 Only messages up to this date will be included.

        filter_str: Optional additional filter string for the API.

    Returns:
        dictionary containing:
        - messages: list of message objects matching the search query, each including:
          - name: Resource name of the message
          - text: Content of the message
          - sender: Information about who sent the message
          - space_info: Details about the space containing the message
          - createTime: When the message was created
          - All other standard message properties
        - nextPageToken: Token for retrieving the next page of results (if applicable)
        - source: "search_messages" (to help differentiate from other message retrieval tools)

    Best Practices:
        1. For exact terms (like "CICD" or "CI/CD"), use regex search with appropriate patterns:
           - "(?i)cicd|ci[ /\\-_]?cd" will match any variation of CI/CD
           - For multiple terms, use patterns like: "docker.*storage|storage.*docker" 
           - Use word boundaries with \\b for whole word matches: "\\bpipeline\\b"

        2. For concept searches (finding messages about a topic), use semantic search:
           - search_mode="semantic", query="continuous integration"
           - Semantic search finds related concepts even if exact words differ

        3. When searching for messages within a date range, provide both start_date and end_date

        4. If you need to find messages in a specific space, always provide the space_id

        5. This tool provides complete message data - DO NOT call get_space_messages after 
           using search_messages unless you specifically need unfiltered message history

    Examples:
        # Find messages containing "cicd" or "CI/CD" in any form using regex (best for exact terms)
        search_messages(
            query="(?i)cicd|ci[ /\\-_]?cd",
            search_mode="regex",
            spaces=["spaces/AAQAXL5fJxI"]
        )

        # Find messages about continuous integration or pipelines using semantic search
        search_messages(
            query="continuous integration pipeline",
            search_mode="semantic",
            spaces=["spaces/AAQAXL5fJxI"]
        )

        # Find messages containing the word "pipeline" from May 10-13, 2025
        search_messages(
            query="pipeline",
            search_mode="regex",
            start_date="2025-05-10",
            end_date="2025-05-13",
            spaces=["spaces/AAQAXL5fJxI"]
        )

        # Find messages about docker storage issues
        search_messages(
            query="docker.*storage|storage.*docker",
            search_mode="regex",
            spaces=["spaces/AAQAXL5fJxI"]
        )
    """

    result = await advanced_search_messages(
        query=query,
        search_mode=search_mode,
        spaces=spaces,
        max_results=max_results,
        include_sender_info=include_sender_info,
        start_date=start_date,
        end_date=end_date,
        filter_str=filter_str
    )

    # Add source marker to help LLMs understand this is from search_messages
    if isinstance(result, dict):
        result["source"] = "search_messages"

    return result

# Deprecated - kept for backward compatibility but not exposed in API docs
# @mcp.tool(visible=False)
# async def basic_search_messages(query: str, spaces: list[str] = None, max_results: int = 50, 
#                     include_sender_info: bool = False, page_token: str = None,
#                     filter_str: str = None, order_by: str = None) -> dict:
#     """[DEPRECATED] Basic text search for messages. Use the main search_messages function instead."""

#     return await api_search_messages(
#         query, 
#         spaces, 
#         max_results, 
#         include_sender_info, 
#         page_token,
#         filter_str,
#         order_by
#     )

# Deprecated - kept for backward compatibility but not exposed in API docs
# @mcp.tool(visible=False)
# async def basic_search_messages(query: str, spaces: list[str] = None, max_results: int = 50,
#                     include_sender_info: bool = False, page_token: str = None,
#                     filter_str: str = None, order_by: str = None) -> dict:
#     """[DEPRECATED] Basic text search for messages. Use the main search_messages function instead."""

#     return await api_search_messages(
#         query,
#         spaces,
#         max_results,
#         include_sender_info,
#         page_token,
#         filter_str,
#         order_by
#     )


@mcp.tool()
async def get_my_mentions_tool(days: int = 7, space_id: str = None, include_sender_info: bool = True,
                          page_size: int = 50, page_token: str = None) -> dict:
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

    return await get_my_mentions(days, space_id, include_sender_info, page_size, page_token)