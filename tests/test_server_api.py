#!/usr/bin/env python
"""
Unit tests for the server API search endpoints
"""
import pytest
import sys
import os
from unittest.mock import patch, AsyncMock
import json
from fastapi import FastAPI, HTTPException, Body
from fastapi.testclient import TestClient
from typing import Optional, List, Dict

# Add parent directory to path to import server
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the search_messages function from server
from server import search_messages

# Create a mock FastAPI app for testing
app = FastAPI()

# Define a proper request model with validation
from pydantic import BaseModel, Field

class SearchRequest(BaseModel):
    query: str
    search_mode: Optional[str] = None
    spaces: Optional[List[str]] = None
    max_results: Optional[int] = 50
    include_sender_info: Optional[bool] = False
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    filter_str: Optional[str] = None

# Add the search_messages endpoint to our test app with validation
@app.post("/search_messages")
async def search_messages_endpoint(request_data: SearchRequest):
    try:
        # Forward the request to the actual search_messages function
        result = await search_messages(
            query=request_data.query,
            search_mode=request_data.search_mode,
            spaces=request_data.spaces,
            max_results=request_data.max_results,
            include_sender_info=request_data.include_sender_info,
            start_date=request_data.start_date,
            end_date=request_data.end_date,
            filter_str=request_data.filter_str
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})

# Create test client
client = TestClient(app)

@pytest.fixture
def mock_advanced_search():
    """Create a mock for the advanced search function."""
    with patch('advanced_search_integration.advanced_search_messages', new_callable=AsyncMock) as mock_search:
        # Set up a default return value
        mock_search.return_value = {
            "messages": [
                {
                    "name": "spaces/test/messages/123",
                    "text": "Test message with CICD content",
                    "createTime": "2023-05-01T12:00:00Z"
                }
            ],
            "nextPageToken": None,
            "search_complete": True
        }
        yield mock_search

def test_search_messages_endpoint_success(mock_advanced_search):
    """Test the search_messages endpoint with successful search."""
    # Prepare test data
    test_request = {
        "query": "cicd",
        "search_mode": "regex",
        "spaces": ["spaces/test"],
        "max_results": 10
    }
    
    # Make request to the API
    response = client.post("/search_messages", json=test_request)
    
    # Verify response
    assert response.status_code == 200
    response_data = response.json()
    assert "messages" in response_data
    assert len(response_data["messages"]) == 1
    
    # Verify the search function was called with correct parameters
    mock_advanced_search.assert_called_once()
    call_kwargs = mock_advanced_search.call_args.kwargs
    assert call_kwargs["query"] == "cicd"
    assert call_kwargs["search_mode"] == "regex"
    assert call_kwargs["spaces"] == ["spaces/test"]

def test_search_messages_missing_query():
    """Test search_messages endpoint with missing query."""
    # Prepare test data with missing query
    test_request = {
        "search_mode": "regex",
        "spaces": ["spaces/test"]
    }
    
    # Make request to the API
    response = client.post("/search_messages", json=test_request)
    
    # Verify response - should error due to missing required field
    # With our Pydantic model validation, we expect 422 Unprocessable Entity
    assert response.status_code == 422
    assert "detail" in response.json()
    # Check that the error is about the missing query field
    assert "query" in str(response.json()["detail"])

def test_search_messages_default_parameters(mock_advanced_search):
    """Test search_messages endpoint uses correct defaults."""
    # Prepare minimal test data
    test_request = {
        "query": "cicd"
    }
    
    # Make request to the API
    response = client.post("/search_messages", json=test_request)
    
    # Verify response
    assert response.status_code == 200
    
    # Verify query was passed correctly and search_mode was None (defaults are applied in advanced_search_messages)
    call_kwargs = mock_advanced_search.call_args.kwargs
    assert call_kwargs["query"] == "cicd"
    assert call_kwargs["search_mode"] is None  # Default mode should be None, will be set to 'regex' inside advanced_search_messages
    assert call_kwargs["max_results"] == 50  # Default max_results

def test_search_messages_with_dates(mock_advanced_search):
    """Test search_messages endpoint with date filters."""
    # Prepare test data with dates
    test_request = {
        "query": "cicd",
        "search_mode": "regex",
        "spaces": ["spaces/test"],
        "start_date": "2023-05-01",
        "end_date": "2023-05-10"
    }
    
    # Make request to the API
    response = client.post("/search_messages", json=test_request)
    
    # Verify response
    assert response.status_code == 200
    
    # Verify date parameters were passed
    call_kwargs = mock_advanced_search.call_args.kwargs
    assert call_kwargs["start_date"] == "2023-05-01"
    assert call_kwargs["end_date"] == "2023-05-10"

def test_search_messages_error_handling(mock_advanced_search):
    """Test error handling in search_messages endpoint."""
    # Configure mock to raise an exception
    mock_advanced_search.side_effect = Exception("Search failed")
    
    # Prepare test data
    test_request = {
        "query": "cicd",
        "search_mode": "regex"
    }
    
    # Make request to the API
    response = client.post("/search_messages", json=test_request)
    
    # Verify response - should return 500 error
    assert response.status_code == 500
    response_data = response.json()
    assert "detail" in response_data
    assert "error" in response_data["detail"]

def test_search_messages_different_modes(mock_advanced_search):
    """Test search_messages endpoint with different search modes."""
    # Test semantic search
    test_request = {
        "query": "continuous integration",
        "search_mode": "semantic"
    }
    
    response = client.post("/search_messages", json=test_request)
    assert response.status_code == 200
    
    # Verify search mode was passed correctly
    call_kwargs = mock_advanced_search.call_args.kwargs
    assert call_kwargs["search_mode"] == "semantic"
    
    # Reset mock and test hybrid search
    mock_advanced_search.reset_mock()
    test_request["search_mode"] = "hybrid"
    
    response = client.post("/search_messages", json=test_request)
    assert response.status_code == 200
    
    # Verify search mode was passed correctly
    call_kwargs = mock_advanced_search.call_args.kwargs
    assert call_kwargs["search_mode"] == "hybrid"

if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 