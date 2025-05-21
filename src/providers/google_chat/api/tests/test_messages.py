from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from src.providers.google_chat.api.messages import list_space_messages, create_message, update_message, reply_to_thread, \
    get_message, delete_message, add_emoji_reaction, list_messages_with_sender_info, get_message_with_sender_info


MOCK_MESSAGE = {
    "name": "spaces/abc/messages/123",
    "text": "Test message",
    "sender": {"name": "users/123"},
    "sender_info": {
        "email": "test@example.com",
        "display_name": "Test User"
    }
}



@pytest.mark.asyncio
class TestListSpaceMessages:

    @patch("src.providers.google_chat.api.messages.build")
    @patch("src.providers.google_chat.api.messages.get_credentials")
    async def test_basic(self, mock_get_creds, mock_build):
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.spaces.return_value.messages.return_value.list.return_value.execute.return_value = {
            "messages": [MOCK_MESSAGE]
        }

        result = await list_space_messages("spaces/abc")
        assert result["messages"][0]["text"] == "Test message"

    @patch("src.providers.google_chat.api.messages.build")
    @patch("src.providers.google_chat.api.messages.get_credentials")
    @patch("src.providers.google_chat.api.messages.create_date_filter")
    async def test_with_date_filter(self, mock_date_filter, mock_get_creds, mock_build):
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.spaces.return_value.messages.return_value.list.return_value.execute.return_value = {
            "messages": [MOCK_MESSAGE]
        }

        mock_date_filter.return_value = 'createTime > "2024-05-01T00:00:00Z"'

        result = await list_space_messages("spaces/abc", start_date="2024-05-01")
        assert "messages" in result
        mock_date_filter.assert_called_once()

    @patch("src.providers.google_chat.api.messages.get_user_info_by_id", new_callable=AsyncMock)
    @patch("src.providers.google_chat.api.messages.build")
    @patch("src.providers.google_chat.api.messages.get_credentials")
    async def test_with_sender_info(self, mock_get_creds, mock_build, mock_user_info):
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.spaces.return_value.messages.return_value.list.return_value.execute.return_value = {
            "messages": [MOCK_MESSAGE]
        }

        mock_user_info.return_value = {"email": "test@example.com", "display_name": "Test User"}

        result = await list_space_messages("spaces/abc", include_sender_info=True)
        assert "sender_info" in result["messages"][0]
        assert result["messages"][0]["sender_info"]["email"] == "test@example.com"

    @patch("src.providers.google_chat.api.messages.build")
    @patch("src.providers.google_chat.api.messages.get_credentials")
    async def test_invalid_date(self, mock_get_creds, mock_build):
        with patch("src.providers.google_chat.api.messages.create_date_filter") as mock_filter:
            mock_filter.side_effect = ValueError("Invalid date format")
            with pytest.raises(ValueError, match="Invalid date format"):
                await list_space_messages("spaces/abc", start_date="invalid-date")

SPACE_NAME = "spaces/abc"
TEXT = "Hello from test!"
CARDS = [{"card_id": "123", "content": "Test card"}]

@pytest.mark.asyncio
class TestCreateMessage:

    @patch("src.providers.google_chat.api.messages.build")
    @patch("src.providers.google_chat.api.messages.get_credentials")
    async def test_create_message_basic(self, mock_get_creds, mock_build):
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_response = {"name": "spaces/abc/messages/999", "text": TEXT}
        mock_service.spaces.return_value.messages.return_value.create.return_value.execute.return_value = mock_response

        result = await create_message(SPACE_NAME, TEXT)
        assert result["name"] == "spaces/abc/messages/999"
        assert result["text"] == TEXT

    @patch("src.providers.google_chat.api.messages.build")
    @patch("src.providers.google_chat.api.messages.get_credentials")
    async def test_create_message_with_cards(self, mock_get_creds, mock_build):
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_response = {"name": "spaces/abc/messages/1000", "text": TEXT, "cardsV2": CARDS}
        mock_service.spaces.return_value.messages.return_value.create.return_value.execute.return_value = mock_response

        result = await create_message(SPACE_NAME, TEXT, cards_v2=CARDS)
        assert result["cardsV2"] == CARDS

    @patch("src.providers.google_chat.api.messages.get_credentials")
    async def test_create_message_no_credentials(self, mock_get_creds):
        mock_get_creds.return_value = None

        with pytest.raises(Exception, match="No valid credentials found"):
            await create_message(SPACE_NAME, TEXT)

MESSAGE_NAME = "spaces/abc/messages/123"
UPDATED_TEXT = "Updated text!"
UPDATED_CARDS = [{"card_id": "card_001"}]

