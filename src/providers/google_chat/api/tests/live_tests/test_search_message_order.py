import asyncio
import json
import os
import sys
from datetime import datetime
from unittest.mock import patch

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../..")))

from src.providers.google_chat.tools.search_tools import search_messages_tool

# Mock configuration for tests
MOCK_CONFIG = {
    "search_config_path": "mock_search_config.yaml"
}

@patch("src.mcp_core.engine.provider_loader.load_provider_config", return_value=MOCK_CONFIG)
async def test_search_order(_):
    print("Testing search order (messages should be sorted by createTime in descending order - newest first)")

    # Run a simple search
    result = await search_messages_tool(
        query="headache|sick|unavailable",
        search_mode="regex",
        spaces=["spaces/AAQAXL5fJxI"],
        days_window=14
    )

    # Print messages with their createTime for verification
    messages = result.get("messages", [])
    print(f"\nFound {len(messages)} messages. Checking order:")

    if not messages:
        print("No messages found.")
        return

    # Print the creation times and check if they are in descending order
    times = []
    for i, message in enumerate(messages):
        create_time = message.get("createTime", "unknown")
        timestamp = datetime.fromisoformat(create_time.replace('Z', '+00:00')) if create_time != "unknown" else None
        text_snippet = message.get("text", "")[:50] + "..." if message.get("text", "") else "No text"
        print(f"{i+1}. {create_time} - {text_snippet}")
        if timestamp:
            times.append(timestamp)

    # Verify ordering
    if len(times) > 1:
        is_ordered = all(times[i] >= times[i+1] for i in range(len(times)-1))
        if is_ordered:
            print("\n✅ Messages are correctly ordered by createTime in descending order (newest first)")
        else:
            print("\n❌ Messages are NOT ordered by createTime in descending order!")

    print("\nSearch metadata:")
    print(json.dumps(result.get("search_metadata", {}), indent=2))

if __name__ == "__main__":
    asyncio.run(test_search_order()) 
