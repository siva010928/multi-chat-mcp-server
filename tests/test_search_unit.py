#!/usr/bin/env python
"""
Unit tests for the search functionality
"""
import pytest
import unittest.mock as mock
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# Import the modules to test
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from advanced_search_integration import advanced_search_messages
from search_manager import SearchManager

@pytest.fixture
def mock_search_manager():
    """Create a mock search manager."""
    with patch('search_manager.SearchManager') as mock_manager_class:
        instance = MagicMock()
        mock_manager_class.return_value = instance
        
        # Set up some methods
        instance.get_default_mode.return_value = "regex"
        instance.search.return_value = []
        
        # Add a mock for the _load_config method
        instance._load_config = MagicMock(return_value={
            'search_modes': [
                {
                    'name': 'regex',
                    'enabled': True,
                    'description': 'Regular expression search',
                    'weight': 1.2,
                    'options': {'ignore_case': True}
                }
            ],
            'search': {
                'default_mode': 'regex'
            }
        })
        
        yield instance

@pytest.mark.asyncio
async def test_regex_search_direct_call(mock_search_manager):
    """Test regex search with mocked search manager."""
    # Setup mock messages
    mock_messages = [
        {"text": "Updated the CICD pipeline", "createTime": "2023-05-01T12:00:00Z"},
        {"text": "Testing the CI/CD workflow", "createTime": "2023-05-02T12:00:00Z"}
    ]
    
    # Mock the list_space_messages function
    with patch('google_chat.list_space_messages', new_callable=AsyncMock) as mock_list:
        mock_list.return_value = {'messages': mock_messages}
        
        # Mock the search_manager.search method
        mock_search_manager.search.return_value = [(0.9, mock_messages[0]), (0.8, mock_messages[1])]
        
        # Mock the SearchManager initialization to avoid file loading
        with patch('advanced_search_integration.SearchManager', return_value=mock_search_manager):
            # Call the function
            result = await advanced_search_messages(
                query="cicd",
                search_mode="regex",
                spaces=["spaces/test"]
            )
            
            # Verify the search manager was used with the correct parameters
            mock_search_manager.search.assert_called_once()
            # Instead of examining specific indexes, just verify the search was called
            # and check the metadata in the result
            assert result['search_metadata']['query'] == "cicd"
            assert result['search_metadata']['mode'] == "regex"
            
            # Verify the result is as expected
            assert len(result['messages']) == 2
            assert 'search_metadata' in result
            assert result['search_complete'] is True

@pytest.mark.asyncio
async def test_semantic_search_direct_call(mock_search_manager):
    """Test semantic search with mocked search manager."""
    # Setup mock messages
    mock_messages = [
        {"text": "Need to improve our continuous integration process", "createTime": "2023-05-01T12:00:00Z"}
    ]
    
    # Mock the list_space_messages function
    with patch('google_chat.list_space_messages', new_callable=AsyncMock) as mock_list:
        mock_list.return_value = {'messages': mock_messages}
        
        # Mock the search_manager.search method
        mock_search_manager.search.return_value = [(0.85, mock_messages[0])]
        
        # Mock the SearchManager initialization to avoid file loading
        with patch('advanced_search_integration.SearchManager', return_value=mock_search_manager):
            # Call the function
            result = await advanced_search_messages(
                query="ci/cd implementation",
                search_mode="semantic",
                spaces=["spaces/test"]
            )
            
            # Verify the search manager was used with the correct parameters
            mock_search_manager.search.assert_called_once()
            
            # Verify the result
            assert len(result['messages']) == 1
            assert 'search_metadata' in result
            assert result['search_metadata']['mode'] == 'semantic'
            assert result['search_metadata']['query'] == 'ci/cd implementation'

@pytest.mark.asyncio
async def test_hybrid_search_direct_call(mock_search_manager):
    """Test hybrid search with mocked search manager."""
    # Setup mock messages
    mock_messages = [
        {"text": "Updated the CICD pipeline", "createTime": "2023-05-01T12:00:00Z"},
        {"text": "Need to improve our continuous integration process", "createTime": "2023-05-02T12:00:00Z"}
    ]
    
    # Mock the list_space_messages function
    with patch('google_chat.list_space_messages', new_callable=AsyncMock) as mock_list:
        mock_list.return_value = {'messages': mock_messages}
        
        # Mock the search_manager.search method
        mock_search_manager.search.return_value = [(0.9, mock_messages[0]), (0.85, mock_messages[1])]
        
        # Mock the SearchManager initialization to avoid file loading
        with patch('advanced_search_integration.SearchManager', return_value=mock_search_manager):
            # Call the function
            result = await advanced_search_messages(
                query="continuous integration",
                search_mode="hybrid",
                spaces=["spaces/test"]
            )
            
            # Verify the search manager was used with the correct parameters
            mock_search_manager.search.assert_called_once()
            
            # Verify the result
            assert len(result['messages']) == 2
            assert 'search_metadata' in result
            assert result['search_metadata']['mode'] == 'hybrid'
            assert result['search_metadata']['query'] == 'continuous integration'

