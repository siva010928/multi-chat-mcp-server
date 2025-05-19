#!/usr/bin/env python3
"""
Simple test script to verify search with date filtering.
"""
import asyncio
import logging
import pytest

from src.google_chat.advanced_search import advanced_search_messages

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_script")

@pytest.mark.asyncio
async def test_search_with_dates():
    """Test search with different date configurations."""
    space_id = "spaces/AAQAXL5fJxI"  # Replace with your space ID
    
    # Test case 1: Simple search with no date filter
    logger.info("TEST CASE 1: Simple search with no date filter")
    results1 = await advanced_search_messages(
        query="test",
        search_mode="regex",
        spaces=[space_id],
        max_results=10,
        include_sender_info=True
    )
    logger.info(f"Results with no date filter: {len(results1.get('messages', []))} messages found")
    
    # Test case 2: Search with only start_date 
    logger.info("\nTEST CASE 2: Search with start_date only")
    start_date = "2025-05-01"
    results2 = await advanced_search_messages(
        query="test",
        search_mode="regex",
        spaces=[space_id],
        start_date=start_date,
        max_results=10,
        include_sender_info=True
    )
    logger.info(f"Results with start_date={start_date}: {len(results2.get('messages', []))} messages found")
    
    # Test case 3: Search with both start_date and end_date
    logger.info("\nTEST CASE 3: Search with start_date AND end_date")
    start_date = "2025-05-01" 
    end_date = "2025-05-30"
    results3 = await advanced_search_messages(
        query="test",
        search_mode="regex",
        spaces=[space_id],
        start_date=start_date,
        end_date=end_date,
        max_results=10,
        include_sender_info=True
    )
    logger.info(f"Results with date range {start_date} to {end_date}: {len(results3.get('messages', []))} messages found")
    
    # Summary
    logger.info("\n=== TEST SUMMARY ===")
    logger.info(f"Case 1 (no date filter): {len(results1.get('messages', []))} messages")
    logger.info(f"Case 2 (start_date only): {len(results2.get('messages', []))} messages")
    logger.info(f"Case 3 (start_date + end_date): {len(results3.get('messages', []))} messages")

if __name__ == "__main__":
    logger.info("Starting search tests...")
    asyncio.run(test_search_with_dates()) 