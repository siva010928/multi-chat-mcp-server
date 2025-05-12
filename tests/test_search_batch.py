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

class TestSearchBatchOperations(unittest.TestCase):
    """Test search and batch operations in google_chat.py"""
    
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
        self.test_message_name = "spaces/test_space/messages/test_message"
        self.test_query = "test query"
        self.test_messages = [
            {
                "name": "spaces/test_space/messages/msg1",
                "text": "This is a test query result",
                "createTime": "2023-01-01T12:00:00Z"
            },
            {
                "name": "spaces/test_space/messages/msg2",
                "text": "Another test query match",
                "createTime": "2023-01-02T12:00:00Z"
            }
        ]
        
    def tearDown(self):
        """Tear down test fixtures"""
        # Stop all patches
        mock.patch.stopall()
    
    @mock.patch('google_chat.list_chat_spaces')
    @mock.patch('google_chat.list_space_messages')
    def test_search_messages(self, mock_list_messages, mock_list_spaces):
        """Test searching messages across spaces"""
        # Mock list_chat_spaces to return one space
        mock_list_spaces.return_value = [{"name": self.test_space_name}]
        
        # Mock list_space_messages to return test messages with the new dict format
        mock_list_messages.return_value = {
            "messages": self.test_messages,
            "nextPageToken": None
        }
        
        # Run the coroutine
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            google_chat.search_messages(self.test_query)
        )
        
        # Check results - result now contains a dict with 'messages' key
        self.assertIn('messages', result)
        messages = result['messages']
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["name"], self.test_messages[0]["name"])
        self.assertEqual(messages[1]["name"], self.test_messages[1]["name"])
        self.assertEqual(messages[0]["space_info"]["name"], self.test_space_name)
        
        # Verify mocks were called correctly
        mock_list_spaces.assert_called_once()
        self.assertEqual(mock_list_messages.call_count, 1)
    
    @mock.patch('google_chat.list_space_messages')
    def test_search_messages_with_spaces(self, mock_list_messages):
        """Test searching messages in specific spaces"""
        # Mock list_space_messages to return test messages with the new dict format
        mock_list_messages.return_value = {
            "messages": self.test_messages,
            "nextPageToken": None
        }
        
        # Test spaces to search
        test_spaces = [self.test_space_name]
        
        # Run the coroutine
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            google_chat.search_messages(self.test_query, spaces=test_spaces)
        )
        
        # Check results - result now contains a dict with 'messages' key
        self.assertIn('messages', result)
        messages = result['messages']
        self.assertEqual(len(messages), 2)
        
        # Verify mock was called with the provided space
        mock_list_messages.assert_called_once()
    
    @mock.patch('google_chat.reply_to_thread')
    @mock.patch('google_chat.create_message')
    def test_batch_send_messages(self, mock_create_message, mock_reply_to_thread):
        """Test batch sending messages"""
        # Mock responses for create_message and reply_to_thread
        create_response = {"name": "spaces/test_space/messages/new1"}
        reply_response = {"name": "spaces/test_space/messages/reply1"}
        
        mock_create_message.return_value = create_response
        mock_reply_to_thread.return_value = reply_response
        
        # Test batch messages
        batch_messages = [
            {
                "space_name": self.test_space_name,
                "text": "Regular message"
            },
            {
                "space_name": self.test_space_name,
                "text": "Thread reply",
                "thread_key": "thread1"
            }
        ]
        
        # Run the coroutine
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            google_chat.batch_send_messages(batch_messages)
        )
        
        # Check results
        self.assertEqual(len(result["successful"]), 2)
        self.assertEqual(len(result["failed"]), 0)
        
        # Verify mocks were called correctly
        mock_create_message.assert_called_once_with(self.test_space_name, "Regular message", None)
        mock_reply_to_thread.assert_called_once_with(self.test_space_name, "thread1", "Thread reply", None)
    
    def test_batch_send_messages_with_errors(self):
        """Test batch sending messages with some errors"""
        # Mock create_message to succeed and reply_to_thread to fail
        async def mock_create_message_success(space_name, text, cards_v2=None):
            return {"name": "spaces/test_space/messages/success"}
            
        async def mock_reply_thread_fail(space_name, thread_key, text, cards_v2=None):
            raise Exception("Thread key not found")
        
        # Set up the patches
        mock_create = mock.patch('google_chat.create_message', side_effect=mock_create_message_success).start()
        mock_reply = mock.patch('google_chat.reply_to_thread', side_effect=mock_reply_thread_fail).start()
        
        # Test batch messages - one should succeed, one should fail
        batch_messages = [
            {
                "space_name": self.test_space_name,
                "text": "Regular message"
            },
            {
                "space_name": self.test_space_name,
                "text": "Thread reply",
                "thread_key": "invalid_thread"
            }
        ]
        
        # Run the coroutine
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            google_chat.batch_send_messages(batch_messages)
        )
        
        # Check results - should have one success and one failure
        self.assertEqual(len(result["successful"]), 1)
        self.assertEqual(len(result["failed"]), 1)
        self.assertEqual(result["failed"][0]["index"], 1)
        self.assertTrue("Thread key not found" in result["failed"][0]["error"])

if __name__ == '__main__':
    unittest.main() 