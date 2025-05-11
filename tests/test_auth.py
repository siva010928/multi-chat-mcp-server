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

class TestAuthentication(unittest.TestCase):
    """Test authentication functions in google_chat.py"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a mock token file path
        self.test_token_path = 'test_token.json'
        
        # Save the original token_info
        self.original_token_info = google_chat.token_info.copy()
        
        # Reset token_info for testing
        google_chat.token_info = {
            'credentials': None,
            'last_refresh': None,
            'token_path': self.test_token_path
        }
        
    def tearDown(self):
        """Tear down test fixtures"""
        # Restore original token_info
        google_chat.token_info = self.original_token_info
        
        # Remove test token file if it exists
        test_token = Path(self.test_token_path)
        if test_token.exists():
            test_token.unlink()
    
    def test_set_token_path(self):
        """Test setting token path"""
        new_path = 'new_token.json'
        google_chat.set_token_path(new_path)
        self.assertEqual(google_chat.token_info['token_path'], new_path)
    
    @mock.patch('google_chat.Credentials')
    def test_save_credentials(self, mock_creds):
        """Test saving credentials to file"""
        # Create a mock credentials object
        mock_creds.to_json.return_value = '{"mock": "credentials"}'
        
        # Call the function under test
        google_chat.save_credentials(mock_creds, self.test_token_path)
        
        # Check if file was created
        token_file = Path(self.test_token_path)
        self.assertTrue(token_file.exists())
        
        # Check if credentials were saved in memory
        self.assertEqual(google_chat.token_info['credentials'], mock_creds)
        self.assertIsNotNone(google_chat.token_info['last_refresh'])
    
    def test_get_credentials_from_file(self):
        """Test getting credentials from file"""
        # Create a mock credentials object
        mock_creds = mock.MagicMock()
        mock_creds.expired = False
        mock_creds.valid = True
        
        # Setup our test scenario
        with mock.patch('pathlib.Path.exists', return_value=True) as mock_exists, \
             mock.patch('google_chat.Credentials.from_authorized_user_file', 
                        return_value=mock_creds) as mock_from_file:
            
            # Call the function under test
            creds = google_chat.get_credentials(self.test_token_path)
            
            # Check if credentials were loaded
            self.assertEqual(creds, mock_creds)
            self.assertEqual(google_chat.token_info['credentials'], mock_creds)
            
            # Verify the mock was called with correct parameters
            mock_exists.assert_called()
            mock_from_file.assert_called_once_with(self.test_token_path, google_chat.SCOPES)
    
    def test_get_credentials_expired_auto_refresh(self):
        """Test getting credentials that need refresh"""
        # Create a mock credentials object that's expired but has a refresh token
        mock_creds = mock.MagicMock()
        mock_creds.expired = True
        mock_creds.valid = False
        mock_creds.refresh_token = "test_refresh_token"
        
        # Setup our test scenario
        with mock.patch('pathlib.Path.exists', return_value=True) as mock_exists, \
             mock.patch('google_chat.Credentials.from_authorized_user_file', 
                        return_value=mock_creds) as mock_from_file, \
             mock.patch('google_chat.Request') as mock_request, \
             mock.patch('google_chat.save_credentials') as mock_save:
            
            # After refresh, the credentials should be valid
            mock_creds.valid = True
            
            # Call the function under test
            creds = google_chat.get_credentials(self.test_token_path)
            
            # Check if credentials were refreshed
            self.assertEqual(creds, mock_creds)
            mock_creds.refresh.assert_called_once_with(mock_request.return_value)
            mock_save.assert_called_once()
    
    def test_get_credentials_no_file(self):
        """Test getting credentials when file doesn't exist"""
        # Setup our test scenario
        with mock.patch('pathlib.Path.exists', return_value=False) as mock_exists:
            
            # Call the function under test
            creds = google_chat.get_credentials(self.test_token_path)
            
            # Should return None if file doesn't exist
            self.assertIsNone(creds)
            mock_exists.assert_called()
    
    @mock.patch('google_chat.Credentials')
    @mock.patch('google_chat.Request')
    def test_refresh_token(self, mock_request, mock_creds):
        """Test refreshing token"""
        # Setup the mock
        mock_credential = mock.MagicMock()
        mock_credential.refresh_token = "refresh_token"
        google_chat.token_info['credentials'] = mock_credential
        
        # We need to patch the save_credentials function to avoid file operations
        with mock.patch('google_chat.save_credentials') as mock_save:
            # Use asyncio to run the coroutine
            loop = asyncio.get_event_loop()
            success, message = loop.run_until_complete(
                google_chat.refresh_token(self.test_token_path)
            )
            
            # Check if refresh was successful
            self.assertTrue(success)
            self.assertEqual(message, "Token refreshed successfully")
            
            # Verify the mocks were called
            mock_credential.refresh.assert_called_once_with(mock_request.return_value)
            mock_save.assert_called_once_with(mock_credential, self.test_token_path)
    
    @mock.patch('google_chat.Credentials.from_authorized_user_file')
    @mock.patch('pathlib.Path.exists')
    def test_refresh_token_no_token(self, mock_exists, mock_from_file):
        """Test refreshing token when no token exists"""
        # No credentials in memory
        google_chat.token_info['credentials'] = None
        # No token file
        mock_exists.return_value = False
        
        # Use asyncio to run the coroutine
        loop = asyncio.get_event_loop()
        success, message = loop.run_until_complete(
            google_chat.refresh_token(self.test_token_path)
        )
        
        # Check result is failure
        self.assertFalse(success)
        self.assertEqual(message, "No token file found")
    
    @mock.patch('google_chat.Credentials.from_authorized_user_file')
    @mock.patch('pathlib.Path.exists')
    def test_refresh_token_no_refresh_token(self, mock_exists, mock_from_file):
        """Test refreshing token when no refresh token available"""
        # No credentials in memory
        google_chat.token_info['credentials'] = None
        # Token file exists
        mock_exists.return_value = True
        
        # Create mock credentials with no refresh token
        mock_creds = mock.MagicMock()
        mock_creds.refresh_token = None
        mock_from_file.return_value = mock_creds
        
        # Use asyncio to run the coroutine
        loop = asyncio.get_event_loop()
        success, message = loop.run_until_complete(
            google_chat.refresh_token(self.test_token_path)
        )
        
        # Check result is failure
        self.assertFalse(success)
        self.assertEqual(message, "No refresh token available")
    
    @mock.patch('google_chat.Credentials.from_authorized_user_file')
    @mock.patch('google_chat.Request')
    @mock.patch('pathlib.Path.exists')
    def test_refresh_token_exception(self, mock_exists, mock_request, mock_from_file):
        """Test refreshing token with exception during refresh"""
        # No credentials in memory
        google_chat.token_info['credentials'] = None
        # Token file exists
        mock_exists.return_value = True
        
        # Create mock credentials
        mock_creds = mock.MagicMock()
        mock_creds.refresh_token = "mock_refresh_token"
        mock_from_file.return_value = mock_creds
        
        # Make refresh raise an exception
        mock_creds.refresh.side_effect = Exception("Refresh failed")
        
        # Use asyncio to run the coroutine
        loop = asyncio.get_event_loop()
        success, message = loop.run_until_complete(
            google_chat.refresh_token(self.test_token_path)
        )
        
        # Check result is failure
        self.assertFalse(success)
        self.assertEqual(message, "Failed to refresh token: Refresh failed")

if __name__ == '__main__':
    unittest.main() 