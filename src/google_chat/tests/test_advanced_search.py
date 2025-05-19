import pytest
from unittest.mock import patch, AsyncMock
import datetime

from src.google_chat.advanced_search import advanced_search_messages


@pytest.mark.asyncio
async def test_advanced_search_date_filter_formatting():
    """Test that advanced_search correctly formats date filters with quotes."""
    
    # Mock list_space_messages and create_date_filter
    with patch("src.google_chat.advanced_search.list_space_messages", new_callable=AsyncMock) as mock_list_space_messages, \
         patch("src.google_chat.advanced_search.create_date_filter") as mock_create_date_filter:
        
        # First call returns empty results to trigger the fallback
        mock_list_space_messages.return_value = {"messages": []}
        mock_create_date_filter.return_value = 'createTime > "2025-05-19T00:00:00Z" AND createTime < "2025-05-19T23:59:59.999999Z"'
        
        # Call advanced_search with dates
        await advanced_search_messages(
            query="test query",
            search_mode="semantic",
            spaces=["spaces/test"],
            start_date="2025-05-19",
            end_date="2025-05-19"
        )
        
        # Verify that create_date_filter was called with correct parameters
        mock_create_date_filter.assert_called_with("2025-05-19", "2025-05-19")
        
        # For semantic search, list_space_messages is called twice due to fallback behavior:
        # 1. First call with date filter
        # 2. Second call without date filter if first call returns no results
        assert mock_list_space_messages.call_count == 2
        
        # Check that first call has start_date and end_date
        first_call_args = mock_list_space_messages.call_args_list[0][1]
        assert "start_date" in first_call_args
        assert "end_date" in first_call_args
        assert first_call_args["start_date"] == "2025-05-19"
        assert first_call_args["end_date"] == "2025-05-19"
        
        # Check that second call doesn't have date parameters (fallback behavior)
        second_call_args = mock_list_space_messages.call_args_list[1][1]
        assert "start_date" not in second_call_args
        assert "end_date" not in second_call_args


@pytest.mark.asyncio
async def test_advanced_search_date_filter_fallback():
    """Test that semantic search falls back when date filter returns no results."""
    
    # First call returns empty results, simulating no matches with date filter
    # Second call returns some results, simulating finding matches without date filter
    mock_responses = [
        {"messages": []},
        {"messages": [{"text": "test message", "name": "spaces/test/messages/123"}]}
    ]
    
    with patch("src.google_chat.advanced_search.list_space_messages", new_callable=AsyncMock) as mock_list_space_messages:
        mock_list_space_messages.side_effect = mock_responses
        
        # Call advanced_search with semantic mode and date
        results = await advanced_search_messages(
            query="test query",
            search_mode="semantic",
            spaces=["spaces/test"],
            start_date="2025-05-19",
            end_date="2025-05-19"
        )
        
        # Verify that list_space_messages was called twice:
        # First with date filter, then without
        assert mock_list_space_messages.call_count == 2
        
        # First call should have dates
        first_call_args = mock_list_space_messages.call_args_list[0][1]
        assert "start_date" in first_call_args
        assert "end_date" in first_call_args
        
        # Second call should not have dates (fallback behavior)
        second_call_args = mock_list_space_messages.call_args_list[1][1]
        assert "start_date" not in second_call_args
        assert "end_date" not in second_call_args 