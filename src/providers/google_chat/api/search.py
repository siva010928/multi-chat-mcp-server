"""
Search Integration - Connect SearchManager with Google Chat API
"""
import datetime
import logging
from typing import Optional, Tuple

from src.providers.google_chat.api.messages import list_space_messages
from src.providers.google_chat.api.spaces import list_chat_spaces
from src.providers.google_chat.utils.constants import SEARCH_CONFIG_YAML_PATH
from src.providers.google_chat.utils.search_manager import SearchManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("search_integration")

def calculate_date_range(days_window: int = 3) -> Tuple[str, str]:
    """
    Calculate a date range for the last X days.

    Args:
        days_window: Number of days to look back (default: 3)

    Returns:
        Tuple of (end_date, start_date) in YYYY-MM-DD format
    """
    today = datetime.datetime.now(datetime.timezone.utc)
    end_date = today.strftime("%Y-%m-%d")

    start_date = (today - datetime.timedelta(days=days_window)).strftime("%Y-%m-%d")

    return end_date, start_date

async def search_messages(
    query: str,
    search_mode: str = None,
    spaces: list[str] = None,
    max_results: int = 50,
    include_sender_info: bool = False,
    filter_str: Optional[str] = None,
    days_window: int = 3,
    offset: int = 0,
) -> dict:
    logger.info(f"search started: query='{query}', mode={search_mode}, spaces={spaces}")

    # Initialize search manager
    search_manager = SearchManager(config_path=SEARCH_CONFIG_YAML_PATH)

    # Determine search mode
    if not search_mode:
        search_mode = search_manager.get_default_mode()
    logger.info(f"Using search mode: {search_mode}")

    # Get spaces
    spaces_to_search = spaces
    if not spaces_to_search:
        space_objs = await list_chat_spaces()
        spaces_to_search = [s.get("name") for s in space_objs if s.get("name")]

    all_messages = []
    original_days_window = days_window
    used_days_window = days_window  # Track the actual window used for the response

    for space_name in spaces_to_search:
        try:
            # Use a much larger page_size to get as many messages as possible in one request
            # Google Chat API typically limits to 1000 messages per request
            large_page_size = 1000
            
            # Initial search with original days_window and offset
            current_days_window = original_days_window
            result = await list_space_messages(
                space_name,
                include_sender_info=include_sender_info,
                page_size=large_page_size,  # Use large page size to get all messages  
                filter_str=filter_str,
                order_by="createTime desc",  # Always use descending order by default
                days_window=current_days_window,
                offset=offset
            )

            messages = result.get("messages", [])
            logger.info(f"Retrieved {len(messages)} messages from {space_name} (window: {current_days_window} days, offset: {offset})")

            # If no messages found and we're using semantic search, try fallback strategies
            if not messages and search_mode == "semantic":
                # First fallback: Try with expanded date range (double the window)
                current_days_window = original_days_window * 2
                used_days_window = current_days_window  # Update the used window
                logger.info(f"No messages found. Trying expanded date range (last {current_days_window} days)")

                result = await list_space_messages(
                    space_name,
                    include_sender_info=include_sender_info,
                    page_size=large_page_size,  # Use large page size
                    filter_str=filter_str,
                    order_by="createTime desc",
                    days_window=current_days_window,
                    offset=offset  # Keep the same offset
                )
                messages = result.get("messages", [])
                logger.info(f"Expanded date range result: found {len(messages)} messages")

                # Second fallback: For semantic search, try with a much larger window
                if not messages and search_mode == "semantic":
                    current_days_window = original_days_window * 10
                    used_days_window = current_days_window  # Update the used window
                    logger.info(f"Semantic fallback: retrying {space_name} with a much larger window ({current_days_window} days)")
                    
                    result = await list_space_messages(
                        space_name,
                        include_sender_info=include_sender_info,
                        page_size=large_page_size,  # Use large page size
                        filter_str=filter_str,
                        order_by="createTime desc",
                        days_window=current_days_window,
                        offset=0  # Reset offset for semantic fallback
                    )
                    messages = result.get("messages", [])
                    logger.info(f"Semantic fallback result: found {len(messages)} messages")

            # Add space information to messages
            for msg in messages:
                msg["space_info"] = {"name": space_name}
            
            # Only collect the initial set of messages
            all_messages.extend(messages)

            # Handle pagination - fetch ALL messages in the time window
            next_page_token = result.get("nextPageToken")
            page_count = 1
            max_pages = 10  # Increased max pages to ensure we get all messages within the time window
            
            # Fetch all remaining pages as long as there's a next_page_token
            while next_page_token and page_count < max_pages:
                page_count += 1
                logger.info(f"Fetching next page of messages (page {page_count})")
                
                # Get next page of messages
                next_page = await list_space_messages(
                    space_name,
                    include_sender_info=include_sender_info,
                    page_size=large_page_size,
                    page_token=next_page_token,
                    order_by="createTime desc",
                    days_window=current_days_window,
                    offset=offset
                )
                
                next_page_messages = next_page.get("messages", [])
                next_page_token = next_page.get("nextPageToken")
                
                # Add space information to messages
                for msg in next_page_messages:
                    msg["space_info"] = {"name": space_name}
                
                all_messages.extend(next_page_messages)
                logger.info(f"Added {len(next_page_messages)} messages from page {page_count}. Total: {len(all_messages)}")
                
                # If we have no more messages to fetch, break the loop
                if not next_page_token or not next_page_messages:
                    break

        except Exception as e:
            logger.warning(f"Error fetching messages from {space_name}: {str(e)}")
            continue

    if not all_messages:
        return {
            "messages": [],
            "nextPageToken": None,
            "space_info": {"searched_spaces": spaces_to_search},
            "search_metadata": {
                "query": query,
                "mode": search_mode,
                "found_count": 0,
                "searched_count": 0,
                "days_window_used": used_days_window
            },
            "search_complete": True,
            "source": "search_messages"
        }

    # Now apply the actual search filtering based on the chosen search mode
    logger.info(f"Applying {search_mode} search to {len(all_messages)} messages")
    results = search_manager.search(query, all_messages, mode=search_mode)

    # Only limit the final results returned to the user, not the messages we search through
    final_messages = [msg for _, msg in results[:max_results]]
    
    # Ensure messages are sorted by createTime in descending order (newest first)
    # This ensures consistent ordering regardless of how the search manager sorted by relevance
    final_messages.sort(key=lambda msg: msg.get("createTime", ""), reverse=True)

    return {
        "messages": final_messages,
        "nextPageToken": None,
        "space_info": {"searched_spaces": spaces_to_search},
        "search_metadata": {
            "query": query,
            "mode": search_mode,
            "found_count": len(final_messages),
            "searched_count": len(all_messages),
            "days_window_used": used_days_window
        },
        "search_complete": True,
        "source": "search_messages",
        "message_count": len(final_messages)
    }


# Example usage:
# results = await search_messages(
#     "important meeting notes",
#     search_mode="hybrid",
#     start_date="2023-01-01",
#     end_date="2023-12-31"
# )
# print(results)
