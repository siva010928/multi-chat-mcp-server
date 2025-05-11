import unittest
from unittest import mock
import os
import json
import datetime
from pathlib import Path
import sys
import asyncio

# Add parent directory to path to import google_chat
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import google_chat
from google.oauth2.credentials import Credentials

class TestFileOperations(unittest.TestCase):
    """Test file operations in google_chat.py"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock credentials
        self.mock_creds = mock.MagicMock()
        self.mock_creds.valid = True
        self.mock_creds.expired = False
        
        # Set up mock service
        self.mock_service = mock.MagicMock()
        self.mock_build = mock.patch('google_chat.build', return_value=self.mock_service).start()
        
        # Mock get_credentials function
        self.get_credentials_patcher = mock.patch(
            'google_chat.get_credentials', 
            return_value=self.mock_creds
        )
        self.mock_get_credentials = self.get_credentials_patcher.start()
        
        # Test data
        self.test_space_name = "spaces/test_space"
        self.test_file_path = "test_file.txt"
        self.test_file_content = "Test file content"
        self.test_message_text = "Test message text"
        
    def tearDown(self):
        """Tear down test fixtures"""
        # Stop all patches
        mock.patch.stopall()
        
        # Remove test file if it exists
        test_file = Path(self.test_file_path)
        if test_file.exists():
            test_file.unlink()
    
    @mock.patch('google_chat.MediaFileUpload')
    def test_upload_attachment(self, mock_media_upload):
        """Test uploading a file attachment"""
        # Create a mock file
        with open(self.test_file_path, 'w') as f:
            f.write(self.test_file_content)
            
        # Mock media upload and service responses
        mock_media = mock.MagicMock()
        mock_media_upload.return_value = mock_media
        
        # Mock upload response
        mock_upload_response = {"name": "media/test_upload"}
        self.mock_service.media().upload.return_value.execute.return_value = mock_upload_response
        
        # Mock message creation response
        mock_message_response = {"name": "spaces/test_space/messages/test_message"}
        self.mock_service.spaces().messages().create.return_value.execute.return_value = mock_message_response
        
        # Run the coroutine
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            google_chat.upload_attachment(self.test_space_name, self.test_file_path, self.test_message_text)
        )
        
        # Check results
        self.assertEqual(result, mock_message_response)
        
        # Verify mocks were called correctly
        mock_media_upload.assert_called_once()
        self.mock_service.media().upload.assert_called_once()
        self.mock_service.spaces().messages().create.assert_called_once()
    
    @mock.patch('google_chat.create_message')
    def test_send_file_message(self, mock_create_message):
        """Test sending a file message"""
        # Create a mock file
        with open(self.test_file_path, 'w') as f:
            f.write(self.test_file_content)
            
        # Mock create_message response
        mock_response = {"name": "spaces/test_space/messages/test_message"}
        mock_create_message.return_value = mock_response
        
        # Run the coroutine
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            google_chat.send_file_message(self.test_space_name, self.test_file_path, self.test_message_text)
        )
        
        # Check results
        self.assertEqual(result, mock_response)
        
        # Verify mock was called
        mock_create_message.assert_called_once()
        
        # Verify the message contains the file content
        call_args = mock_create_message.call_args[0]
        self.assertEqual(call_args[0], self.test_space_name)
        self.assertIn(self.test_message_text, call_args[1])
        self.assertIn(self.test_file_content, call_args[1])
    
    @mock.patch('google_chat.create_message')
    def test_send_file_message_file_not_found(self, mock_create_message):
        """Test sending a file message with nonexistent file"""
        # Test with a file that doesn't exist
        nonexistent_file = "nonexistent_file.txt"
        
        # Run the coroutine and expect Exception that wraps FileNotFoundError
        loop = asyncio.get_event_loop()
        with self.assertRaises(Exception) as context:
            loop.run_until_complete(
                google_chat.send_file_message(self.test_space_name, nonexistent_file)
            )
        
        # Verify the error message contains 'File not found'
        self.assertIn("File not found", str(context.exception))
        
        # Verify mock was not called
        mock_create_message.assert_not_called()
    
    @mock.patch('google_chat.create_message')
    def test_send_file_message_binary_file(self, mock_create_message):
        """Test sending a file message with binary file (that can't be read as text)"""
        # Mock reading binary file to raise UnicodeDecodeError
        with mock.patch('builtins.open') as mock_open:
            mock_open.return_value.__enter__.return_value.read.side_effect = UnicodeDecodeError(
                'utf-8', b'binary data', 0, 1, 'invalid byte'
            )
            
            # Mock Path.exists to return True
            with mock.patch('pathlib.Path.exists', return_value=True):
                # Mock response
                mock_response = {"name": "spaces/test_space/messages/test_message"}
                mock_create_message.return_value = mock_response
                
                # Run the coroutine
                loop = asyncio.get_event_loop()
                result = loop.run_until_complete(
                    google_chat.send_file_message(self.test_space_name, "binary_file.bin")
                )
                
                # Check results
                self.assertEqual(result, mock_response)
                
                # Verify mock was called and message indicates binary file
                mock_create_message.assert_called_once()
                call_args = mock_create_message.call_args[0]
                self.assertIn("Binary file content not shown", call_args[1])

if __name__ == '__main__':
    unittest.main() 