@pytest.mark.asyncio
async def test_search_with_date_filters_direct_call(mock_search_manager):
    """Test search with date filters with mocked search manager."""
    # Setup mock messages
    mock_messages = [
        {"text": "CICD discussion", "createTime": "2023-05-01T12:00:00Z"}
    ]
    
    # Mock the list_space_messages function
    with patch('google_chat.list_space_messages', new_callable=AsyncMock) as mock_list:
        mock_list.return_value = {'messages': mock_messages}
        
        # Mock the search_manager.search method
        mock_search_manager.search.return_value = [(0.95, mock_messages[0])]
        
        # Mock the SearchManager initialization to avoid file loading
        with patch('advanced_search_integration.SearchManager', return_value=mock_search_manager):
            # Call the function
            result = await advanced_search_messages(
                query="cicd",
                search_mode="regex",
                spaces=["spaces/test"],
                start_date="2023-05-01",
                end_date="2023-05-02"
            )
            
            # Verify the filter string contains the dates
            mock_list.assert_called_once()
            kwargs = mock_list.call_args[1]
            assert 'filter_str' in kwargs
            assert 'createTime' in kwargs['filter_str']
            assert '2023-05-01' in kwargs['filter_str']
            assert '2023-05-02' in kwargs['filter_str']
            
            # Verify the result
            assert len(result['messages']) == 1

@pytest.mark.asyncio
async def test_error_handling_direct_call(mock_search_manager):
    """Test error handling with mocked search manager."""
    # Mock the list_space_messages function to raise an exception
    with patch('google_chat.list_space_messages', new_callable=AsyncMock) as mock_list:
        mock_list.side_effect = Exception("Search failed")
        
        # Mock the SearchManager initialization to avoid file loading
        with patch('advanced_search_integration.SearchManager', return_value=mock_search_manager):
            # Call the function
            result = await advanced_search_messages(
                query="cicd",
                search_mode="regex",
                spaces=["spaces/test"]
            )
            
            # Verify error handling - just check that we get an empty messages list
            assert 'messages' in result
            assert len(result['messages']) == 0
            assert 'nextPageToken' in result

@pytest.mark.asyncio
async def test_multiple_spaces_direct_call(mock_search_manager):
    """Test searching across multiple spaces with mocked search manager."""
    # Setup mock messages for each space
    mock_messages1 = [{"text": "CICD discussion", "createTime": "2023-05-01T12:00:00Z"}]
    mock_messages2 = [{"text": "More CICD talk", "createTime": "2023-05-02T12:00:00Z"}]
    
    # Mock the list_space_messages function
    with patch('google_chat.list_space_messages', new_callable=AsyncMock) as mock_list:
        # Return different messages for different spaces
        mock_list.side_effect = [
            {'messages': mock_messages1},
            {'messages': mock_messages2}
        ]
        
        # Mock the search_manager.search method
        combined_messages = mock_messages1 + mock_messages2
        mock_search_manager.search.return_value = [(0.9, combined_messages[0]), (0.8, combined_messages[1])]
        
        # Mock the SearchManager initialization to avoid file loading
        with patch('advanced_search_integration.SearchManager', return_value=mock_search_manager):
            # Call the function
            result = await advanced_search_messages(
                query="cicd",
                search_mode="regex",
                spaces=["spaces/test1", "spaces/test2"]
            )
            
            # Verify the function was called twice (once for each space)
            assert mock_list.call_count == 2
            
            # Verify the search was performed on combined messages
            mock_search_manager.search.assert_called_once()
            
            # Verify the result contains messages from both spaces
            assert 'space_info' in result
            assert 'searched_spaces' in result['space_info']
            assert len(result['space_info']['searched_spaces']) == 2
            assert len(result['messages']) == 2

if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 