#!/usr/bin/env python
"""
Test script to check if semantic search works properly with various queries
"""
import asyncio
import logging
from advanced_search_integration import advanced_search_messages

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_semantic_search")

async def run_search_tests():
    """Run a series of tests with different search modes and queries."""
    # Define test parameters
    space_id = "spaces/AAQAXL5fJxI"  # Team space ID
    
    # Define test cases
    test_cases = [
        {
            "name": "Regex search for CICD",
            "query": "cicd",
            "search_mode": "regex",
        },
        {
            "name": "Case-insensitive regex for CICD",
            "query": "(?i)cicd",
            "search_mode": "regex",
        },
        {
            "name": "Regex for CI/CD variants",
            "query": "ci[ /\\-_]?cd|cicd",
            "search_mode": "regex",
        },
        {
            "name": "Regex for CICD pipeline variations",
            "query": "cicd.*pipeline|pipeline.*cicd",
            "search_mode": "regex",
        },
        {
            "name": "Regex for updated CICD",
            "query": "updated.*cicd",
            "search_mode": "regex",
        },
        {
            "name": "Regex for docker storage",
            "query": "docker.*storage",
            "search_mode": "regex",
        },
        {
            "name": "Semantic search for CI/CD concepts",
            "query": "continuous integration",
            "search_mode": "semantic",
        },
        {
            "name": "Semantic search for CI/CD pipeline concepts",
            "query": "continuous integration pipeline",
            "search_mode": "semantic",
        },
        {
            "name": "Semantic search for CICD implementation",
            "query": "implementing cicd",
            "search_mode": "semantic",
        },
        {
            "name": "Semantic search for docker storage",
            "query": "docker storage issue",
            "search_mode": "semantic",
        },
        {
            "name": "Exact search for CI/CD",
            "query": "CI/CD",
            "search_mode": "exact",
        },
        {
            "name": "Hybrid search for CI/CD workflows",
            "query": "continuous integration workflow",
            "search_mode": "hybrid",
        }
    ]
    
    # Run each test
    for test in test_cases:
        name = test["name"]
        query = test["query"]
        search_mode = test["search_mode"]
        
        logger.info(f"\n===== TEST: {name} =====")
        logger.info(f"Query: '{query}' with {search_mode} mode in space {space_id}")
        
        # Run search
        search_result = await advanced_search_messages(
            query=query, 
            spaces=[space_id],
            include_sender_info=True,
            search_mode=search_mode
        )
        
        # Process results
        messages = search_result.get('messages', [])
        logger.info(f"Found {len(messages)} messages")
        
        # Show sample of results
        for i, msg in enumerate(messages[:3]):
            if i >= len(messages):
                break
                
            text = msg.get('text', '')[:100].replace('\n', ' ')
            create_time = msg.get('createTime', '')[:19].replace('T', ' ')
            sender = msg.get('sender_info', {}).get('display_name', 'Unknown')
            
            logger.info(f"  Result {i+1}: [{create_time}] {sender}: {text}...")
            
        logger.info(f"====================\n")

async def main():
    """Main entry point."""
    logger.info("Starting search tests")
    await run_search_tests()
    logger.info("All tests completed")

if __name__ == "__main__":
    asyncio.run(main()) 