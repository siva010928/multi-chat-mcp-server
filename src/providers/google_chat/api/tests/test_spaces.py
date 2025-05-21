import pytest
from unittest.mock import patch, MagicMock

from src.providers.google_chat.api.spaces import list_chat_spaces, manage_space_members


@pytest.mark.asyncio
class TestChatSpaces:

    @patch("src.providers.google_chat.api.spaces.build")
    @patch("src.providers.google_chat.api.spaces.get_credentials")
    async def test_list_chat_spaces_success(self, mock_get_creds, mock_build):
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_get_creds.return_value = MagicMock()

        mock_service.spaces.return_value.list.return_value.execute.return_value = {
            "spaces": [{"name": "spaces/abc", "displayName": "Test Space"}]
        }

        result = await list_chat_spaces()
        assert len(result) == 1
        assert result[0]["name"] == "spaces/abc"

    @patch("src.providers.google_chat.api.spaces.get_credentials", return_value=None)
    async def test_list_chat_spaces_no_creds(self, mock_get_creds):
        with pytest.raises(Exception, match="No valid credentials found"):
            await list_chat_spaces()

    @patch("src.providers.google_chat.api.spaces.build")
    @patch("src.providers.google_chat.api.spaces.get_credentials")
    async def test_manage_members_add_success(self, mock_get_creds, mock_build):
        mock_service = MagicMock()
        mock_get_creds.return_value = MagicMock()
        mock_build.return_value = mock_service

        result = await manage_space_members("abc", "add", ["test@example.com"])

        assert result["operation"] == "add"
        assert "test@example.com" in result["successful"]
        assert len(result["failed"]) == 0

    @patch("src.providers.google_chat.api.spaces.build")
    @patch("src.providers.google_chat.api.spaces.get_credentials")
    async def test_manage_members_remove_success(self, mock_get_creds, mock_build):
        mock_service = MagicMock()
        mock_get_creds.return_value = MagicMock()
        mock_build.return_value = mock_service

        result = await manage_space_members("abc", "remove", ["test@example.com"])

        assert result["operation"] == "remove"
        assert "test@example.com" in result["successful"]
        assert len(result["failed"]) == 0

    @patch("src.providers.google_chat.api.spaces.get_credentials", return_value=None)
    async def test_manage_members_no_creds(self, mock_get_creds):
        with pytest.raises(Exception, match="No valid credentials found"):
            await manage_space_members("abc", "add", ["test@example.com"])

    @patch("src.providers.google_chat.api.spaces.build")
    @patch("src.providers.google_chat.api.spaces.get_credentials")
    async def test_manage_members_invalid_operation(self, mock_get_creds, mock_build):
        mock_get_creds.return_value = MagicMock()  # ✅ valid mock Credentials
        mock_build.return_value = MagicMock()

        with pytest.raises(ValueError, match="Operation must be either 'add' or 'remove'"):
            await manage_space_members("abc", "update", ["test@example.com"])

