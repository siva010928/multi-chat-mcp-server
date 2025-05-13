#!/usr/bin/env python
"""
Test script to directly check the API response for various search terms
"""
import asyncio
import logging
from advanced_search_integration import advanced_search_messages

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_api_direct")

async def test_search_term(term, search_mode="regex"):
    """Test a specific search term with the specified search mode."""
    space_id = "spaces/AAQAXL5fJxI"  # Team space ID
    
    logger.info(f"Testing {search_mode} search with query '{term}' in space {space_id}")
    
    # Run search
    result = await advanced_search_messages(
        query=term, 
        spaces=[space_id],
        include_sender_info=True,
        search_mode=search_mode
    )
    
    # Print the results
    message_count = len(result.get('messages', []))
    print(f"\nSEARCH RESULTS for '{term}' using {search_mode} mode: {message_count} messages")
    
    # Print details of each message
    for i, msg in enumerate(result.get('messages', [])):
        print(f"\n--- Message {i+1} ---")
        print(f"Text: {msg.get('text', '')[:100]}...")  # First 100 chars
        
        # Show sender info if available
        if 'sender_info' in msg:
            sender = msg['sender_info']
            print(f"Sender: {sender.get('display_name', 'Unknown')} ({sender.get('email', 'No email')})")
        
        # Show creation time
        print(f"Created: {msg.get('createTime', 'Unknown time')}")
    
    return message_count

async def main():
    """Test multiple search terms with regex and semantic search."""
    # Test with regex search
    print("\n======= REGEX SEARCH RESULTS =======")
    cicd_regex_count = await test_search_term("cicd", "regex")
    ci_cd_regex_count = await test_search_term("ci/cd", "regex")
    pipeline_regex_count = await test_search_term("pipeline", "regex")
    
    # Test with semantic search
    print("\n======= SEMANTIC SEARCH RESULTS =======")
    cicd_semantic_count = await test_search_term("cicd", "semantic")
    ci_cd_semantic_count = await test_search_term("ci/cd", "semantic")
    pipeline_semantic_count = await test_search_term("pipeline", "semantic")
    
    # Summary
    print("\n======= SEARCH RESULTS SUMMARY =======")
    print(f"'cicd' - Regex: {cicd_regex_count}, Semantic: {cicd_semantic_count}")
    print(f"'ci/cd' - Regex: {ci_cd_regex_count}, Semantic: {ci_cd_semantic_count}")
    print(f"'pipeline' - Regex: {pipeline_regex_count}, Semantic: {pipeline_semantic_count}")

if __name__ == "__main__":
    asyncio.run(main()) 