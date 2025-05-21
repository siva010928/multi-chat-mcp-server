"""
Search Integration - Connect SearchManager with Google Chat API
"""
import logging
from typing import Optional

from src.providers.google_chat.api.messages import list_space_messages
from src.providers.google_chat.api.spaces import list_chat_spaces
from src.providers.google_chat.utils import create_date_filter
from src.providers.google_chat.utils.constants import SEARCH_CONFIG_YAML_PATH
from src.providers.google_chat.utils.search_manager import SearchManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("search_integration")

async def search_messages(
    query: str,
    search_mode: str = None,
    spaces: list[str] = None,
    max_results: int = 50,
    include_sender_info: bool = False,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    filter_str: Optional[str] = None,
) -> dict:
    logger.info(f"search started: query='{query}', mode={search_mode}, spaces={spaces}")

    # Initialize search manager
    search_manager = SearchManager(config_path=SEARCH_CONFIG_YAML_PATH)

    # Determine search mode
    if not search_mode:
        search_mode = search_manager.get_default_mode()
    logger.info(f"Using search mode: {search_mode}")

    # Build date filter
    date_filter = None
    if start_date:
        try:
            date_filter = create_date_filter(start_date, end_date)
        except ValueError as e:
            raise ValueError(f"Invalid date format: {str(e)}")

    # Combine filters
    combined_filter = f"{filter_str} AND ({date_filter})" if filter_str and date_filter else (date_filter or filter_str)

    # Get spaces
    spaces_to_search = spaces
    if not spaces_to_search:
        space_objs = await list_chat_spaces()
        spaces_to_search = [s.get("name") for s in space_objs if s.get("name")]

    all_messages = []

    for space_name in spaces_to_search:
        try:
            result = await list_space_messages(
                space_name,
                start_date=start_date,
                end_date=end_date,
                include_sender_info=include_sender_info,
                page_size=max_results,
                filter_str=combined_filter
            )

            messages = result.get("messages", [])
            if not messages and search_mode == "semantic" and start_date:
                # fallback retry without date filter for semantic only
                logger.info(f"Semantic fallback: retrying {space_name} without date filter")
                result = await list_space_messages(
                    space_name,
                    include_sender_info=include_sender_info,
                    page_size=max_results,
                    filter_str=filter_str
                )
                messages = result.get("messages", [])

            for msg in messages:
                msg["space_info"] = {"name": space_name}
            all_messages.extend(messages)

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
                "searched_count": 0
            },
            "search_complete": True,
            "source": "search_messages"
        }

    logger.info(f"Applying {search_mode} search to {len(all_messages)} messages")
    results = search_manager.search(query, all_messages, mode=search_mode)

    final_messages = [msg for _, msg in results[:max_results]]

    return {
        "messages": final_messages,
        "nextPageToken": None,
        "space_info": {"searched_spaces": spaces_to_search},
        "search_metadata": {
            "query": query,
            "mode": search_mode,
            "found_count": len(final_messages),
            "searched_count": len(all_messages)
        },
        "search_complete": True
    }


# Example usage:
# results = await search_messages(
#     "important meeting notes",
#     search_mode="hybrid",
#     start_date="2023-01-01",
#     end_date="2023-12-31"
# )
# print(results)