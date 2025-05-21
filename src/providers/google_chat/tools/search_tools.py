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
                          start_date: str = None,
                          end_date: str = None,
                          filter_str: str = None) -> dict:
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

        start_date: Optional start date in YYYY-MM-DD format (e.g., "2024-05-01").
                    Used to filter messages by creation date. When provided:
                    
                    - All messages AFTER this date will be included
                    - For any search_mode (regex, semantic, etc.)
                    - Creates a filter like: 'createTime > "2024-05-01T00:00:00Z"'
                    
                    IMPORTANT DATE FILTERING NOTES:
                    1. The Google Chat API uses ">" (greater than) for date filtering,
                       NOT ">=" (greater than or equal to), which means messages created
                       exactly at midnight on the start date might be excluded.
                    
                    2. When using start_date alone (without end_date), 
                       the system returns ALL messages AFTER the start date.
                    
                    3. For semantic search, date filters are treated as PREFERENCES rather
                       than strict requirements. This special behavior is UNIQUE to semantic search
                       and works as follows:
                       
                       a) System FIRST tries to find messages matching both:
                          - Semantically relevant to your query
                          - Within the specified date range
                       
                       b) If NO messages match both criteria, system does automatic fallback:
                          - Date filter is completely ignored
                          - All messages are searched for semantic relevance
                          - Best semantic matches are returned regardless of date
                          
                       c) This happens automatically and transparently to the user
                       
                       STEP-BY-STEP EXAMPLE:
                       User searches for "project updates" with:
                         - search_mode="semantic"
                         - start_date="2024-05-18"
                         
                       Available messages:
                         - May 15: "Here's the current status of Project X: 75% complete"
                         - May 20: "Team lunch scheduled for Friday"
                         
                       Search process:
                         1. Look for semantically relevant messages from May 18 onward
                            → Found nothing (May 20 message is in range but not relevant)
                         2. Fallback: Ignore date filter and search all messages
                            → Return the May 15 message because it's semantically relevant
                            
                       This ensures users always get useful results, even when strict
                       date filtering would return nothing.
                       
                    4. For regex and exact searches, date filters are applied strictly.
                       These modes will return NO results if no messages match both the
                       query and the date filter.
                       
                    5. For future dates (like "2025-05-01"), searches will return empty
                       results until messages exist for that timeframe.
        
        end_date: Optional end date in YYYY-MM-DD format (e.g., "2024-05-05").
                  Used to filter messages by creation date. When provided
                  with start_date, creates a date range filter.
                  
                  - All messages BEFORE this date will be included
                  - Creates a filter like: 'createTime < "2024-05-05T23:59:59Z"'
                  
                  When both start_date and end_date are provided, only messages within
                  that time range will be returned (for regex and exact searches).
                  For semantic search, messages outside this range might be returned
                  if no messages within the range match semantically.

        filter_str: Optional additional filter string for the API in Google Chat API filter format.
                   See API reference for advanced filtering options.

    Returns:
        dictionary containing:
        - messages: list of message objects matching the search query
        - nextPageToken: token for retrieving the next page of results (if applicable)
        - source: "search_messages" (to identify the source of the response)
        - space_info: information about the spaces that were searched
        - search_metadata: details about the search query and results
        - search_complete: boolean indicating whether the search is complete

    Note: For optimal results with semantic search, use descriptive natural language
    queries rather than short keywords.

    Usage Examples:

    1. Basic regex search in a specific space:
       ```python
       search_messages(
           query="meeting",
           spaces=["spaces/AAQAXL5fJxI"]
       )
       ```

    2. Find messages about continuous integration using semantic search:
       ```python
       search_messages(
           query="continuous integration pipeline",
           search_mode="semantic",
           spaces=["spaces/AAQAXL5fJxI"],
           include_sender_info=True
       )
       ```

    3. Find messages containing "budget" from the month of May 2024:
       ```python
       search_messages(
           query="budget",
           search_mode="regex",
           start_date="2024-05-01",
           end_date="2024-05-31",
           spaces=["spaces/AAQAXL5fJxI"]
       )
       ```
       
    4. Find all messages after a specific date:
       ```python
       search_messages(
           query=".*",  # Match anything (regex mode)
           start_date="2024-05-18",  # All messages after this date
           spaces=["spaces/AAQAXL5fJxI"]
       )
       ```
       
           5. Semantic search with flexible date filtering:
       ```python
       search_messages(
           query="quarterly report discussion",
           search_mode="semantic",
           start_date="2024-05-13",  # Prefer messages after this date
           spaces=["spaces/AAQAXL5fJxI"]
       )
       ```
       This example will try to find messages about quarterly reports after May 13,
       but if none exist in that timeframe, it will return semantically relevant
       messages from before May 13 rather than returning no results.
       
       IMPORTANT: How semantic search works with date filters (unlike regex/exact):
       
       ```
       Example Scenario:
       
       Timeline:     May 10               May 13               May 15               May 20
                       |                    |                    |                    |
       Messages:  [Q1 Report]               |                [Team Meeting]     [Project Update]
                       |                    |                    |                    |
                       |<---Filter excludes-|---------Filter includes---------------->|
                       |                    |                    |                    |
       ```
       
       If you search for "quarterly financial results" with start_date="2024-05-13":
       
       - First attempt: Look for semantically matching messages after May 13
         - Found: None (the only relevant message is from May 10)
       
       - Fallback behavior: The system will IGNORE the date filter completely
         - Will return: [Q1 Report] from May 10 because it's semantically relevant
       
       - Irrelevant messages like [Team Meeting] and [Project Update] won't be returned
         even though they're within the date range, because they're not semantically relevant
       
       This prioritizes finding RELEVANT content over strict date adherence.
    
           6. Advanced regex search with word boundaries:
       ```python
       search_messages(
           query="\\bplan\\b.*\\bmeeting\\b",  # Find messages with words "plan" and "meeting"
           search_mode="regex",
           start_date="2024-06-01",
           end_date="2024-06-30"
       )
       ```
       This will strictly find only messages with both "plan" and "meeting" as whole words,
       created in June 2024, and will return no results if no messages match both criteria.
       
       7. Real-world semantic search for troubleshooting:
       ```python
       search_messages(
           query="users experiencing slow performance on the application dashboard",
           search_mode="semantic",
           start_date="2024-05-01"  # Try to find recent issues first
       )
       ```
       This detailed query could find messages like:
       - "We've received reports of dashboard timeouts"
       - "The visualization widgets are taking forever to load"
       - "Database queries for the admin panel are inefficient"
       - "Users are complaining about lag when viewing reports"
       
       Even if these messages are from April (before the start_date), they'll be
       returned if no relevant messages exist after May 1st. This makes semantic
       search extremely powerful for finding information when you don't know the 
       exact wording or timing of messages.
    """
    logger.info(f"Searching for messages: query='{query}', mode={search_mode}")
    
    try:
        # Normalize and prepare the query
        query = query.strip()
        if not query:
            logger.error("Empty query received")
            return {
                'messages': [],
                'search_metadata': {'error': 'Empty query'},
                'search_complete': False
            }
            
        # Validate mode
        valid_modes = ["semantic", "regex", "exact", "hybrid", None]
        if search_mode not in valid_modes:
            logger.warning(f"Invalid search mode '{search_mode}', using default")
            search_mode = None
        
        logger.info(f"Starting advanced search with: query='{query}', mode={search_mode}, spaces={spaces}")
        
        results = await search_messages(
            query=query,
            search_mode=search_mode,
            spaces=spaces,
            max_results=max_results,
            include_sender_info=include_sender_info,
            start_date=start_date,
            end_date=end_date,
            filter_str=filter_str
        )
        
        logger.info(f"Search complete, found {len(results.get('messages', []))} messages")
        return results
    except Exception as e:
        logger.error(f"Error in search_messages_tool: {str(e)}", exc_info=True)
        return {
            'messages': [],
            'error': f"Search failed: {str(e)}",
            'search_complete': False
        }


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