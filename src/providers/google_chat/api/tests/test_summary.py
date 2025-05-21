import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from src.providers.google_chat.api.summary import (
    get_my_mentions,
    get_conversation_participants,
    summarize_conversation
)

@pytest.mark.asyncio
class TestSummaryUtils:

    @patch("src.providers.google_chat.api.summary.get_credentials", return_value=MagicMock())
    @patch("src.providers.google_chat.api.summary.get_current_user_info", new_callable=AsyncMock)
    @patch("src.providers.google_chat.api.summary.list_space_messages", new_callable=AsyncMock)
    @patch("src.providers.google_chat.api.summary.build")
    async def test_get_my_mentions_single_space(self, mock_build, mock_list_msgs, mock_user_info, mock_creds):
        mock_user_info.return_value = {"display_name": "Alice"}
        mock_list_msgs.return_value = {
            "messages": [
                {"text": "Hey Alice", "sender": {"name": "users/1"}},
                {"text": "No mention here"}
            ]
        }
        mock_build.return_value.spaces().get().execute.return_value = {
            "displayName": "Test Space"
        }

        result = await get_my_mentions(space_id="spaces/test", days=1)
        assert len(result["messages"]) == 1
        assert result["messages"][0]["space_info"]["displayName"] == "Test Space"

    @patch("src.providers.google_chat.api.summary.get_credentials", return_value=MagicMock())
    @patch("src.providers.google_chat.api.summary.get_current_user_info", new_callable=AsyncMock)
    @patch("src.providers.google_chat.api.summary.list_chat_spaces", new_callable=AsyncMock)
    @patch("src.providers.google_chat.api.summary.list_space_messages", new_callable=AsyncMock)
    @patch("src.providers.google_chat.api.summary.build")
    async def test_get_my_mentions_all_spaces(self, mock_build, mock_list_msgs, mock_list_spaces, mock_user_info, mock_creds):
        mock_user_info.return_value = {"display_name": "Bob"}
        mock_list_spaces.return_value = [{"name": "spaces/one"}, {"name": "spaces/two"}]
        mock_list_msgs.side_effect = [
            {"messages": [{"text": "hello @bob"}]},
            {"messages": [{"text": "no mention"}]}
        ]
        mock_build.return_value.spaces().get().execute.return_value = {
            "displayName": "Space"
        }

        result = await get_my_mentions(days=1)
        assert len(result["messages"]) == 1
        assert "@bob" in result["messages"][0]["text"].lower()

    @patch("src.providers.google_chat.api.summary.list_space_messages", new_callable=AsyncMock)
    async def test_get_conversation_participants(self, mock_list_msgs):
        mock_list_msgs.return_value = {
            "messages": [
                {"sender_info": {"id": "u1", "name": "User 1"}},
                {"sender_info": {"id": "u2", "name": "User 2"}},
                {"sender_info": {"id": "u1", "name": "User 1"}}
            ]
        }

        participants = await get_conversation_participants("spaces/test")
        assert len(participants) == 2
        assert any(p["id"] == "u1" for p in participants)

    @patch("src.providers.google_chat.api.summary.get_credentials", return_value=MagicMock())
    @patch("src.providers.google_chat.api.summary.list_space_messages", new_callable=AsyncMock)
    @patch("src.providers.google_chat.api.summary.build")
    async def test_summarize_conversation(self, mock_build, mock_list_msgs, mock_get_creds):
        mock_build.return_value.spaces().get().execute.return_value = {
            "name": "spaces/abc",
            "displayName": "Chat Space",
            "type": "ROOM"
        }
        mock_list_msgs.return_value = {
            "messages": [
                {"sender_info": {"id": "u1", "name": "User A"}, "text": "Hi"},
                {"sender_info": {"id": "u2", "name": "User B"}, "text": "Hello"}
            ],
            "nextPageToken": None
        }

        summary = await summarize_conversation("spaces/abc")
        assert summary["space"]["display_name"] == "Chat Space"
        assert summary["participant_count"] == 2
        assert summary["message_count"] == 2