@pytest.mark.asyncio
class TestUpdateMessage:

    @patch("src.providers.google_chat.api.messages.build")
    @patch("src.providers.google_chat.api.messages.get_credentials")
    async def test_update_text_only(self, mock_get_creds, mock_build):
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_response = {"name": MESSAGE_NAME, "text": UPDATED_TEXT}
        mock_service.spaces.return_value.messages.return_value.patch.return_value.execute.return_value = mock_response

        result = await update_message(MESSAGE_NAME, text=UPDATED_TEXT)
        assert result["text"] == UPDATED_TEXT

    @patch("src.providers.google_chat.api.messages.build")
    @patch("src.providers.google_chat.api.messages.get_credentials")
    async def test_update_cards_only(self, mock_get_creds, mock_build):
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_response = {"name": MESSAGE_NAME, "cardsV2": UPDATED_CARDS}
        mock_service.spaces.return_value.messages.return_value.patch.return_value.execute.return_value = mock_response

        result = await update_message(MESSAGE_NAME, cards_v2=UPDATED_CARDS)
        assert result["cardsV2"] == UPDATED_CARDS

    @patch("src.providers.google_chat.api.messages.get_credentials")
    async def test_update_message_no_credentials(self, mock_get_creds):
        mock_get_creds.return_value = None

        with pytest.raises(Exception, match="No valid credentials found"):
            await update_message(MESSAGE_NAME, text="Anything")

    @pytest.mark.asyncio
    async def test_update_message_no_input(self):
        with pytest.raises(ValueError, match="At least one of text or cards_v2 must be provided"):
            await update_message(MESSAGE_NAME)  # ✅ call it inside async

THREAD_KEY = "sample-thread-key"


@pytest.mark.asyncio
class TestReplyToThread:

    @pytest.mark.asyncio
    @patch("src.providers.google_chat.api.messages.build")
    @patch("src.providers.google_chat.api.messages.get_credentials")
    async def test_reply_to_thread_direct_key(self, mock_get_creds, mock_build):
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_get_creds.return_value = MagicMock()

        # Setup fake API return
        mock_create = mock_service.spaces.return_value.messages.return_value.create
        mock_create.return_value.execute.return_value = {"name": MESSAGE_NAME}

        result = await reply_to_thread(SPACE_NAME, THREAD_KEY, "Hello thread!")

        assert result["name"] == MESSAGE_NAME
        args, kwargs = mock_create.call_args
        assert kwargs["body"]["thread"]["threadKey"] == THREAD_KEY


    @pytest.mark.asyncio
    @patch("src.providers.google_chat.api.messages.build")
    @patch("src.providers.google_chat.api.messages.get_credentials")
    async def test_reply_to_thread_with_full_thread_name(self, mock_get_creds, mock_build):
        thread_name = "spaces/abc/threads/xyz"
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_get_creds.return_value = MagicMock()

        mock_create = mock_service.spaces.return_value.messages.return_value.create
        mock_create.return_value.execute.return_value = {"name": MESSAGE_NAME}

        result = await reply_to_thread(SPACE_NAME, thread_name, "Full thread")

        assert result["name"] == MESSAGE_NAME
        args, kwargs = mock_create.call_args
        assert kwargs["body"]["thread"]["name"] == thread_name


    @pytest.mark.asyncio
    @patch("src.providers.google_chat.api.messages.build")
    @patch("src.providers.google_chat.api.messages.get_credentials")
    async def test_reply_to_thread_fallback_to_thread_lookup(self, mock_get_creds, mock_build):
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_get_creds.return_value = MagicMock()

        thread_key = "fallback-thread-id"
        fake_thread_name = "spaces/abc/threads/xyz"

        # Mock failed direct get but successful search
        mock_service.spaces.return_value.messages.return_value.get.side_effect = Exception("Not found")
        mock_service.spaces.return_value.messages.return_value.list.return_value.execute.return_value = {
            "messages": [
                {"thread": {"name": fake_thread_name}, "name": f"{SPACE_NAME}/messages/{thread_key}"}
            ]
        }

        mock_create = mock_service.spaces.return_value.messages.return_value.create
        mock_create.return_value.execute.return_value = {"name": MESSAGE_NAME}

        result = await reply_to_thread(SPACE_NAME, thread_key, "Fallback thread")
        assert result["name"] == MESSAGE_NAME
        args, kwargs = mock_create.call_args
        assert kwargs["body"]["thread"]["name"] == fake_thread_name

class TestGetMessage:

    @pytest.mark.asyncio
    @patch("src.providers.google_chat.api.messages.build")
    @patch("src.providers.google_chat.api.messages.get_credentials")
    async def test_get_message_basic(self, mock_get_creds, mock_build):
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.spaces.return_value.messages.return_value.get.return_value.execute.return_value = MOCK_MESSAGE

        result = await get_message("spaces/abc/messages/123")
        assert result["text"] == "Test message"

    @pytest.mark.asyncio
    @patch("src.providers.google_chat.api.messages.get_user_info_by_id", new_callable=AsyncMock)
    @patch("src.providers.google_chat.api.messages.build")
    @patch("src.providers.google_chat.api.messages.get_credentials")
    async def test_get_message_with_sender_info(self, mock_get_creds, mock_build, mock_user_info):
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.spaces.return_value.messages.return_value.get.return_value.execute.return_value = MOCK_MESSAGE
        mock_user_info.return_value = {"display_name": "Sender Test"}

        result = await get_message("spaces/abc/messages/123", include_sender_info=True)
        assert "sender_info" in result
        assert result["sender_info"]["display_name"] == "Sender Test"

    @pytest.mark.asyncio
    @patch("src.providers.google_chat.api.messages.get_credentials")
    async def test_get_message_no_credentials(self, mock_get_creds):
        mock_get_creds.return_value = None
        with pytest.raises(Exception, match="No valid credentials found"):
            await get_message("spaces/abc/messages/123")


