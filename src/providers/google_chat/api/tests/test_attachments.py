from unittest.mock import patch, MagicMock, mock_open

import pytest

from src.providers.google_chat.api.attachments import upload_attachment, send_file_message


@pytest.mark.asyncio
class TestAttachmentUtils:

    @patch("src.providers.google_chat.api.attachments.get_credentials", return_value=MagicMock())
    @patch("src.providers.google_chat.api.attachments.Path.exists", return_value=True)
    @patch("src.providers.google_chat.api.attachments.MediaFileUpload")
    @patch("src.providers.google_chat.api.attachments.build")
    async def test_upload_attachment_success(self, mock_build, mock_media, mock_exists, mock_get_creds):
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # Simulate media().upload().execute() returning attachment data
        mock_service.media.return_value.upload.return_value.execute.return_value = {"file": "uploaded"}

        # Simulate spaces().messages().create().execute()
        mock_service.spaces.return_value.messages.return_value.create.return_value.execute.return_value = {"message": "sent"}

        result = await upload_attachment("spaces/test", "somefile.txt", "Here is a file")

        assert "message" in result
        mock_media.assert_called_once()

    @patch("src.providers.google_chat.api.attachments.get_credentials", return_value=MagicMock())
    @patch("src.providers.google_chat.api.attachments.Path.exists", return_value=False)
    async def test_upload_attachment_file_not_found(self, mock_exists, mock_get_creds):
        with pytest.raises(Exception, match="File not found"):
            await upload_attachment("spaces/test", "missing.txt")

    @patch("src.providers.google_chat.api.attachments.get_credentials", return_value=None)
    async def test_upload_attachment_no_creds(self, mock_get_creds):
        with pytest.raises(Exception, match="No valid credentials found"):
            await upload_attachment("spaces/test", "somefile.txt")

    @patch("src.providers.google_chat.api.attachments.get_credentials", return_value=MagicMock())
    @patch("src.providers.google_chat.api.attachments.Path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data="Sample content")
    @patch("src.providers.google_chat.api.attachments.create_message", return_value={"message": "mocked"})
    async def test_send_file_message_success(self, mock_create, mock_open_, mock_exists, mock_get_creds):
        result = await send_file_message("spaces/test", "sample.txt", "Here it is")
        assert "message" in result
        mock_create.assert_called_once()

    @patch("src.providers.google_chat.api.attachments.get_credentials", return_value=None)
    async def test_send_file_message_no_creds(self, mock_get_creds):
        with pytest.raises(Exception, match="No valid credentials found"):
            await send_file_message("spaces/test", "sample.txt")

    @patch("src.providers.google_chat.api.attachments.get_credentials", return_value=MagicMock())
    @patch("src.providers.google_chat.api.attachments.Path.exists", return_value=False)
    async def test_send_file_message_file_missing(self, mock_exists, mock_get_creds):
        with pytest.raises(Exception, match="File not found"):
            await send_file_message("spaces/test", "sample.txt")
