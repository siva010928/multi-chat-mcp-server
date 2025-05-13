#!/usr/bin/env python
"""
Test script for searching messages with advanced search capabilities
"""
import asyncio
import logging
from advanced_search_integration import advanced_search_messages

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_search")

async def run_search():
    # Define test parameters
    space_id = "spaces/AAQAXL5fJxI"  # Team space ID
    search_term = "pipeline"  # Changed from "cicd" to "pipeline" to test related concept
    
    logger.info(f"Testing search with query '{search_term}' in space {space_id}")
    
    # First try with basic search mode
    logger.info("--- Testing with basic 'exact' search mode ---")
    exact_result = await advanced_search_messages(
        query=search_term, 
        spaces=[space_id],
        include_sender_info=True,
        search_mode="exact"  # Use exact string matching
    )
    
    # Print the results
    print(f"\nEXACT SEARCH results: {len(exact_result.get('messages', []))} messages")
    print_message_details(exact_result.get('messages', []))
    
    # Then try with semantic search
    logger.info("--- Testing with semantic search mode ---")
    semantic_result = await advanced_search_messages(
        query=search_term, 
        spaces=[space_id],
        include_sender_info=True,
        search_mode="semantic"  # Use semantic search
    )
    
    # Print the results
    print(f"\nSEMANTIC SEARCH results: {len(semantic_result.get('messages', []))} messages")
    print_message_details(semantic_result.get('messages', []))

def print_message_details(messages):
    """Helper function to print message details"""
    # Print details of each message
    for i, msg in enumerate(messages):
        print(f"\n--- Message {i+1} ---")
        print(f"Text: {msg.get('text', '')[:100]}...")  # First 100 chars
        
        # Show sender info if available
        if 'sender_info' in msg:
            sender = msg['sender_info']
            print(f"Sender: {sender.get('display_name', 'Unknown')} ({sender.get('email', 'No email')})")
        
        # Show creation time
        print(f"Created: {msg.get('createTime', 'Unknown time')}")
        
        # Show space info
        if 'space_info' in msg:
            print(f"Space: {msg['space_info'].get('name', 'Unknown space')}")

# Run the search
if __name__ == "__main__":
    asyncio.run(run_search()) 