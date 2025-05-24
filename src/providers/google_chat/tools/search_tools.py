import logging

from src.providers.google_chat.api.search import search_messages
from src.providers.google_chat.api.summary import get_my_mentions
from src.mcp_instance import mcp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@mcp.tool()
async def search_messages_tool(query: str,
                          search_mode: str = None,
                          spaces: list[str] = None,
                          max_results: int = 50,
                          include_sender_info: bool = False,
                          filter_str: str = None,
                          days_window: int = 3,
                          offset: int = 0) -> dict:
    """Search for messages across all spaces or specified spaces.

    This tool performs advanced search for messages in Google Chat spaces using various search strategies.
    It's the primary tool for finding specific content in conversations by supporting multiple search modes
    including regex pattern matching, semantic search, and exact substring matching.

    Args:
        query: The search query string. Format varies by search_mode:

            ▶ For "regex" search (DEFAULT mode):
              - Use regular expression patterns
              - Case-insensitive by default
              - Examples:
                - "meeting notes" → Matches "meeting notes", "Meeting Notes", etc.
                - "(?i)cicd|ci[ /\\-_]?cd" → Matches any variation of CI/CD
                - "\\bpipeline\\b" → Matches "pipeline" as a whole word only
                - "docker.*storage|storage.*docker" → Finds messages with both terms in any order
                - "term1|term2|term3|term4|term5" → More effective than space-separated terms,
                  as it will match any message containing at least one of these terms
                - "error.{0,20}\\b(500|503|404)\\b" → Finds error messages with specific HTTP codes
              - Advanced patterns:
                - "\\bimportant\\b.*\\bdeadline" → Finds "important" followed by "deadline"
                - "release.{0,50}version.{0,10}[0-9\\.]+" → Finds version numbers in release discussions
                - "(?i)(blocker|urgent|critical).{0,30}(fix|resolve|solve)" → Priority issues being fixed

            ▶ For "semantic" search:
              - Natural language queries that match by meaning, not exact words
              - Uses embeddings to find conceptually similar messages
              - MUCH more flexible than regex or exact matching
              - Examples:
                - "continuous integration pipeline" → Can find messages about:
                  * "Jenkins builds are failing"
                  * "We need to fix the GitHub Actions workflow"
                  * "The automated tests in our CI system are slow"
                  * "I'm setting up the deployment pipeline"
                  (even when they don't contain "continuous integration" explicitly)

                - "performance issues" → Will find messages discussing:
                  * "The system is very slow when loading large files"
                  * "Users are experiencing lag in the dashboard"
                  * "We need to optimize the database queries"
                  * "Response times have degraded since the last release"

                - "quarterly financial review" → Will match messages like:
                  * "Here's the Q1 financial summary we discussed"
                  * "The budget numbers for this quarter look good"
                  * "We need to prepare the financial analysis for the board"

            ▶ For "exact" search:
              - Simple substring matching (fastest but least flexible)
              - Examples:
                - "budget" → Only finds exact occurrences of "budget" (case-sensitive)

            SEARCH MODE COMPARISON AND BEST PRACTICES:

            1. REGEX SEARCH (Default)
               Advantages:
               - Fastest search method
               - Precise pattern matching with wildcards and special characters
               - Good for finding specific text patterns or formats
               Best for: Technical terms, identifiers, predictable text patterns

            2. SEMANTIC SEARCH
               Advantages:
               - Finds conceptually related content without exact word matches
               - Works well with natural language descriptions
               - Flexible date filtering with automatic fallback
               - Best at understanding the meaning behind your query
               Best for: Concept-based searches, troubleshooting, finding related information

            3. EXACT SEARCH
               Advantages:
               - Simple substring matching
               - No special characters to escape
               - Most straightforward to use
               Best for: Precise text snippets when you know exactly what to find

            WHEN TO USE EACH MODE:
            - Use REGEX for: Technical terms with specific formats (CI/CD, v1.2.3)
            - Use SEMANTIC for: Concept-based searches, troubleshooting, finding related content
            - Use EXACT for: Finding exact literal strings without pattern matching

        search_mode: The search strategy to use. One of:
                   - "regex": Pattern matching with regular expressions (DEFAULT)
                   - "semantic": Meaning-based search using embeddings
                   - "exact": Simple substring search
                   - "hybrid": Combines multiple search approaches

                   If not specified, "regex" is used as the default mode.

        spaces: Optional list of space names to search in. Format: ["spaces/{space_id}", ...]
              If None, searches across all accessible spaces.

        max_results: Maximum number of results to return (default: 50).

        include_sender_info: When True, adds email, display name, and profile photo
                          information for message senders (default: False).

        filter_str: Optional additional filter string for the API in Google Chat API filter format.
                   See API reference for advanced filtering options.

        days_window: Number of days to look back for messages (default: 3).
                   This parameter controls the date range for message retrieval.
                   For example, if days_window=3, messages from the last 3 days will be retrieved.
                   If no results are found in the initial date range, the system will 
                   automatically try with an expanded date range (double the window size)
                   before falling back to other strategies.
                   
                   INCREMENTAL SEARCH STRATEGY:
                   To effectively search through historical messages in chunks:
                   1. Start with small window (days_window=3, offset=0) for recent messages
                   2. If needed, move backward in time by increasing offset while keeping window consistent:
                      - First search: days_window=3, offset=0 (0-3 days ago)
                      - Second search: days_window=3, offset=3 (3-6 days ago)
                      - Third search: days_window=3, offset=6 (6-9 days ago)
                   3. For broader searches, increase the window size:
                      - days_window=7, offset=0 (0-7 days ago)
                      - days_window=7, offset=7 (7-14 days ago)
                      - days_window=7, offset=14 (14-21 days ago)
                   4. For targeted searches of specific time periods:
                      - days_window=1, offset=30 (messages from exactly 30 days ago)

        offset: Number of days to offset the end date from today (default: 0).
               For example, if offset=3, the end date will be 3 days before today,
               and with days_window=3, messages from 6 to 3 days ago will be retrieved.
               
               OFFSET EXPLAINED:
               - offset=0: End date is today (search includes most recent messages)
               - offset=7: End date is 7 days ago (search excludes the last 7 days of messages)
               - Combining with days_window creates a sliding window through message history
               - Useful for methodical searching without duplicate results

                   IMPORTANT DATE FILTERING NOTES:
                   1. Messages are ALWAYS returned in descending order by creation time 
                      (newest first), matching the natural way users read chat history.

                   2. The date range is calculated as follows:
                      - end_date = current_date - offset
                      - start_date = end_date - days_window

                   3. For semantic search, date filters are treated as PREFERENCES rather
                      than strict requirements. This special behavior is UNIQUE to semantic search
                      and works as follows:

                      a) System FIRST tries to find messages matching both:
                         - Semantically relevant to your query
                         - Within the specified date range

                      b) If NO messages match both criteria, system does automatic fallback:
                         - First tries with expanded date range (double the window size)
                         - If still no results, tries with a much larger window (10x)
                         - Best semantic matches are returned regardless of date

                      c) This happens automatically and transparently to the user

                      STEP-BY-STEP EXAMPLE:
                      User searches for "project updates" with:
                        - search_mode="semantic"
                        - days_window=3
                        - offset=0

                      Available messages:
                        - 5 days ago: "Here's the current status of Project X: 75% complete"
                        - 2 days ago: "Team lunch scheduled for Friday"

                      Search process:
                        1. Look for semantically relevant messages from the last 3 days
                           → Found nothing (2-day-old message is in range but not relevant)
                        2. Try with expanded date range (6 days)
                           → Found the 5-day-old message because it's semantically relevant
                        3. If still nothing, would try with a much larger window (30 days)

                      This ensures users always get useful results, even when strict
                      date filtering would return nothing.

                   4. For regex and exact searches, date filters are applied strictly.
                      These modes will return NO results if no messages match both the
                      query and the date filter.

    Returns:
        dictionary containing:
        - messages: list of message objects matching the search query
        - nextPageToken: token for retrieving the next page of results (if applicable)
        - source: "search_messages" (to identify the source of the response)
        - space_info: information about the spaces that were searched
        - search_metadata: details about the search query and results
        - search_complete: boolean indicating whether the search is complete
        - message_count: number of messages returned (integer)

    Note: For optimal results with semantic search, use descriptive natural language
    queries rather than short keywords.

    Usage Examples:

    1. Basic regex search in a specific space:
       ```python
       search_messages_tool(
           query="meeting",
           spaces=["spaces/AAQAXL5fJxI"]
       )
       ```

    2. Find messages about continuous integration using semantic search:
       ```python
       search_messages_tool(
           query="continuous integration pipeline",
           search_mode="semantic",
           spaces=["spaces/AAQAXL5fJxI"],
           include_sender_info=True
       )
       ```

    3. Find messages containing "budget" from the last 30 days:
       ```python
       search_messages_tool(
           query="budget",
           search_mode="regex",
           days_window=30,
           spaces=["spaces/AAQAXL5fJxI"]
       )
       ```

    4. Find all messages from 7-14 days ago:
       ```python
       search_messages_tool(
           query=".*",  # Match anything (regex mode)
           days_window=7,
           offset=7,  # Start from 7 days ago
           spaces=["spaces/AAQAXL5fJxI"]
       )
       ```

    5. Semantic search with flexible date filtering:
       ```python
       search_messages_tool(
           query="quarterly report discussion",
           search_mode="semantic",
           days_window=7  # Look back 7 days initially
       )
       ```
       This example will try to find messages about quarterly reports from the last 7 days,
       but if none exist in that timeframe, it will try with expanded date ranges rather
       than returning no results.

    6. Sequential searches without message duplication:
       ```python
       # First search - last 3 days
       results_first = search_messages_tool(
           query="project updates",
           days_window=3,
           offset=0
       )
       
       # Second search - previous 3 days (days 3-6)
       results_second = search_messages_tool(
           query="project updates",
           days_window=3,
           offset=3
       )
       ```

    7. Search with regex OR patterns for more effective term matching:
       ```python
       search_messages_tool(
           query="issue|bug|problem|error|failure",
           search_mode="regex",
           days_window=14,  # Last two weeks
           spaces=["spaces/AAQAXL5fJxI"]
       )
       ```
       This pattern will find messages containing any of these related terms, which is 
       more effective than using space-separated terms that would require all terms to match.

    8. Incremental time-based searching pattern:
       ```python
       # Start with recent messages (last 3 days)
       recent_results = search_messages_tool(
           query="deployment issues",
           days_window=3,
           offset=0
       )
       
       # If not found, check next time chunk (3-6 days ago)
       if len(recent_results.get("messages", [])) == 0:
           older_results = search_messages_tool(
               query="deployment issues",
               days_window=3,
               offset=3
           )
       
       # Continue searching further back if needed (6-9 days ago)
       if len(older_results.get("messages", [])) == 0:
           oldest_results = search_messages_tool(
               query="deployment issues",
               days_window=3,
               offset=6
           )
       ```
       This pattern allows methodically searching back in time without missing messages.
       
    9. Combining regex searches with word boundaries:
       ```python
       search_messages_tool(
           query=r"\berror\b.{0,50}\bfailed\b",
           search_mode="regex",
           days_window=7
       )
       ```
       This will find messages where "error" and "failed" appear within 50 characters of each other,
       but only when they're complete words (not parts of other words).
       
    10. Finding messages with exact phrases that might have contraction variants:
        ```python
        search_messages_tool(
            query="don't understand|didn't understand|do not understand|did not understand",
            search_mode="regex"
        )
        ```
        This handles different ways people might phrase the same concept with contractions.
        
    11. Comparing OR operator (|) vs space-separated terms:
        ```python
        # More effective: Using the OR operator to match any of these terms
        search_messages_tool(
            query="report|update|status|progress",
            search_mode="regex"
        )
        
        # Less effective: This would try to match all terms in a single message
        search_messages_tool(
            query="report update status progress",
            search_mode="regex"
        )
        ```
        The first query will find any message containing at least one of these terms,
        while the second would only match messages containing all of these terms together.
    """
    logger.info(f"Searching for messages: query='{query}', mode={search_mode}")
    logger.info(f"Starting advanced search with: query='{query}', mode={search_mode}, spaces={spaces}")

    # Search messages across spaces
    result = await search_messages(
        query,
        search_mode,
        spaces,
        max_results,
        include_sender_info,
        filter_str,
        days_window,
        offset
    )
    
    # Add message count if not already present
    if "message_count" not in result:
        result["message_count"] = len(result.get("messages", []))

    return result


