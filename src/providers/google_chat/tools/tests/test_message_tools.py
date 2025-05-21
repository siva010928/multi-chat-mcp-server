# #!/usr/bin/env python3
#
# """
# Test module for Google Chat MCP message-related tools.
# """

import pytest
from datetime import datetime

from src.providers.google_chat.tools.message_tools import (
    send_message_tool,
    update_chat_message_tool,
    reply_to_message_thread_tool,
    get_space_messages_tool,
    get_chat_message_tool,
    get_message_with_sender_info_tool,
    delete_chat_message_tool,
    add_emoji_reaction_tool,
    send_file_content_tool,
    list_messages_with_sender_info_tool,
)

@pytest.mark.asyncio
class TestGoogleChatMCPMessageTools:
    async def test_send_message_tool(self, authenticated, test_space):
        msg = await send_message_tool(space_name=test_space, text="📩 Hello from test!")
        assert msg["text"] == "📩 Hello from test!"
        assert msg["name"].startswith("spaces/")

    async def test_update_chat_message_tool(self, authenticated, test_space):
        msg = await send_message_tool(space_name=test_space, text="🔧 Will update")
        updated = await update_chat_message_tool(message_name=msg["name"], new_text="✅ Updated text")
        assert updated["text"] == "✅ Updated text"

    async def test_reply_to_message_thread_tool(self, authenticated, test_space):
        root = await send_message_tool(space_name=test_space, text="💬 Thread root")
        thread_key = root.get("thread", {}).get("name", root["name"].split("/")[-1])
        reply = await reply_to_message_thread_tool(space_name=test_space, thread_key=thread_key, text="↩️ Thread reply")
        assert reply["text"] == "↩️ Thread reply"
        assert "thread" in reply

    async def test_get_space_messages_tool(self, authenticated, test_space):
        today = datetime.now().strftime('%Y-%m-%d')
        result = await get_space_messages_tool(space_name=test_space, start_date=today)
        assert "messages" in result
        assert result["source"] == "get_space_messages"

    async def test_get_chat_message_tool(self, authenticated, test_message):
        msg = await get_chat_message_tool(message_name=test_message["name"])
        assert msg["name"] == test_message["name"]

    async def test_get_message_with_sender_info_tool(self, authenticated, test_message):
        result = await get_message_with_sender_info_tool(message_name=test_message["name"])
        assert "sender_info" in result
        assert result["sender_info"].get("display_name", None) is not None

    async def test_delete_chat_message_tool(self, authenticated, test_space):
        msg = await send_message_tool(space_name=test_space, text="🗑️ Delete me")
        deleted = await delete_chat_message_tool(message_name=msg["name"])
        assert deleted == {}

    async def test_add_emoji_reaction_tool(self, authenticated, test_space):
        msg = await send_message_tool(space_name=test_space, text="🎉 Add reaction")
        reaction = await add_emoji_reaction_tool(message_name=msg["name"], emoji="🎯")
        assert reaction["emoji"]["unicode"] == "🎯"

    async def test_send_file_content_tool(self, authenticated, test_space):
        result = await send_file_content_tool(space_name=test_space)
        assert "File Content" in result["text"]

    async def test_list_messages_with_sender_info_tool(self, authenticated, test_space):
        result = await list_messages_with_sender_info_tool(space_name=test_space, limit=2)
        assert "messages" in result
        for msg in result["messages"]:
            assert "sender_info" in msg
