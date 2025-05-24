import pytest
from unittest.mock import patch, MagicMock, mock_open, AsyncMock
from google.oauth2.credentials import Credentials
from pathlib import Path

from src.providers.google_chat.api.auth import (
    get_credentials,
    save_credentials,
    refresh_token,
    get_current_user_info,
    get_user_info_by_id
)

# Mock configuration for tests
MOCK_CONFIG = {
    "token_path": "dummy/token.json",
    "scopes": [
        "https://www.googleapis.com/auth/chat.spaces.readonly",
        "https://www.googleapis.com/auth/chat.messages",
        "https://www.googleapis.com/auth/chat.messages.create",
        "https://www.googleapis.com/auth/chat.spaces"
    ]
}


DUMMY_TOKEN_PATH = "dummy/token.json"


@pytest.mark.asyncio
class TestAuthUtils:

    @pytest.fixture(autouse=True)
    def mock_provider_config(self):
        """Mock the provider_loader.load_provider_config function to return our test config."""
        with patch("src.mcp_core.engine.provider_loader.load_provider_config", return_value=MOCK_CONFIG):
            yield

    @pytest.fixture
    def dummy_creds(self):
        creds = MagicMock(spec=Credentials)
        creds.valid = True
        creds.expired = False
        creds.refresh_token = "dummy-refresh-token"
        creds.to_json.return_value = '{"token": "abc"}'
        return creds

    @patch("builtins.open", new_callable=mock_open)
    def test_save_credentials_writes_to_file(self, mock_open_, dummy_creds):
        save_credentials(dummy_creds, token_path=DUMMY_TOKEN_PATH)

        mock_open_.assert_called_once_with(Path(DUMMY_TOKEN_PATH), "w")
        handle = mock_open_.return_value
        handle.write.assert_called_once_with(dummy_creds.to_json())

    @patch("pathlib.Path.exists", return_value=True)
    @patch("src.providers.google_chat.api.auth.Credentials.from_authorized_user_file")
    def test_get_credentials_from_file(self, mock_from_file, mock_exists):
        from src.providers.google_chat.api import auth
        auth.token_info["credentials"] = None  # Clear in-memory cache

        # Create mock credentials
        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_creds.expired = False
        mock_creds.refresh_token = "dummy"
        mock_from_file.return_value = mock_creds

        result = get_credentials(DUMMY_TOKEN_PATH)

        # Check identity
        assert result is mock_creds

    @patch("src.providers.google_chat.api.auth.save_credentials")
    async def test_refresh_token_success(self, mock_save):
        from src.providers.google_chat.api import auth

        dummy_creds = MagicMock(spec=Credentials)
        dummy_creds.expired = True
        dummy_creds.refresh_token = "refresh"
        dummy_creds.valid = True
        dummy_creds.refresh = MagicMock()

        auth.token_info["credentials"] = dummy_creds

        success, msg = await refresh_token(DUMMY_TOKEN_PATH)
        assert success is True
        assert "successfully" in msg
        dummy_creds.refresh.assert_called_once()
        mock_save.assert_called_once_with(dummy_creds, DUMMY_TOKEN_PATH)

    @patch("pathlib.Path.exists", return_value=False)
    async def test_refresh_token_no_creds(self, mock_exists):
        from src.providers.google_chat.api import auth
        auth.token_info["credentials"] = None

        success, msg = await refresh_token(DUMMY_TOKEN_PATH)
        assert not success
        assert "no token file" in msg.lower()

    @patch("src.providers.google_chat.api.auth.get_credentials")
    @patch("src.providers.google_chat.api.auth.build")
    async def test_get_current_user_info_success(self, mock_build, mock_get_creds, dummy_creds):
        mock_people = MagicMock()
        mock_get = mock_people.people.return_value.get
        mock_get.return_value.execute.return_value = {
            "names": [{"displayName": "Jane Smith", "givenName": "Jane", "familyName": "Smith"}],
            "emailAddresses": [{"value": "jane@example.com"}]
        }

        mock_build.return_value = mock_people
        mock_get_creds.return_value = dummy_creds

        result = await get_current_user_info()
        assert result["email"] == "jane@example.com"
        assert result["display_name"] == "Jane Smith"

    @patch("src.providers.google_chat.api.auth.get_credentials")
    @patch("src.providers.google_chat.api.auth.build")
    async def test_get_user_info_by_id_success(self, mock_build, mock_get_creds, dummy_creds):
        mock_people = MagicMock()
        mock_get = mock_people.people.return_value.get
        mock_get.return_value.execute.return_value = {
            "names": [{"displayName": "John Doe", "givenName": "John", "familyName": "Doe"}],
            "emailAddresses": [{"value": "john@example.com"}],
            "photos": [{"url": "https://photo.example.com"}]
        }

        mock_build.return_value = mock_people
        mock_get_creds.return_value = dummy_creds

        result = await get_user_info_by_id("users/123")
        assert result["email"] == "john@example.com"
        assert result["display_name"] == "John Doe"
        assert result["profile_photo"].startswith("https://")

    @patch("src.providers.google_chat.api.auth.get_credentials", return_value=None)
    async def test_get_user_info_by_id_no_creds(self, mock_get_creds):
        with pytest.raises(Exception, match="No valid credentials found"):
            await get_user_info_by_id("users/123")