@mcp.tool()
async def get_my_mentions_tool(days: int = 7, space_id: str = None, include_sender_info: bool = True,
                          page_size: int = 50, page_token: str = None, offset: int = 0) -> dict:
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
              
              USAGE STRATEGY:
              - For recent mentions: days=1 or days=3
              - For weekly review: days=7
              - For monthly review: days=30
              
              PERFORMANCE NOTE: Lower values (fewer days) result in faster searches.
              
        space_id: Optional space ID to check for mentions in a specific space.
                 If provided, searches only this space. If null (default), searches all accessible spaces.
                 Can be either a full resource name (e.g., 'spaces/AAQAtjsc9v4') or just the ID portion.
                 
                 USAGE STRATEGY:
                 - For targeted searches, provide specific space_id
                 - For broad searches across all conversations, leave as null
                 - Searching a specific space is significantly faster than searching all spaces
              
        include_sender_info: Whether to include detailed sender information in the returned messages.
                            When true, each message will include a sender_info object with details
                            like email, display_name, and profile_photo. (default: True)
                            
                            Set to False if you only need message content and not sender details.
                            
        page_size: Maximum number of messages to return per space (default: 50)
                  Only applies when space_id is provided; otherwise, all matching mentions are returned.
                  
                  NOTE: Increasing this value may impact performance but ensures more comprehensive results.
                  
        page_token: Optional page token for pagination (only applicable when space_id is provided)
                   Use the nextPageToken from a previous response to get the next page of results.
                   
                   This allows retrieving messages beyond the initial page_size limit.
                   
        offset: Number of days to offset the end date from today (default: 0).
               For example, if offset=3, the search will exclude mentions from the last 3 days.
               
               USAGE STRATEGY:
               - For current mentions: offset=0 (default)
               - To exclude recent mentions: offset=3 (excludes last 3 days)
               - To check older time periods: combine with days parameter
                 - Last week, excluding today: offset=1, days=7
                 - Previous week only: offset=7, days=7
               
               This parameter helps you perform non-overlapping sequential searches.

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
        - message_count: Number of messages returned (integer)

    Examples:
    
    1. Basic usage - get all mentions from the past week:
       ```python
       get_my_mentions_tool()
       ```
       
    2. Check for recent mentions (last 24 hours):
       ```python
       get_my_mentions_tool(days=1)
       ```
       
    3. Check for mentions in a specific space:
       ```python
       get_my_mentions_tool(
           space_id="spaces/AAQAtjsc9v4",
           days=3
       )
       ```
       
    4. Check for mentions from previous week (not including current week):
       ```python
       get_my_mentions_tool(
           offset=7,  # Skip the last 7 days
           days=7     # Look at the 7 days before that
       )
       ```
       
    5. Sequential non-overlapping searches for methodical review:
       ```python
       # First check last 3 days
       recent_mentions = get_my_mentions_tool(days=3, offset=0)
       
       # Then check days 4-7
       older_mentions = get_my_mentions_tool(days=4, offset=3)
       
       # Then check days 8-14
       oldest_mentions = get_my_mentions_tool(days=7, offset=7)
       ```
    """
    logger.info(f"Finding mentions in the last {days} days (offset: {offset} days)")
    
    # Get mentions from all spaces or single space
    result = await get_my_mentions(
        days=days,
        space_id=space_id,
        include_sender_info=include_sender_info,
        page_size=page_size,
        page_token=page_token,
        offset=offset
    )
    
    # Add message count if not already present
    if "message_count" not in result:
        result["message_count"] = len(result.get("messages", []))

    return result
