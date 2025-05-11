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

class TestUserInfo(unittest.TestCase):
    """Test user info and mentions functions in google_chat.py"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock credentials
        self.mock_creds = mock.MagicMock()
        self.mock_creds.valid = True
        self.mock_creds.expired = False
        
        # Set up mock service for Chat API
        self.mock_chat_service = mock.MagicMock()
        
        # Set up mock service for People API
        self.mock_people_service = mock.MagicMock()
        
        # Mock the build function to return different mock services based on the service name
        def mock_build_side_effect(service_name, version, credentials):
            if service_name == 'chat':
                return self.mock_chat_service
            elif service_name == 'people':
                return self.mock_people_service
            return mock.MagicMock()
            
        self.mock_build = mock.patch(
            'google_chat.build', 
            side_effect=mock_build_side_effect
        ).start()
        
        # Mock get_credentials function
        self.get_credentials_patcher = mock.patch(
            'google_chat.get_credentials', 
            return_value=self.mock_creds
        )
        self.mock_get_credentials = self.get_credentials_patcher.start()
        
        # Test data
        self.test_space_name = "spaces/test_space"
        self.test_user_info = {
            "email": "test@example.com",
            "display_name": "Test User",
            "given_name": "Test",
            "family_name": "User"
        }
        self.test_message_with_mention = {
            "name": "spaces/test_space/messages/test_message",
            "text": "Hey @Test User, check this out",
            "createTime": "2023-01-01T12:00:00Z"
        }
        self.test_message_without_mention = {
            "name": "spaces/test_space/messages/test_message2",
            "text": "This is a message without mentions",
            "createTime": "2023-01-01T12:00:00Z"
        }
        
    def tearDown(self):
        """Tear down test fixtures"""
        # Stop all patches
        mock.patch.stopall()
    
    def test_get_current_user_info(self):
        """Test getting current user info"""
        # Mock the People API responses
        mock_profile = {
            "names": [
                {
                    "displayName": self.test_user_info["display_name"],
                    "givenName": self.test_user_info["given_name"],
                    "familyName": self.test_user_info["family_name"]
                }
            ],
            "emailAddresses": [
                {
                    "value": self.test_user_info["email"]
                }
            ]
        }
        mock_execute = mock.MagicMock(return_value=mock_profile)
        self.mock_people_service.people().get.return_value.execute = mock_execute
        
        # Create and use a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                google_chat.get_current_user_info()
            )
        finally:
            loop.close()
            asyncio.set_event_loop(None)
        
        # Check results
        self.assertEqual(result, self.test_user_info)
        
        # Verify mocks were called correctly
        self.mock_get_credentials.assert_called_once()
        self.mock_build.assert_called_with('people', 'v1', credentials=self.mock_creds)
        self.mock_people_service.people().get.assert_called_once_with(
            resourceName='people/me',
            personFields='names,emailAddresses'
        )
        mock_execute.assert_called_once()
    
    @mock.patch('google_chat.get_current_user_info')
    @mock.patch('google_chat.list_chat_spaces')
    @mock.patch('google_chat.list_space_messages')
    def test_get_user_mentions(self, mock_list_messages, mock_list_spaces, mock_get_user_info):
        """Test getting user mentions"""
        # Mock user info
        mock_get_user_info.return_value = self.test_user_info
        
        # Mock list_chat_spaces to return one space
        mock_list_spaces.return_value = [{"name": self.test_space_name}]
        
        # Mock list_space_messages to return one message with mention and one without
        mock_list_messages.return_value = [
            self.test_message_with_mention,
            self.test_message_without_mention
        ]
        
        # Mock spaces().get().execute() to get space details
        mock_space_details = {"displayName": "Test Space"}
        mock_execute = mock.MagicMock(return_value=mock_space_details)
        self.mock_chat_service.spaces().get.return_value.execute = mock_execute
        
        # Create and use a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                google_chat.get_user_mentions(days=7)
            )
        finally:
            loop.close()
            asyncio.set_event_loop(None)
        
        # Check results - should only include the message with mention
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], self.test_message_with_mention["name"])
        self.assertEqual(result[0]["space_info"]["name"], self.test_space_name)
        self.assertEqual(result[0]["space_info"]["displayName"], "Test Space")
        
        # Verify mocks were called correctly
        mock_get_user_info.assert_called_once()
        mock_list_spaces.assert_called_once()
        self.assertEqual(mock_list_messages.call_count, 1)
        self.mock_chat_service.spaces().get.assert_called_once_with(name=self.test_space_name)
    
    @mock.patch('google_chat.get_current_user_info')
    @mock.patch('google_chat.list_space_messages')
    def test_get_user_mentions_with_space_id(self, mock_list_messages, mock_get_user_info):
        """Test getting user mentions with specific space ID"""
        # Mock user info
        mock_get_user_info.return_value = self.test_user_info
        
        # Mock list_space_messages to return one message with mention and one without
        mock_list_messages.return_value = [
            self.test_message_with_mention,
            self.test_message_without_mention
        ]
        
        # Mock spaces().get().execute() to get space details
        mock_space_details = {"displayName": "Test Space"}
        mock_execute = mock.MagicMock(return_value=mock_space_details)
        self.mock_chat_service.spaces().get.return_value.execute = mock_execute
        
        # Create and use a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                google_chat.get_user_mentions(days=7, space_id=self.test_space_name)
            )
        finally:
            loop.close()
            asyncio.set_event_loop(None)
        
        # Check results - should only include the message with mention
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], self.test_message_with_mention["name"])
        
        # Verify mocks - list_chat_spaces should not be called when space_id is provided
        mock_get_user_info.assert_called_once()
        mock_list_messages.assert_called_once()
        self.mock_chat_service.spaces().get.assert_called_once_with(name=self.test_space_name)

if __name__ == '__main__':
    unittest.main() 