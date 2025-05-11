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

class TestMessaging(unittest.TestCase):
    """Test messaging functions in google_chat.py"""
    
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
        
        # Test space and message data
        self.test_space_name = "spaces/test_space"
        self.test_message_text = "Test message"
        self.test_message_name = "spaces/test_space/messages/test_message"
        self.test_thread_key = "test_thread"
        
    def tearDown(self):
        """Tear down test fixtures"""
        # Stop all patches
        mock.patch.stopall()
    
    def test_create_message(self):
        """Test creating a message in a space"""
        # Mock the spaces().messages().create().execute()
        mock_execute = mock.MagicMock(return_value={"name": self.test_message_name})
        self.mock_service.spaces().messages().create.return_value.execute = mock_execute
        
        # Run the coroutine
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            google_chat.create_message(self.test_space_name, self.test_message_text)
        )
        
        # Check results
        self.assertEqual(result, {"name": self.test_message_name})
        
        # Verify mocks were called correctly
        self.mock_get_credentials.assert_called_once()
        self.mock_build.assert_called_once_with('chat', 'v1', credentials=self.mock_creds)
        self.mock_service.spaces().messages().create.assert_called_once_with(
            parent=self.test_space_name,
            body={"text": self.test_message_text}
        )
        mock_execute.assert_called_once()
    
    def test_update_message(self):
        """Test updating a message"""
        # Mock the spaces().messages().patch().execute()
        mock_execute = mock.MagicMock(return_value={"name": self.test_message_name, "text": "Updated message"})
        self.mock_service.spaces().messages().patch.return_value.execute = mock_execute
        
        # Run the coroutine
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            google_chat.update_message(self.test_message_name, "Updated message")
        )
        
        # Check results
        self.assertEqual(result, {"name": self.test_message_name, "text": "Updated message"})
        
        # Verify mocks were called correctly
        self.mock_service.spaces().messages().patch.assert_called_once_with(
            name=self.test_message_name,
            updateMask="text",
            body={"name": self.test_message_name, "text": "Updated message"}
        )
        mock_execute.assert_called_once()
    
    def test_reply_to_thread(self):
        """Test replying to a thread"""
        # Mock the spaces().messages().create().execute()
        mock_execute = mock.MagicMock(return_value={"name": self.test_message_name})
        self.mock_service.spaces().messages().create.return_value.execute = mock_execute
        
        # Run the coroutine
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            google_chat.reply_to_thread(self.test_space_name, self.test_thread_key, self.test_message_text)
        )
        
        # Check results
        self.assertEqual(result, {"name": self.test_message_name})
        
        # Verify mocks were called correctly
        self.mock_service.spaces().messages().create.assert_called_once_with(
            parent=self.test_space_name,
            messageReplyOption="REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD",
            body={
                "text": self.test_message_text,
                "thread": {"threadKey": self.test_thread_key}
            }
        )
        mock_execute.assert_called_once()
    
    def test_get_message(self):
        """Test getting a message by name"""
        # Mock response
        mock_response = {"name": self.test_message_name, "text": self.test_message_text}
        mock_execute = mock.MagicMock(return_value=mock_response)
        self.mock_service.spaces().messages().get.return_value.execute = mock_execute
        
        # Run the coroutine
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            google_chat.get_message(self.test_message_name)
        )
        
        # Check results
        self.assertEqual(result, mock_response)
        
        # Verify mocks were called correctly
        self.mock_service.spaces().messages().get.assert_called_once_with(name=self.test_message_name)
        mock_execute.assert_called_once()
    
    def test_delete_message(self):
        """Test deleting a message"""
        # Mock response
        mock_execute = mock.MagicMock(return_value={})
        self.mock_service.spaces().messages().delete.return_value.execute = mock_execute
        
        # Run the coroutine
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            google_chat.delete_message(self.test_message_name)
        )
        
        # Check results
        self.assertEqual(result, {})
        
        # Verify mocks were called correctly
        self.mock_service.spaces().messages().delete.assert_called_once_with(name=self.test_message_name)
        mock_execute.assert_called_once()
    
    def test_add_emoji_reaction(self):
        """Test adding an emoji reaction to a message"""
        # Mock response
        mock_response = {"name": f"{self.test_message_name}/reactions/123"}
        mock_execute = mock.MagicMock(return_value=mock_response)
        self.mock_service.spaces().messages().reactions().create.return_value.execute = mock_execute
        
        # Run the coroutine
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            google_chat.add_emoji_reaction(self.test_message_name, "👍")
        )
        
        # Check results
        self.assertEqual(result, mock_response)
        
        # Verify mocks were called correctly
        self.mock_service.spaces().messages().reactions().create.assert_called_once_with(
            parent=self.test_message_name,
            body={"emoji": {"unicode": "👍"}}
        )
        mock_execute.assert_called_once()

if __name__ == '__main__':
    unittest.main() 