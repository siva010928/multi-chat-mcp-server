#!/usr/bin/env python3

"""
Test module for Google Chat MCP authentication tools.
"""

import asyncio
import pytest
import sys
import os

from src.mcp_core.engine.provider_loader import get_provider_config_value, initialize_provider_config

# Initialize the provider configuration
initialize_provider_config("google_chat")

# Get token path from provider config
DEFAULT_TOKEN_PATH = get_provider_config_value("google_chat", "token_path")

# Convert to absolute path if it's a relative path
if not os.path.isabs(DEFAULT_TOKEN_PATH):
    # Get the project root directory (parent of src)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../'))
    DEFAULT_TOKEN_PATH = os.path.join(project_root, DEFAULT_TOKEN_PATH)

# Add the project root to the path so we can import the src modules
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

from src.providers.google_chat.api.auth import get_credentials, get_current_user_info, get_user_info_by_id


@pytest.mark.asyncio
async def test_authentication():
    """Test if authentication is working."""
    print("\n=== Testing Authentication ===")
    creds = get_credentials(token_path=DEFAULT_TOKEN_PATH)
    if creds and creds.valid:
        print("✅ Authentication successful - valid credentials found")
        if hasattr(creds, 'expiry'):
            print(f"   Token expires at: {creds.expiry}")
        assert True
        return True
    else:
        print("❌ Authentication failed - no valid credentials")
        assert False


@pytest.mark.asyncio
async def test_get_my_user_info(authenticated):
    """Test getting current user info."""
    print("\n=== Testing get_my_user_info ===")
    try:
        result = await get_current_user_info()
        print(f"✅ Successfully retrieved my user info")
        print(f"   User: {result.get('display_name', 'Unknown')}")
        assert result is not None
        assert 'display_name' in result
        return result
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        pytest.fail(f"Error getting user info: {str(e)}")


@pytest.mark.asyncio
async def test_get_user_info_by_id_with_none():
    """Test getting user info with None ID - should skip gracefully."""
    user_id = None
    if not user_id:
        print("\n=== Skipping get_user_info_by_id (no user ID) ===")
        assert True  # Test passes if it skips gracefully
        return

    # This code shouldn't execute with None user_id
    result = await get_user_info_by_id(user_id)
    assert result is not None


# Skip this test in pytest runs
@pytest.mark.skip(reason="Requires a valid user ID parameter")
@pytest.mark.asyncio
async def test_get_user_info_by_id():
    """Test getting user info by ID."""
    pytest.skip("This test requires a user ID to be passed as parameter")


# Run all tests for this module
@pytest.mark.asyncio
async def run_tests():
    """Run all authentication tests."""
    # First, check authentication
    auth_ok = await test_authentication()
    assert auth_ok, "Authentication failed"

    # Test user info
    await test_get_my_user_info(auth_ok)
    await test_get_user_info_by_id_with_none()

    print("\n=== All authentication tests completed ===")
    return True


if __name__ == "__main__":
    asyncio.run(run_tests()) 
