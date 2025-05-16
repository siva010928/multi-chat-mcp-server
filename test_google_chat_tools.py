#!/usr/bin/env python3

"""
Test script for Google Chat MCP tools.
This script tests each of the available tools in the Google Chat MCP server.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pprint import pprint
import traceback

from src.google_chat.advanced_search import advanced_search_messages

# Add the project root to the path so we can import the src modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import necessary modules
from src.google_chat.auth import get_credentials, get_current_user_info, get_user_info_by_id
from src.google_chat import messages, spaces, summary, advanced_search

# Test space and thread for our tests
TEST_SPACE = "spaces/AAQAXL5fJxI"

async def test_authentication():
    """Test if authentication is working."""
    print("\n=== Testing Authentication ===")
    creds = get_credentials()
    if creds and creds.valid:
        print("✅ Authentication successful - valid credentials found")
        if hasattr(creds, 'expiry'):
            print(f"   Token expires at: {creds.expiry}")
        return True
    else:
        print("❌ Authentication failed - no valid credentials")
        return False

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
        return None

async def test_send_message(space_name):
    """Test sending a message to a space."""
    if not space_name:
        print("\n=== Skipping send_message (no space) ===")
        return None
    
    print(f"\n=== Testing send_message to {space_name} ===")
    try:
        test_message = f"Test message from Google Chat MCP test script - {datetime.now()}"
        result = await messages.create_message(space_name, test_message)
        print(f"✅ Message sent successfully: {result.get('name')}")
        return result
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

async def test_update_message(message):
    """Test updating a message."""
    if not message:
        print("\n=== Skipping update_chat_message (no message to update) ===")
        return None
    
    print("\n=== Testing update_chat_message ===")
    try:
        message_name = message.get("name")
        updated_text = f"Updated message - {datetime.now()}"
        result = await messages.update_message(message_name, updated_text)
        print(f"✅ Message updated successfully: {result.get('name')}")
        return result
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

async def test_reply_to_thread(message):
    """Test replying to a message thread."""
    if not message:
        print("\n=== Skipping reply_to_message_thread (no thread to reply to) ===")
        return None
    
    print("\n=== Testing reply_to_message_thread ===")
    try:
        space_name = message["name"].split("/messages/")[0]
        thread_key = message.get("thread", {}).get("name", "").split("/threads/")[-1]
        if not thread_key:
            thread_key = message["name"].split("/messages/")[-1]
        
        reply_text = f"Reply to thread - {datetime.now()}"
        result = await messages.reply_to_thread(space_name, thread_key, reply_text)
        print(f"✅ Reply sent successfully: {result.get('name')}")
        return result
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

async def test_get_message(message):
    """Test getting a specific message."""
    if not message:
        print("\n=== Skipping get_chat_message (no message to get) ===")
        return
    
    print("\n=== Testing get_chat_message ===")
    try:
        message_name = message.get("name")
        result = await messages.get_message(message_name)
        print(f"✅ Successfully retrieved message: {result.get('name')}")
        return result
    except Exception as e:
        print(f"❌ Error: {str(e)}")

async def test_get_space_messages(space_name):
    """Test getting messages from a space."""
    if not space_name:
        print("\n=== Skipping get_space_messages (no space) ===")
        return []
    
    print(f"\n=== Testing get_space_messages from {space_name} ===")
    try:
        # Get messages from last 7 days
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        result = await messages.list_space_messages(
            space_name, 
            start_date=start_date, 
            end_date=end_date,
            page_size=5
        )
        
        msgs = result.get("messages", [])
        print(f"✅ Successfully retrieved {len(msgs)} messages")
        return msgs
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return []

async def test_delete_message(message):
    """Test deleting a message."""
    if not message:
        print("\n=== Skipping delete_chat_message (no message to delete) ===")
        return
    
    print("\n=== Testing delete_chat_message ===")
    try:
        message_name = message.get("name")
        await messages.delete_message(message_name)
        print(f"✅ Message deleted successfully: {message_name}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

async def test_add_emoji_reaction(message):
    """Test adding an emoji reaction to a message."""
    if not message:
        print("\n=== Skipping add_emoji_reaction (no message) ===")
        return
    
    print("\n=== Testing add_emoji_reaction ===")
    try:
        message_name = message.get("name")
        emoji = "👍"  # thumbs up emoji
        result = await messages.add_emoji_reaction(message_name, emoji)
        print(f"✅ Emoji reaction added successfully")
        return result
    except Exception as e:
        print(f"❌ Error: {str(e)}")

async def test_get_message_with_sender_info(message):
    """Test getting a message with sender info."""
    if not message:
        print("\n=== Skipping get_message_with_sender_info (no message) ===")
        return
    
    print("\n=== Testing get_message_with_sender_info ===")
    try:
        message_name = message.get("name")
        result = await messages.get_message_with_sender_info(message_name)
        print(f"✅ Successfully retrieved message with sender info")
        if "sender_info" in result:
            print(f"   Sender: {result['sender_info'].get('display_name', 'Unknown')}")
        return result
    except Exception as e:
        print(f"❌ Error: {str(e)}")

async def test_list_messages_with_sender_info(space_name):
    """Test listing messages with sender info."""
    if not space_name:
        print("\n=== Skipping list_messages_with_sender_info (no space) ===")
        return
    
    print(f"\n=== Testing list_messages_with_sender_info for {space_name} ===")
    try:
        result = await messages.list_messages_with_sender_info(
            space_name,
            limit=3
        )
        msgs = result.get("messages", [])
        print(f"✅ Successfully retrieved {len(msgs)} messages with sender info")
        return result
    except Exception as e:
        print(f"❌ Error: {str(e)}")

async def test_search_messages(query="update"):
    """Test searching for messages."""
    print("\n=== Testing search_messages ===")
    try:
        print(f"Searching for '{query}'...")
        result = await advanced_search_messages(
            query=query,
            search_mode="semantic",
            spaces=[
                "spaces/AAQAXL5fJxI"  # Replace with your space ID
            ],
            include_sender_info=True
        )
        
        if result and "messages" in result:
            print(f"✅ Found {len(result['messages'])} messages matching query")
            if result['messages']:
                msg = result['messages'][0]
                print(f"   First result: {msg['text'][:50]}..." if len(msg['text']) > 50 else msg['text'])
        else:
            print("❌ No messages found for query")
        
        # Now test with date filter
        print(f"\nSearching for '{query}' with date filter...")
        result = await advanced_search_messages(
            query=query,
            search_mode="semantic",
            spaces=[
                "spaces/AAQAXL5fJxI"  # Replace with your space ID
            ],
            include_sender_info=True,
            start_date="2025-05-01",
            end_date="2025-05-31"
        )
        
        if result and "messages" in result:
            print(f"✅ Found {len(result['messages'])} messages with date filter")
            if result['messages']:
                msg = result['messages'][0]
                print(f"   First result: {msg['text'][:50]}..." if len(msg['text']) > 50 else msg['text'])
        else:
            print("✅ No messages found within date range (expected if no matches)")
            
        return result
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        traceback.print_exc()

async def test_get_my_mentions():
    """Test getting mentions of the current user."""
    print("\n=== Testing get_my_mentions ===")
    try:
        # Check if the function exists in the messages module
        if not hasattr(summary, "get_my_mentions"):
            print("❌ Function 'get_my_mentions' not found in messages module")
            return

        result = await summary.get_my_mentions(days=30)
        msgs = result.get("messages", [])
        print(f"✅ Found {len(msgs)} mentions")
        return result
    except Exception as e:
        print(f"❌ Error: {str(e)}")

async def test_get_my_user_info():
    """Test getting current user info."""
    print("\n=== Testing get_my_user_info ===")
    try:
        result = await get_current_user_info()
        print(f"✅ Successfully retrieved my user info")
        print(f"   User: {result.get('display_name', 'Unknown')}")
        return result
    except Exception as e:
        print(f"❌ Error: {str(e)}")

async def test_get_user_info_by_id(message):
    """Test getting user info by ID."""
    if not message or "sender" not in message:
        print("\n=== Skipping get_user_info_by_id (no sender) ===")
        return
    
    print("\n=== Testing get_user_info_by_id ===")
    try:
        user_id = message["sender"].get("name")
        if not user_id:
            print("❌ No user ID found in message")
            return
        
        result = await get_user_info_by_id(user_id)
        print(f"✅ Successfully retrieved user info")
        print(f"   User: {result.get('display_name', 'Unknown')}")
        return result
    except Exception as e:
        print(f"❌ Error: {str(e)}")

async def test_summarize_conversation(space_name):
    """Test summarizing a conversation."""
    if not space_name:
        print("\n=== Skipping summarize_conversation (no space) ===")
        return
    
    print(f"\n=== Testing summarize_conversation for {space_name} ===")
    try:
        result = await summary.summarize_conversation(space_name, message_limit=5)
        print("✅ Successfully summarized conversation")
        print(f"   Space: {result.get('space', {}).get('display_name', 'Unknown')}")
        print(f"   Participants: {len(result.get('participants', []))}")
        print(f"   Messages: {len(result.get('messages', []))}")
        return result
    except Exception as e:
        print(f"❌ Error: {str(e)}")

async def test_get_conversation_participants(space_name):
    """Test getting conversation participants."""
    if not space_name:
        print("\n=== Skipping get_conversation_participants (no space) ===")
        return
    
    print(f"\n=== Testing get_conversation_participants for {space_name} ===")
    try:
        result = await summary.get_conversation_participants(space_name)
        print(f"✅ Found {len(result)} participants")
        return result
    except Exception as e:
        print(f"❌ Error: {str(e)}")

async def test_manage_space_members(space_name, operation="add", emails=None):
    """Test managing space members."""
    if not space_name:
        print("\n=== Skipping manage_space_members (no space) ===")
        return
    
    if not emails:
        # Use a fake email for testing - this should fail gracefully
        emails = ["test@example.com"]
    
    print(f"\n=== Testing manage_space_members ({operation}) for {space_name} ===")
    try:
        result = await spaces.manage_space_members(space_name, operation, emails)
        print(f"✅ Operation {operation} completed")
        return result
    except Exception as e:
        print(f"❌ Error: {str(e)}")

async def test_list_messages():
    """Test list_messages with different date filters"""
    print("\n=== Testing list_messages ===")
    
    # Get today's date
    today = datetime.datetime.now()
    today_str = today.strftime('%Y-%m-%d')
    
    print(f"\n1. Getting messages from today ({today_str}):")
    result = await messages.list_space_messages(TEST_SPACE, start_date=today_str, page_size=5)
    print(f"Messages found: {len(result['messages'])}")
    for idx, msg in enumerate(result['messages'][:2]):
        print(f"Message {idx+1} time: {msg.get('createTime')}")
    
    # Test with specific date range
    print("\n2. Getting messages from specific period:")
    result = await messages.list_space_messages(
        TEST_SPACE, 
        start_date="2025-05-01", 
        end_date="2025-05-15",
        page_size=5
    )
    print(f"Messages found: {len(result['messages'])}")
    
    return True

async def test_message_operations():
    """Test basic message operations"""
    print("\n=== Testing message operations ===")
    
    # Create a test message
    print("\n1. Creating test message:")
    message = await messages.create_message(
        TEST_SPACE,
        text="Test message created by diagnostic script"
    )
    message_name = message.get('name')
    print(f"Message created: {message_name}")
    
    # Get the message
    print("\n2. Retrieving message:")
    message = await messages.get_message(message_name)
    print(f"Message retrieved: {message.get('text')}")
    
    return True

async def test_summary_tools():
    """Test summary-related tools"""
    print("\n=== Testing summary tools ===")
    
    # Test mentions
    print("\n1. Getting recent mentions (last 7 days):")
    mentions = await get_my_mentions(days=7)
    print(f"Mentions found: {len(mentions.get('messages', []))}")
    
    # Test conversation summary
    print("\n2. Getting conversation summary:")
    summary = await summarize_conversation(TEST_SPACE, message_limit=5)
    print(f"Space: {summary.get('space', {}).get('display_name')}")
    print(f"Participants: {summary.get('participant_count')}")
    print(f"Messages: {summary.get('message_count')}")
    
    return True

async def main():
    """Main function to run all tests."""
    print("Starting Google Chat MCP Tool Tests")
    print("==================================")
    
    # First, check authentication
    auth_ok = await test_authentication()
    if not auth_ok:
        print("\n❌ Authentication failed - cannot run tests")
        return
    
    # Test getting spaces first
    space = await test_get_spaces()
    space_name = space if space else None
    
    # Test sending a message (needed for other tests)
    message = await test_send_message(space_name)
    
    # Test message operations
    await test_get_message(message)
    await test_get_message_with_sender_info(message)
    updated_message = await test_update_message(message)
    reply_message = await test_reply_to_thread(updated_message or message)
    
    # Test emoji reaction
    await test_add_emoji_reaction(updated_message or message)
    
    # Test listing messages and searching
    await test_get_space_messages(space_name)
    await test_list_messages_with_sender_info(space_name)
    await test_search_messages(query="unhealthy")
    await test_get_my_mentions()
    
    # Test user info
    await test_get_my_user_info()
    await test_get_user_info_by_id(message)
    
    # Test conversation summary and participants
    await test_summarize_conversation(space_name)
    await test_get_conversation_participants(space_name)
    
    # Test space member management
    await test_manage_space_members(space_name)
    
    # Test summary tools
    await test_summary_tools()
    
    # Finally, test deleting a message (if we want to clean up)
    # Uncomment these if you want to delete the test messages
    # await test_delete_message(reply_message)
    # await test_delete_message(updated_message or message)
    
    print("\n=== All tests completed ===")

if __name__ == "__main__":
    asyncio.run(main()) 