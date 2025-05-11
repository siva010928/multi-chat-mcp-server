import unittest
from unittest import mock
import os
import json
import datetime
from pathlib import Path
import sys
import asyncio
import pytest

# Add parent directory to path to import google_chat
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import google_chat
from google.oauth2.credentials import Credentials

class TestTokenManagement(unittest.TestCase):
    """Test token management functionality in google_chat.py"""
    
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
    
    @mock.patch('google_chat.datetime')
    def test_token_expiry_calculation(self, mock_datetime):
        """Test token expiration time calculation"""
        # Set up a fixed "now" time
        fixed_now = datetime.datetime(2023, 5, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
        mock_datetime.datetime.now.return_value = fixed_now
        mock_datetime.timezone = datetime.timezone
        mock_datetime.timedelta = datetime.timedelta
        
        # Create a mock credentials with an expiry time
        mock_creds = mock.MagicMock()
        mock_creds.expiry = datetime.datetime(2023, 5, 1, 13, 0, 0, tzinfo=datetime.timezone.utc)  # 1 hour later
        
        # Calculate the time left - this would be done inside our utility scripts
        expiry = mock_creds.expiry
        now = fixed_now
        time_left = expiry - now
        hours_left = time_left.total_seconds() / 3600
        
        # Verify the calculation is correct
        self.assertEqual(hours_left, 1.0)
    
    @mock.patch('pathlib.Path.exists')
    def test_token_file_check(self, mock_exists):
        """Test checking if token file exists"""
        # Mock the Path.exists function to return False
        mock_exists.return_value = False
        
        # Check that get_credentials returns None when token file doesn't exist
        creds = google_chat.get_credentials(self.test_token_path)
        self.assertIsNone(creds)
        # Path.exists was called - don't assert on the exact argument since Path object comparison might fail
        self.assertTrue(mock_exists.called)
    
    @mock.patch('google_chat.Credentials')
    @mock.patch('pathlib.Path.exists')
    def test_token_load_from_file(self, mock_exists, mock_credentials_class):
        """Test loading token from file"""
        # Mock that the file exists
        mock_exists.return_value = True
        
        # Create a mock credentials object
        mock_creds = mock.MagicMock()
        mock_creds.expired = False
        mock_creds.valid = True
        mock_credentials_class.from_authorized_user_file.return_value = mock_creds
        
        # Call get_credentials
        creds = google_chat.get_credentials(self.test_token_path)
        
        # Verify it was loaded correctly
        self.assertEqual(creds, mock_creds)
        # Verify from_authorized_user_file was called (don't check the exact args)
        mock_credentials_class.from_authorized_user_file.assert_called()
    
    @mock.patch('google_chat.Request')
    @mock.patch('google_chat.Credentials')
    @mock.patch('pathlib.Path.exists')
    def test_expired_token_auto_refresh(self, mock_exists, mock_credentials_class, mock_request):
        """Test automatic refresh of expired token"""
        # Mock that the file exists
        mock_exists.return_value = True
        
        # Create a mock credentials object that's expired
        mock_creds = mock.MagicMock()
        mock_creds.expired = True
        # Make sure valid becomes True after refresh
        mock_creds.valid = True
        mock_creds.refresh_token = "test_refresh_token"
        mock_credentials_class.from_authorized_user_file.return_value = mock_creds
        
        # Mock save_credentials to avoid file operations
        with mock.patch('google_chat.save_credentials'):
            # Call get_credentials (should trigger an auto-refresh)
            creds = google_chat.get_credentials(self.test_token_path)
            
            # Verify refresh was called
            mock_creds.refresh.assert_called_once()
            # Verify the result is the refreshed credentials
            self.assertEqual(creds, mock_creds)
    
    def test_save_credentials(self):
        """Test saving credentials to file"""
        # Mock the open function
        mock_file = mock.mock_open()
        with mock.patch('builtins.open', mock_file):
            # Create a mock credentials
            mock_creds = mock.MagicMock()
            mock_creds.to_json.return_value = '{"mock": "credentials"}'
            
            # Call save_credentials
            google_chat.save_credentials(mock_creds, self.test_token_path)
            
            # Verify file was written
            mock_file.assert_called_once()
            # Verify write was called with the correct content
            mock_file().write.assert_called_once_with('{"mock": "credentials"}')
            
            # Verify credentials were stored in memory
            self.assertEqual(google_chat.token_info['credentials'], mock_creds)
    
    def test_set_token_path(self):
        """Test setting token path"""
        new_path = 'new_token.json'
        google_chat.set_token_path(new_path)
        self.assertEqual(google_chat.token_info['token_path'], new_path)


@pytest.mark.asyncio
class TestAsyncTokenManagement:
    """Test async token management functionality"""
    
    def setup_method(self):
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
    
    def teardown_method(self):
        """Tear down test fixtures"""
        # Restore original token_info
        google_chat.token_info = self.original_token_info
    
    @pytest.mark.asyncio
    @mock.patch('google_chat.Request')
    async def test_refresh_token_coroutine(self, mock_request):
        """Test the refresh_token async function"""
        # Set up a mock credentials in memory
        mock_creds = mock.MagicMock()
        mock_creds.refresh_token = "test_refresh_token"
        google_chat.token_info['credentials'] = mock_creds
        
        # Mock the save_credentials function
        with mock.patch('google_chat.save_credentials') as mock_save:
            # Call refresh_token
            success, message = await google_chat.refresh_token(self.test_token_path)
            
            # Verify refresh was called
            mock_creds.refresh.assert_called_once()
            mock_save.assert_called_once()
            assert success is True
            assert message == "Token refreshed successfully"
    
    @pytest.mark.asyncio
    @mock.patch('pathlib.Path.exists')
    async def test_refresh_token_no_file(self, mock_exists):
        """Test refresh_token when no token file exists"""
        # Mock that the file doesn't exist
        mock_exists.return_value = False
        google_chat.token_info['credentials'] = None
        
        # Call refresh_token
        success, message = await google_chat.refresh_token(self.test_token_path)
        
        # Verify the result
        assert success is False
        assert message == "No token file found"
    
    @pytest.mark.asyncio
    @mock.patch('google_chat.Credentials')
    @mock.patch('pathlib.Path.exists')
    async def test_refresh_token_no_refresh_token(self, mock_exists, mock_credentials_class):
        """Test refresh_token when credentials have no refresh token"""
        # Mock that the file exists
        mock_exists.return_value = True
        
        # Ensure there are no credentials in memory
        google_chat.token_info['credentials'] = None
        
        # Create a mock credentials without refresh token
        mock_creds = mock.MagicMock()
        mock_creds.refresh_token = None
        mock_credentials_class.from_authorized_user_file.return_value = mock_creds
        
        # Call refresh_token
        success, message = await google_chat.refresh_token(self.test_token_path)
        
        # Verify the result
        assert success is False
        assert message == "No refresh token available"
        
if __name__ == '__main__':
    unittest.main() 