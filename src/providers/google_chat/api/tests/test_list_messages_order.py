import asyncio
import json
from datetime import datetime

from src.providers.google_chat.tools.message_tools import get_space_messages_tool

async def test_list_messages_order():
    print("Testing list_space_messages ordering (should be in descending order - newest first)")
    
    # Run a simple list messages request
    result = await get_space_messages_tool(
        space_name="spaces/AAQAXL5fJxI",
        page_size=10,
        days_window=3
    )
    
    # Print messages with their createTime for verification
    messages = result.get("messages", [])
    message_count = result.get("message_count", 0)
    print(f"\nFound {len(messages)} messages (message_count: {message_count}). Checking order:")
    
    # Verify message_count matches actual length
    if message_count == len(messages):
        print(f"✅ message_count field ({message_count}) correctly matches actual message count ({len(messages)})")
    else:
        print(f"❌ message_count field ({message_count}) doesn't match actual message count ({len(messages)})")
    
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

if __name__ == "__main__":
    asyncio.run(test_list_messages_order()) 