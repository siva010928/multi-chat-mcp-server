"""Test module for Google Chat MCP user-related tools."""

import pytest
from unittest.mock import patch, AsyncMock

from src.tools.user_tools import get_my_user_info_tool, get_user_info_by_id_tool


@pytest.mark.asyncio
async def test_get_my_user_info():
    """Test getting current user info."""
    # Create a mock for get_current_user_info
    mock_user_info = {
        "email": "test_user@example.com",
        "display_name": "Test User",
        "given_name": "Test",
        "family_name": "User",
        "profile_photo": "https://example.com/photo.jpg"
    }
    
    # Apply the mock and call the function
    with patch("src.tools.user_tools.get_current_user_info", 
               new=AsyncMock(return_value=mock_user_info)):
        result = await get_my_user_info_tool()
    
    # Validate the result
    assert result == mock_user_info
    assert "email" in result
    assert "display_name" in result
    assert result["email"] == "test_user@example.com"
    assert result["display_name"] == "Test User"


@pytest.mark.asyncio
async def test_get_user_info_by_id():
    """Test getting user info by ID."""
    # Create a mock for get_user_info_by_id
    mock_user_info = {
        "id": "users/12345",
        "email": "other_user@example.com",
        "display_name": "Other User",
        "given_name": "Other",
        "family_name": "User",
        "profile_photo": "https://example.com/other_photo.jpg"
    }
    
    # Apply the mock and call the function
    with patch("src.tools.user_tools.get_user_info_by_id", 
               new=AsyncMock(return_value=mock_user_info)):
        result = await get_user_info_by_id_tool("users/12345")
    
    # Validate the result
    assert result == mock_user_info
    assert "id" in result
    assert "email" in result
    assert result["id"] == "users/12345"
    assert result["email"] == "other_user@example.com"


@pytest.mark.asyncio
async def test_get_user_info_by_id_error_handling():
    """Test error handling in get_user_info_by_id."""
    # Create a mock for get_user_info_by_id that returns result with error
    mock_error_result = {
        "id": "invalid_id",
        "display_name": "Unknown User",
        "error": "Failed to retrieve user details: Invalid ID format"
    }
    
    # Apply the mock and call the function
    with patch("src.tools.user_tools.get_user_info_by_id", 
               new=AsyncMock(return_value=mock_error_result)):
        result = await get_user_info_by_id_tool("invalid_id")
    
    # Validate the result contains error information
    assert "error" in result
    assert result["id"] == "invalid_id"
    assert "display_name" in result  # Basic info should still be returned


@pytest.mark.asyncio
async def run_tests():
    """Run all user-related tests."""
    await test_get_my_user_info()
    await test_get_user_info_by_id()
    await test_get_user_info_by_id_error_handling()
    print("All user tool tests passed!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_tests()) 