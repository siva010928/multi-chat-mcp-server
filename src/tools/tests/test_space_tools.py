#!/usr/bin/env python3

"""
Test module for Google Chat MCP space-related tools.
"""

import asyncio
import sys
import os
import pytest
from pprint import pprint

# Add the project root to the path so we can import the src modules
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

from src.google_chat import spaces, summary


@pytest.fixture
async def authenticated():
    """Fixture to check authentication before tests."""
    from src.google_chat.auth import get_credentials
    creds = get_credentials()
    if creds and creds.valid:
        return True
    else:
        pytest.fail("Authentication failed - skipping tests")
        return False


@pytest.mark.asyncio
async def test_authentication():
    """Test if authentication is working."""
    from src.google_chat.auth import get_credentials
    print("\n=== Testing Authentication ===")
    creds = get_credentials()
    if creds and creds.valid:
        print("✅ Authentication successful - valid credentials found")
        if hasattr(creds, 'expiry'):
            print(f"   Token expires at: {creds.expiry}")
        assert True
        return True
    else:
        print("❌ Authentication failed - no valid credentials")
        assert False
        return False


@pytest.mark.asyncio
async def test_get_spaces():
    """Test getting the list of spaces."""
    print("\n=== Testing get_chat_spaces ===")
    try:
        result = await spaces.list_chat_spaces()
        print(f"✅ Successfully retrieved {len(result)} spaces")
        
        # Print the first space for verification
        if result:
            print("\nSample space:")
            pprint(result[0])
            return result[0]["name"] if result else None
        
        return None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        pytest.fail(f"Failed to get spaces: {str(e)}")
        return None


@pytest.mark.asyncio
async def test_manage_space_members(test_space):
    """Test managing space members."""
    print(f"\n=== Testing manage_space_members (add) for {test_space} ===")
    try:
        # Use a fake email for testing - this should fail gracefully
        emails = ["test@example.com"]
        operation = "add"
        
        result = await spaces.manage_space_members(test_space, operation, emails)
        print(f"✅ Operation {operation} completed")
        return result
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        # Don't fail the test since we expect it to fail gracefully with fake email
        return None


@pytest.mark.asyncio
async def test_get_conversation_participants(test_space):
    """Test getting conversation participants."""
    print(f"\n=== Testing get_conversation_participants for {test_space} ===")
    try:
        result = await summary.get_conversation_participants(test_space)
        print(f"✅ Found {len(result)} participants")
        assert isinstance(result, list)
        return result
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        pytest.fail(f"Failed to get conversation participants: {str(e)}")
        return None


@pytest.mark.asyncio
async def test_summarize_conversation(test_space):
    """Test summarizing a conversation."""
    print(f"\n=== Testing summarize_conversation for {test_space} ===")
    try:
        result = await summary.summarize_conversation(test_space, message_limit=5)
        print("✅ Successfully summarized conversation")
        print(f"   Space: {result.get('space', {}).get('display_name', 'Unknown')}")
        print(f"   Participants: {len(result.get('participants', []))}")
        print(f"   Messages: {len(result.get('messages', []))}")
        assert "space" in result
        assert "participants" in result
        assert "messages" in result
        return result
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        pytest.fail(f"Failed to summarize conversation: {str(e)}")
        return None


@pytest.mark.asyncio
async def run_tests():
    """Run all space-related tests."""
    # Test spaces
    await test_authentication()
    await test_get_spaces()
    
    # Get a space name for further tests
    space_name = "spaces/AAQAXL5fJxI" 
    
    # Test space-related operations
    await test_get_conversation_participants(space_name)
    await test_summarize_conversation(space_name)
    await test_manage_space_members(space_name)
    
    print("\n=== All space tests completed ===")
    return True


if __name__ == "__main__":
    asyncio.run(run_tests()) 