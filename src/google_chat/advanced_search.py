"""
Advanced Search Integration - Connect SearchManager with Google Chat API
"""
import asyncio
import datetime
import logging
import re
import traceback
from typing import List, Dict, Optional, Any, Tuple
from search_manager import SearchManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("search_integration")

async def advanced_search_messages(
    query: str, 
    search_mode: str = None,  # Changed from "semantic" to None to use config default
    spaces: List[str] = None,
    max_results: int = 50,
    include_sender_info: bool = False,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    filter_str: Optional[str] = None,
) -> Dict:
    """
    Perform advanced search on Google Chat messages using configurable search modes.
    
    This function is the core search implementation used by the MCP tools. It supports multiple
    search modes including regex pattern matching, semantic search, and exact substring matching.
    
    Args:
        query: The search query string. Format depends on the search_mode:
               - For "regex" (default): Regular expression pattern like "ci[ /\\-_]?cd"
               - For "semantic": Natural language description like "continuous integration"
               - For "exact": Simple substring like "meeting notes"
               
               Important notes:
               - Regex searches are case-insensitive by default
               - When using regex special characters like []/()-+*?, escape them with \\
               - For concept searching, use semantic search with descriptive phrases
               
        search_mode: The search strategy to use:
                    - "regex" (DEFAULT): Pattern-based search (e.g., "ci[ /\\-_]?cd|cicd")
                    - "semantic": Meaning-based search (e.g., "continuous integration")
                    - "exact": Simple substring search (e.g., "CI/CD")
                    - "hybrid": Combines multiple search approaches
                    
                    If not specified, uses the default from search_config.yaml (currently "regex").
                    
        spaces: Optional list of space names to search in. Each space name should be in
               the format 'spaces/{space_id}'. If None, searches across all accessible spaces.
               
        max_results: Maximum number of results to return in total (default: 50).
        
        include_sender_info: Whether to include detailed sender information in the results.
        
        start_date: Optional start date in YYYY-MM-DD format (e.g., "2024-05-01")
        
        end_date: Optional end date in YYYY-MM-DD format (e.g., "2024-05-05")
        
        filter_str: Optional additional filter string for the API
        
    Returns:
        Dictionary with search results:
        - messages: List of message objects matching the search query
        - nextPageToken: Token for retrieving the next page of results (if applicable)
    
    Raises:
        ValueError: If date formats are invalid
        Exception: If search operations fail
    
    Examples:
        # Search for "cicd" using regex search in a specific space
        results = await advanced_search_messages(
            query="cicd",
            search_mode="regex",
            spaces=["spaces/AAQAXL5fJxI"]
        )
        
        # Search for messages about continuous integration using semantic search
        results = await advanced_search_messages(
            query="continuous integration",
            search_mode="semantic",
            spaces=["spaces/AAQAXL5fJxI"]
        )
        
        # Search with regex for "CI/CD" in any form (case-insensitive)
        results = await advanced_search_messages(
            query="(?i)ci[ /\\-_]?cd|cicd",
            search_mode="regex",
            spaces=["spaces/AAQAXL5fJxI"]
        )
    """
    from google_chat import search_messages as api_search_messages
    from google_chat import list_space_messages
    
    logger.info(f"Advanced search started: query='{query}', mode={search_mode}, spaces={spaces}")
    
    # Initialize the search manager
    search_manager = SearchManager()
    
    # If mode not specified, use the default from config
    if search_mode is None:
        search_mode = search_manager.get_default_mode()
        logger.info(f"No search mode specified, using default: {search_mode}")
    
    # Log search settings
    logger.info(f"Using search mode: {search_mode}")
    logger.info(f"Max results: {max_results}")
    logger.info(f"Include sender info: {include_sender_info}")
    
    # Create a date-based filter if dates are provided
    date_filter = None
    if start_date:
        try:
            start_datetime = datetime.datetime.strptime(start_date, '%Y-%m-%d').replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            
            if end_date:
                end_datetime = datetime.datetime.strptime(end_date, '%Y-%m-%d').replace(
                    hour=23, minute=59, second=59, microsecond=999999
                )
                date_filter = f"createTime > \"{start_datetime.isoformat()}\" AND createTime < \"{end_datetime.isoformat()}\""
            else:
                # Just one day if only start_date provided
                next_day = start_datetime + datetime.timedelta(days=1)
                date_filter = f"createTime > \"{start_datetime.isoformat()}\" AND createTime < \"{next_day.isoformat()}\""
            
            logger.info(f"Date filter created: {date_filter}")
        except ValueError as e:
            logger.error(f"Invalid date format: start={start_date}, end={end_date}. Error: {str(e)}")
            raise ValueError(f"Invalid date format: {str(e)}")
    
    # Combine with any existing filter
    combined_filter = date_filter
    if filter_str:
        if combined_filter:
            combined_filter = f"{combined_filter} AND {filter_str}"
        else:
            combined_filter = filter_str
            
    logger.info(f"Combined filter: {combined_filter}")
    
    # For exact search only, we can use the API's basic filtering
    if search_mode == "exact":
        # Use the API's built-in search which does basic substring matching
        logger.info("Using API's built-in search (exact mode)")
        try:
            api_result = await api_search_messages(
                query=query,
                spaces=spaces,
                max_results=max_results,
                include_sender_info=include_sender_info,
                filter_str=combined_filter
            )
            logger.info(f"API search completed, found {len(api_result.get('messages', []))} messages")
            return api_result
        except Exception as e:
            logger.error(f"API search failed: {str(e)}")
            logger.info("Falling back to custom search implementation")
            # Continue to custom search implementation below
    
    # For advanced search modes, we need to:
    # 1. Get messages from the API
    # 2. Run them through our search manager
    
    # Get all spaces if none specified
    spaces_to_search = spaces
    if not spaces_to_search:
        try:
            logger.info("No spaces specified, getting all available spaces")
            from google_chat import list_chat_spaces
            spaces_response = await list_chat_spaces()
            spaces_to_search = [space.get("name") for space in spaces_response if space.get("name")]
            logger.info(f"Found {len(spaces_to_search)} spaces to search")
            
            if not spaces_to_search:
                logger.warning("No spaces found to search")
                return {'messages': [], 'nextPageToken': None}
        except Exception as e:
            logger.error(f"Failed to get spaces: {str(e)}")
            return {'messages': [], 'nextPageToken': None, 'error': f"Failed to get spaces: {str(e)}"}
    
    all_messages = []
    
    # Get messages from each space
    for space_name in spaces_to_search:
        try:
            logger.info(f"Fetching messages from space: {space_name}")
            space_messages = await list_space_messages(
                space_name,
                include_sender_info=include_sender_info,
                page_size=max_results,  # Fetch enough to search through
                filter_str=combined_filter
            )
            
            # Add space info to each message
            messages = space_messages.get('messages', [])
            logger.info(f"Received {len(messages)} messages from space {space_name}")
            
            # Log the first few messages to help with debugging
            if messages and len(messages) > 0:
                for i, msg in enumerate(messages[:2]):
                    text = msg.get('text', '')[:100]
                    logger.debug(f"Sample message {i+1}: {text}...")
                    
                    # Explicitly check if the query appears in the text (case insensitive)
                    if search_mode == "regex":
                        try:
                            pattern = re.compile(query, re.IGNORECASE)
                            if text and pattern.search(text):
                                logger.debug(f"✅ Message {i+1} matches regex pattern '{query}'")
                            else:
                                logger.debug(f"❌ Message {i+1} does NOT match regex pattern '{query}'")
                        except re.error:
                            # If regex is invalid, check for simple substring
                            if query.lower() in text.lower():
                                logger.debug(f"✅ Message {i+1} contains substring '{query}'")
                            else:
                                logger.debug(f"❌ Message {i+1} does NOT contain substring '{query}'")
                    else:
                        # For other search modes, just check for substring
                        if query.lower() in text.lower():
                            logger.debug(f"✅ Message {i+1} contains substring '{query}'")
                        else:
                            logger.debug(f"❌ Message {i+1} does NOT contain substring '{query}'")
            
            for msg in messages:
                msg["space_info"] = {"name": space_name}
                
            all_messages.extend(messages)
            
            # Don't fetch too many messages
            if len(all_messages) > max_results * 5:  # Get 5x the needed results for searching
                logger.info(f"Reached message limit ({max_results * 5}), stopping fetch")
                break
                
        except Exception as e:
            logger.error(f"Error fetching messages from space {space_name}: {str(e)}")
            logger.debug(traceback.format_exc())
            continue
    
    logger.info(f"Total messages collected for search: {len(all_messages)}")
    
    if not all_messages:
        logger.warning("No messages found to search")
        return {'messages': [], 'nextPageToken': None}
    
    # Apply advanced search using the search manager
    logger.info(f"Running {search_mode} search on {len(all_messages)} messages")
    try:
        search_results = search_manager.search(query, all_messages, mode=search_mode)
        
        # Format results for API compatibility
        result_messages = [msg for _, msg in search_results[:max_results]]
        logger.info(f"Search complete, found {len(result_messages)} matching messages")
        
        # If regex mode is used, double-check the results with a compiled regex pattern
        # This helps debug any issues with the search implementation
        if search_mode == "regex" and result_messages:
            logger.debug("Verifying regex search results:")
            try:
                pattern = re.compile(query, re.IGNORECASE)
                for i, msg in enumerate(result_messages[:3]):  # Just check first few
                    text = msg.get('text', '')
                    if text and pattern.search(text):
                        logger.debug(f"✅ Result {i+1} correctly matches regex pattern")
                    else:
                        logger.debug(f"❓ Result {i+1} may not match regex pattern - text: {text[:50]}...")
            except re.error:
                logger.debug(f"Cannot verify regex results - invalid pattern '{query}'")
        
        return {
            'messages': result_messages,
            'nextPageToken': None,  # No pagination in this implementation
            'space_info': {'searched_spaces': spaces_to_search} if spaces_to_search else None,
            'search_metadata': {
                'query': query,
                'mode': search_mode,
                'found_count': len(result_messages),
                'searched_count': len(all_messages)
            },
            'search_complete': True  # Signal to LLMs that this is a complete search result
        }
        
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        logger.debug(traceback.format_exc())
        return {
            'messages': [],
            'nextPageToken': None,
            'search_metadata': {'error': str(e)},
            'search_complete': False,
            'error': f"Search failed: {str(e)}"
        }

# Example usage:
# results = await advanced_search_messages(
#     "important meeting notes", 
#     search_mode="hybrid",
#     start_date="2023-01-01", 
#     end_date="2023-12-31"
# ) 