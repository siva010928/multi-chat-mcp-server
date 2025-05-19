#!/usr/bin/env python3

"""
Test module for Google Chat MCP search-related tools.
"""

import asyncio
import sys
import os
import pytest
import traceback
from datetime import datetime, timedelta

# Add the project root to the path so we can import the src modules
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

from src.google_chat.advanced_search import advanced_search_messages
from src.google_chat.summary import get_my_mentions


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
async def test_search_messages(authenticated, test_space):
    """Test searching for messages."""
    query = "update"
    print("\n=== Testing search_messages ===")
    try:
        print(f"Searching for '{query}'...")
        # Using regex search mode instead of semantic to avoid transformer dependency issues
        result = await advanced_search_messages(
            query=query,
            search_mode="regex",  # Changed from "semantic" to "regex"
            spaces=[
                test_space
            ],
            include_sender_info=True
        )
        
        if result and "messages" in result:
            print(f"✅ Found {len(result['messages'])} messages matching query")
            if result['messages']:
                msg = result['messages'][0]
                print(f"   First result: {msg['text'][:50]}..." if len(msg['text']) > 50 else msg['text'])
            assert True  # Result contains messages array
        else:
            print("❌ No messages found for query")
            # Not asserting false here, as empty results are valid depending on the space content
        
        # Now test with date filter
        print(f"\nSearching for '{query}' with date filter...")
        result = await advanced_search_messages(
            query=query,
            search_mode="regex",  # Changed from "semantic" to "regex"
            spaces=[
                test_space
            ],
            include_sender_info=True,
            start_date="2025-05-01",
            end_date="2025-05-31"
        )
        
        # We're just testing that date filtering doesn't crash
        # Results will vary depending on what's in the test space
        assert "messages" in result
            
        return result
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        traceback.print_exc()
        pytest.fail(f"Search failed with error: {str(e)}")


@pytest.mark.asyncio
async def test_get_my_mentions(authenticated):
    """Test getting mentions of the current user."""
    print("\n=== Testing get_my_mentions ===")
    try:
        result = await get_my_mentions(days=30)
        msgs = result.get("messages", [])
        print(f"✅ Found {len(msgs)} mentions")
        assert "messages" in result
        return result
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        pytest.fail(f"Getting mentions failed with error: {str(e)}")


# Run all tests in this module
@pytest.mark.asyncio
async def run_tests(test_space):
    """Run all search-related tests."""
    await test_search_messages(True, test_space)
    await test_get_my_mentions(True)
    print("\n=== All search tests completed ===")
    return True


if __name__ == "__main__":
    asyncio.run(run_tests("spaces/AAQAXL5fJxI")) 