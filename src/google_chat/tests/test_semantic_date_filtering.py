import pytest
import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from src.google_chat.advanced_search import advanced_search_messages
from src.google_chat.messages import list_space_messages


@pytest.mark.asyncio
async def test_semantic_search_fallback_when_no_date_results():
    """Test that semantic search falls back to ignoring date filter when no results found."""
    
    # Mock data - message outside date range but semantically relevant
    old_message = {
        "name": "spaces/123/messages/456",
        "text": "Here's the quarterly financial report we discussed",
        "createTime": "2024-05-13T14:30:00Z"
    }
    
    # Mock the list_space_messages function
    with patch("src.google_chat.advanced_search.list_space_messages", new_callable=AsyncMock) as mock_list_messages:
        # First call with date filter returns empty list (no messages in date range)
        # Second call without date filter returns our test message
        mock_list_messages.side_effect = [
            {"messages": [], "nextPageToken": None},  # No results with date filter
            {"messages": [old_message], "nextPageToken": None}  # Results without date filter
        ]
        
        # Mock the SearchManager
        with patch("src.google_chat.advanced_search.SearchManager") as mock_search_mgr:
            # Configure the search manager mock
            search_manager_instance = MagicMock()
            mock_search_mgr.return_value = search_manager_instance
            
            # Mock the search method to return our message as relevant
            search_manager_instance.search.return_value = [(0.95, old_message)]
            search_manager_instance.get_default_mode.return_value = "semantic"
            
            # Call the function under test
            result = await advanced_search_messages(
                query="financial report",
                search_mode="semantic",
                spaces=["spaces/123"],
                start_date="2024-05-18"  # Date AFTER our message
            )
            
            # Assert we got our message despite it being outside date range
            assert len(result["messages"]) == 1
            assert result["messages"][0]["name"] == "spaces/123/messages/456"
            
            # Verify that list_messages was called twice:
            # 1. First with date filter
            # 2. Then without date filter
            assert mock_list_messages.call_count == 2
            
            # Check the first call included the date filter
            args1, kwargs1 = mock_list_messages.call_args_list[0]
            assert kwargs1.get("start_date") == "2024-05-18"
            
            # Check the second call had no date filter
            args2, kwargs2 = mock_list_messages.call_args_list[1]
            assert "start_date" not in kwargs2


@pytest.mark.asyncio
async def test_semantic_search_with_date_results():
    """Test that semantic search properly uses date filter when results are available in range."""
    
    # Mock data - message inside date range and semantically relevant
    recent_message = {
        "name": "spaces/123/messages/789",
        "text": "The latest financial analysis is now available",
        "createTime": "2024-05-20T09:15:00Z"
    }
    
    # Mock the list_space_messages function
    with patch("src.google_chat.advanced_search.list_space_messages", new_callable=AsyncMock) as mock_list_messages:
        # First call with date filter returns our test message (message found in date range)
        mock_list_messages.return_value = {
            "messages": [recent_message], 
            "nextPageToken": None
        }
        
        # Mock the SearchManager
        with patch("src.google_chat.advanced_search.SearchManager") as mock_search_mgr:
            # Configure the search manager mock
            search_manager_instance = MagicMock()
            mock_search_mgr.return_value = search_manager_instance
            
            # Mock the search method to return our message as relevant
            search_manager_instance.search.return_value = [(0.92, recent_message)]
            search_manager_instance.get_default_mode.return_value = "semantic"
            
            # Call the function under test
            result = await advanced_search_messages(
                query="financial analysis",
                search_mode="semantic",
                spaces=["spaces/123"],
                start_date="2024-05-18"  # Date BEFORE our message
            )
            
            # Assert we got our message from inside date range
            assert len(result["messages"]) == 1
            assert result["messages"][0]["name"] == "spaces/123/messages/789"
            
            # Verify that list_messages was called only once (no need for fallback)
            assert mock_list_messages.call_count == 1


@pytest.mark.asyncio
async def test_regex_search_strict_date_filtering():
    """Test that regex search strictly enforces date filters with no fallback."""
    
    # Mock data - message outside date range but with matching text
    old_message = {
        "name": "spaces/123/messages/456",
        "text": "Budget report for Q1",
        "createTime": "2024-05-13T14:30:00Z"
    }
    
    # Mock the list_space_messages function
    with patch("src.google_chat.advanced_search.list_space_messages", new_callable=AsyncMock) as mock_list_messages:
        # Call with date filter returns empty list (no messages in date range)
        mock_list_messages.return_value = {"messages": [], "nextPageToken": None}
        
        # Mock the SearchManager
        with patch("src.google_chat.advanced_search.SearchManager") as mock_search_mgr:
            # Configure the search manager mock
            search_manager_instance = MagicMock()
            mock_search_mgr.return_value = search_manager_instance
            search_manager_instance.get_default_mode.return_value = "regex"
            
            # Call the function under test
            result = await advanced_search_messages(
                query="budget",
                search_mode="regex",  # Not semantic - should enforce date filter strictly
                spaces=["spaces/123"],
                start_date="2024-05-18"  # Date AFTER our message
            )
            
            # Assert we got NO messages (strict date filtering)
            assert len(result["messages"]) == 0
            
            # Verify that list_messages was called only once (no fallback for regex mode)
            assert mock_list_messages.call_count == 1
            
            # Check that the search manager's search method was never called
            # (because there were no messages to search)
            search_manager_instance.search.assert_not_called() 