import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.providers.google_chat.api.search import search_messages

# Shared constants
SPACE = "spaces/test"
MSG_OLD = {
    "name": f"{SPACE}/messages/123",
    "text": "Here's the quarterly financial report we discussed",
    "createTime": "2024-05-13T14:30:00Z"
}
MSG_RECENT = {
    "name": f"{SPACE}/messages/456",
    "text": "The latest financial analysis is now available",
    "createTime": "2024-05-20T09:15:00Z"
}


@pytest.mark.asyncio
async def test_date_filter_formatting_and_fallback_with_semantic():
    """
    Test that days_window and offset parameters work correctly and fallback is triggered
    if no results are returned with initial date filtering.
    """
    with patch("src.providers.google_chat.api.search.list_space_messages", new_callable=AsyncMock) as mock_list_messages:
        # First call with days_window=1 and offset=5 returns no messages
        # Second call with expanded date range (days_window=2) returns a message
        mock_list_messages.side_effect = [
            {"messages": []},
            {"messages": [MSG_OLD]},
        ]

        with patch("src.providers.google_chat.api.search.SearchManager") as mock_mgr:
            search_mgr = MagicMock()
            mock_mgr.return_value = search_mgr
            search_mgr.search.return_value = [(0.9, MSG_OLD)]
            search_mgr.get_default_mode.return_value = "semantic"

            result = await search_messages(
                query="financial report",
                search_mode="semantic",
                spaces=[SPACE],
                days_window=1,
                offset=5
            )

        # Verify the first call used the original parameters
        first_call_args = mock_list_messages.call_args_list[0][1]
        assert first_call_args["days_window"] == 1
        assert first_call_args["offset"] == 5
        
        # Verify the second call used an expanded date window
        second_call_args = mock_list_messages.call_args_list[1][1]
        assert second_call_args["days_window"] == 2  # Double the original
        assert second_call_args["offset"] == 5  # Same offset
        
        # Verify result has the message
        assert len(result["messages"]) == 1
        assert result["messages"][0]["name"] == MSG_OLD["name"]
        assert mock_list_messages.call_count == 2


@pytest.mark.asyncio
async def test_returns_results_within_date_range_with_semantic():
    """Test that messages within the date range are returned correctly."""
    with patch("src.providers.google_chat.api.search.list_space_messages", new_callable=AsyncMock) as mock_list_messages:
        mock_list_messages.return_value = {"messages": [MSG_RECENT]}

        with patch("src.providers.google_chat.api.search.SearchManager") as mock_mgr:
            search_mgr = MagicMock()
            mock_mgr.return_value = search_mgr
            search_mgr.search.return_value = [(0.92, MSG_RECENT)]
            search_mgr.get_default_mode.return_value = "semantic"

            result = await search_messages(
                query="financial analysis",
                search_mode="semantic",
                spaces=[SPACE],
                days_window=7
            )

        assert len(result["messages"]) == 1
        assert result["messages"][0]["name"] == MSG_RECENT["name"]
        assert mock_list_messages.call_count == 1


@pytest.mark.asyncio
async def test_falls_back_when_no_date_results_with_semantic():
    """
    If no messages are found with the date filter, search should retry without it.
    """
    with patch("src.providers.google_chat.api.search.list_space_messages", new_callable=AsyncMock) as mock_list_messages:
        mock_list_messages.side_effect = [
            {"messages": []},
            {"messages": [MSG_OLD]}
        ]

        with patch("src.providers.google_chat.api.search.SearchManager") as mock_mgr:
            search_mgr = MagicMock()
            mock_mgr.return_value = search_mgr
            search_mgr.search.return_value = [(0.95, MSG_OLD)]
            search_mgr.get_default_mode.return_value = "semantic"

            result = await search_messages(
                query="financial report",
                search_mode="semantic",
                spaces=[SPACE],
                days_window=7
            )

        assert len(result["messages"]) == 1
        assert result["messages"][0]["name"] == MSG_OLD["name"]
        assert mock_list_messages.call_count == 2


@pytest.mark.asyncio
async def test_regex_enforces_strict_date_filtering():
    """
    Regex search should not fall back and must strictly enforce date filters.
    """
    with patch("src.providers.google_chat.api.search.list_space_messages", new_callable=AsyncMock) as mock_list_messages:
        mock_list_messages.return_value = {"messages": []}

        with patch("src.providers.google_chat.api.search.SearchManager") as mock_mgr:
            search_mgr = MagicMock()
            mock_mgr.return_value = search_mgr
            search_mgr.get_default_mode.return_value = "regex"

            result = await search_messages(
                query="budget",
                search_mode="regex",
                spaces=[SPACE],
                days_window=7
            )

        assert len(result["messages"]) == 0
        assert mock_list_messages.call_count == 1
        search_mgr.search.assert_not_called()
