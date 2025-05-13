#!/usr/bin/env python
"""
Test script to debug the MCP tool API interface for search_messages
"""
import asyncio
import logging
import json
import re
from advanced_search_integration import advanced_search_messages
import httpx

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_tool_api")

async def test_direct_api_call(query="cicd", search_mode="regex"):
    """Test directly calling the advanced search integration API."""
    space_id = "spaces/AAQAXL5fJxI"  # Team space ID
    
    logger.info(f"Testing direct API call with query '{query}' and mode '{search_mode}' in space {space_id}")
    
    # Call the API directly
    api_result = await advanced_search_messages(
        query=query,
        search_mode=search_mode,
        spaces=[space_id],
        include_sender_info=True
    )
    
    # Log the results
    message_count = len(api_result.get('messages', []))
    logger.info(f"Direct API call found {message_count} messages matching '{query}'")
    
    # Print some details of the first few matches if any
    if message_count > 0:
        for i, msg in enumerate(api_result.get('messages', [])[:3]):
            text = msg.get('text', '')[:100]
            create_time = msg.get('createTime', '')[:19].replace('T', ' ')  # Format as YYYY-MM-DD HH:MM:SS
            logger.info(f"Message {i+1} [{create_time}]: {text}...")
            
            # Check if the query actually matches the text
            if search_mode == "regex":
                try:
                    pattern = re.compile(query, re.IGNORECASE)
                    if text and pattern.search(text):
                        logger.info(f"✓ Message {i+1} validates - matches regex '{query}'")
                    else:
                        logger.info(f"✗ Message {i+1} does NOT match regex '{query}'")
                except re.error:
                    logger.info(f"! Cannot verify regex - invalid pattern '{query}'")
            else:
                if query.lower() in text.lower():
                    logger.info(f"✓ Message {i+1} validates - contains '{query}'")
                else:
                    logger.info(f"✗ Message {i+1} does NOT contain '{query}'")
    
    return api_result

async def test_comprehensive_queries():
    """Run tests with various query formats to verify search behavior."""
    test_queries = [
        {"query": "cicd", "search_mode": "regex", "description": "Simple term 'cicd'"},
        {"query": "(?i)cicd", "search_mode": "regex", "description": "Case-insensitive 'cicd'"},
        {"query": "ci[ /\\-_]?cd|cicd", "search_mode": "regex", "description": "Any form of CI/CD"},
        {"query": "CI/CD", "search_mode": "regex", "description": "Exact 'CI/CD'"},
        {"query": "updated.*cicd", "search_mode": "regex", "description": "Updated + CICD in that order"},
        {"query": "cicd.*updated|updated.*cicd", "search_mode": "regex", "description": "Updated and CICD in any order"},
        {"query": "cicd.*pipeline|pipeline.*cicd", "search_mode": "regex", "description": "CICD pipeline in any order"},
        {"query": "\\bcicd\\b", "search_mode": "regex", "description": "CICD as a whole word only"},
        {"query": "\\bcicd\\b.*\\bpipeline\\b", "search_mode": "regex", "description": "CICD followed by pipeline (whole words)"},
        {"query": "docker.*storage", "search_mode": "regex", "description": "Docker storage related"},
        {"query": "pipeline", "search_mode": "regex", "description": "Pipeline term"},
        {"query": "continuous integration", "search_mode": "semantic", "description": "CI concept search"},
        {"query": "docker storage issue", "search_mode": "semantic", "description": "Docker storage issues"},
        {"query": "cicd pipeline", "search_mode": "semantic", "description": "CICD pipeline concept"},
        {"query": "ci/cd workflow", "search_mode": "semantic", "description": "CI/CD workflow concept"},
        {"query": "continuous integration and deployment", "search_mode": "semantic", "description": "CICD full concept"}
    ]
    
    logger.info("Starting comprehensive search tests")
    logger.info("=" * 80)
    
    for test in test_queries:
        query = test["query"]
        search_mode = test["search_mode"]
        description = test["description"]
        
        logger.info(f"Test: {description}")
        logger.info(f"Query: '{query}' using {search_mode} mode")
        
        result = await test_direct_api_call(query, search_mode)
        message_count = len(result.get('messages', []))
        
        logger.info(f"Result: {message_count} messages found")
        logger.info("-" * 80)
        
        # Pause briefly between tests
        await asyncio.sleep(0.5)

async def main():
    """Run the tests."""
    logger.info("Starting test script for advanced search")
    
    # Test specifically for the CICD pipeline message
    logger.info("TESTING FOR SPECIFIC CICD PIPELINE MESSAGE")
    logger.info("=" * 80)
    await test_direct_api_call("(?i)updated.*cicd.*pipeline", "regex")
    await test_direct_api_call("pipeline.*docker.*storage", "regex")
    
    # Run comprehensive tests with various query formats
    await test_comprehensive_queries()
    
    logger.info("Tests completed")

if __name__ == "__main__":
    asyncio.run(main()) 