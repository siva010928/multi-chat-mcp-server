#!/usr/bin/env python3

"""
Test module for Google Chat MCP message-related tools.
"""

import asyncio
import sys
import os
import pytest
from datetime import datetime, timedelta
from pprint import pprint

# Add the project root to the path so we can import the src modules
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

from src.google_chat import messages


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


@pytest.fixture
async def test_message(authenticated, test_space):
    """Create a test message for use in other tests."""
    test_msg = f"Test message from Google Chat MCP test script - {datetime.now()}"
    try:
        result = await messages.create_message(test_space, test_msg)
        print(f"✅ Created test message: {result.get('name')}")
        return result
    except Exception as e:
        pytest.fail(f"Failed to create test message: {str(e)}")
        return None


@pytest.mark.asyncio
async def test_list_messages(authenticated, test_space):
    """Test list_messages with different date filters"""
    print("\n=== Testing list_messages ===")
    
    # Get today's date
    today = datetime.now()
    today_str = today.strftime('%Y-%m-%d')
    
    print(f"\n1. Getting messages from today ({today_str}):")
    result = await messages.list_space_messages(test_space, start_date=today_str, page_size=5)
    assert "messages" in result
    print(f"Messages found: {len(result['messages'])}")
    for idx, msg in enumerate(result['messages'][:2]):
        print(f"Message {idx+1} time: {msg.get('createTime')}")
    
    # Test with specific date range
    print("\n2. Getting messages from specific period:")
    result = await messages.list_space_messages(
        test_space, 
        start_date="2025-05-01", 
        end_date="2025-05-15",
        page_size=5
    )
    assert "messages" in result
    print(f"Messages found: {len(result['messages'])}")
    
    return True


@pytest.mark.asyncio
async def test_message_operations(authenticated, test_space):
    """Test basic message operations"""
    print("\n=== Testing message operations ===")
    
    # Create a test message
    print("\n1. Creating test message:")
    message = await messages.create_message(
        test_space,
        text="Test message created by diagnostic script"
    )
    assert message is not None
    assert "name" in message
    message_name = message.get('name')
    print(f"Message created: {message_name}")
    
    # Get the message
    print("\n2. Retrieving message:")
    retrieved = await messages.get_message(message_name)
    assert retrieved is not None
    assert "text" in retrieved
    print(f"Message retrieved: {retrieved.get('text')}")
    
    return True


# Functions that rely on existing message fixture
@pytest.mark.asyncio
async def test_get_message(authenticated, test_message):
    """Test getting a specific message."""
    print("\n=== Testing get_chat_message ===")
    message_name = test_message.get("name")
    result = await messages.get_message(message_name)
    assert result is not None
    assert "name" in result
    print(f"✅ Successfully retrieved message: {result.get('name')}")
    return result


@pytest.mark.asyncio
async def test_get_message_with_sender_info(authenticated, test_message):
    """Test getting a message with sender info."""
    print("\n=== Testing get_message_with_sender_info ===")
    message_name = test_message.get("name")
    result = await messages.get_message_with_sender_info(message_name)
    assert result is not None
    assert "sender_info" in result
    print(f"✅ Successfully retrieved message with sender info")
    print(f"   Sender: {result['sender_info'].get('display_name', 'Unknown')}")
    return result


# Run all tests in this module
@pytest.mark.asyncio
async def run_tests(test_space):
    """Run all message-related tests."""
    await test_list_messages(True, test_space)
    await test_message_operations(True, test_space)
    
    # Create a test message for subsequent tests
    message = await messages.create_message(
        test_space,
        text="Test message for subsequent tests"
    )
    
    if message:
        await test_get_message(True, message)
        await test_get_message_with_sender_info(True, message)
    
    print("\n=== All message tests completed ===")
    return True


if __name__ == "__main__":
    asyncio.run(run_tests("spaces/AAQAXL5fJxI")) 