class TestDeleteMessage:

    @pytest.mark.asyncio
    @patch("src.providers.google_chat.api.messages.build")
    @patch("src.providers.google_chat.api.messages.get_credentials")
    async def test_delete_message_success(self, mock_get_creds, mock_build):
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.spaces.return_value.messages.return_value.delete.return_value.execute.return_value = {}

        result = await delete_message("spaces/abc/messages/123")
        assert result == {}

    @pytest.mark.asyncio
    @patch("src.providers.google_chat.api.messages.get_credentials")
    async def test_delete_message_no_credentials(self, mock_get_creds):
        mock_get_creds.return_value = None
        with pytest.raises(Exception, match="No valid credentials found"):
            await delete_message("spaces/abc/messages/123")

@pytest.mark.asyncio
class TestAddEmojiReaction:
    @patch("src.providers.google_chat.api.messages.build")
    @patch("src.providers.google_chat.api.messages.get_credentials")
    async def test_add_emoji_reaction_success(self, mock_get_creds, mock_build):
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.spaces.return_value.messages.return_value.reactions.return_value.create.return_value.execute.return_value = {}

        result = await add_emoji_reaction("spaces/abc/messages/123", emoji="👍")
        assert result == {}

    @patch("src.providers.google_chat.api.messages.get_credentials")
    async def test_add_emoji_reaction_no_credentials(self, mock_get_creds):
        mock_get_creds.return_value = None
        with pytest.raises(Exception, match="No valid credentials found"):
            await add_emoji_reaction("spaces/abc/messages/123", emoji="🔥")

MESSAGES_WITH_SENDER = [
    {"name": "spaces/abc/messages/1", "text": "Hello!", "sender": {"name": "users/123"}},
    {"name": "spaces/abc/messages/2", "text": "Hi!", "sender": {"name": "users/456"}}
]

@pytest.mark.asyncio
class TestGetMessageWithSenderInfo:

    @patch("src.providers.google_chat.api.messages.get_user_info_by_id", new_callable=AsyncMock)
    async def test_returns_enriched_message(self, mock_user_info):
        mock_user_info.return_value = {
            "email": "test@example.com",
            "display_name": "Test User"
        }

        # Also patch API service to avoid real call
        with patch("src.providers.google_chat.api.messages.build") as mock_build, \
                patch("src.providers.google_chat.api.messages.get_credentials") as mock_creds:
            mock_service = MagicMock()
            mock_build.return_value = mock_service
            mock_creds.return_value = MagicMock()

            mock_service.spaces.return_value.messages.return_value.get.return_value.execute.return_value = {
                "name": "spaces/abc/messages/123",
                "text": "Hello!",
                "sender": {"name": "users/123"}
            }

            result = await get_message_with_sender_info("spaces/abc/messages/123")

            assert result["sender_info"]["email"] == "test@example.com"
            assert result["sender_info"]["display_name"] == "Test User"


@pytest.mark.asyncio
class TestListMessagesWithSenderInfo:

    @patch("src.providers.google_chat.api.messages.get_user_info_by_id", new_callable=AsyncMock)
    @patch("src.providers.google_chat.api.messages.build")
    @patch("src.providers.google_chat.api.messages.get_credentials")
    async def test_enriches_messages_with_sender_info(self, mock_get_creds, mock_build, mock_user_info):
        # Prepare fake service and credentials
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_get_creds.return_value = MagicMock()

        # Simulate API returning messages with senders
        mock_service.spaces.return_value.messages.return_value.list.return_value.execute.return_value = {
            "messages": [
                {"text": "Hi", "sender": {"name": "users/1"}},
                {"text": "Hello", "sender": {"name": "users/2"}}
            ]
        }

        # Simulate get_user_info_by_id returning info
        mock_user_info.side_effect = [
            {"email": "user1@example.com", "display_name": "User One"},
            {"email": "user2@example.com", "display_name": "User Two"}
        ]

        result = await list_messages_with_sender_info("spaces/mock-space")

        # Assertions
        assert len(result["messages"]) == 2
        assert result["messages"][0]["sender_info"]["email"] == "user1@example.com"
        assert result["messages"][1]["sender_info"]["display_name"] == "User Two"
        assert mock_user_info.await_count == 2

