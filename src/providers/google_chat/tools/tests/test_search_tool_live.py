import pytest
import traceback

from src.providers.google_chat.api.search import search_messages
from src.providers.google_chat.api.summary import get_my_mentions

@pytest.fixture(scope="module")
def test_space():
    return "spaces/AAQAXL5fJxI"  # Replace with your space ID

@pytest.mark.asyncio
async def test_live_regex_search(test_space):
    query = r"docker"
    print(f"\n🔍 Live Regex Search for: {query}")
    try:
        result = await search_messages(
            query=query,
            search_mode="regex",
            spaces=[test_space],
            include_sender_info=True,
        )
        assert "messages" in result
        print(f"✅ Found {len(result['messages'])} messages")
        if result["messages"]:
            print("First match:", result["messages"][0]["text"][:80])
    except Exception as e:
        print("❌ Live regex search failed")
        traceback.print_exc()
        pytest.fail(str(e))

@pytest.mark.asyncio
async def test_live_semantic_search(test_space):
    query = "unhealthy"
    print(f"\n🧠 Live Semantic Search for: {query}")
    try:
        result = await search_messages(
            query=query,
            search_mode="semantic",
            spaces=[test_space],
        )
        assert "messages" in result
        print(f"✅ Found {len(result['messages'])} messages")
        if result["messages"]:
            print("Top semantic match:", result["messages"][0]["text"][:80])
    except Exception as e:
        print("❌ Live semantic search failed")
        traceback.print_exc()
        pytest.fail(str(e))

@pytest.mark.asyncio
async def test_live_exact_match(test_space):
    query = "CI/CD Pipeline Update Summary"
    print(f"\n🔍 Live Exact Match Search for: '{query}'")
    try:
        result = await search_messages(
            query=query,
            search_mode="exact",
            spaces=[test_space],
        )
        assert "messages" in result
        print(f"✅ Found {len(result['messages'])} exact match(es)")
        if result["messages"]:
            print("Matched message:", result["messages"][0]["text"][:80])
    except Exception as e:
        print("❌ Live exact match search failed")
        traceback.print_exc()
        pytest.fail(str(e))

@pytest.mark.asyncio
async def test_live_mentions_summary():
    print("\n📣 Live Mentions Summary")
    try:
        result = await get_my_mentions(days=7)
        assert "messages" in result
        print(f"✅ Found {len(result['messages'])} recent mentions")
        if result["messages"]:
            print("Recent mention:", result["messages"][0]["text"][:80])
    except Exception as e:
        print("❌ Getting mentions failed")
        traceback.print_exc()
        pytest.fail(str(e))
