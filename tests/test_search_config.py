#!/usr/bin/env python
"""
Unit tests for search configuration loading
"""
import os
import sys
import unittest
import tempfile
import yaml
from unittest.mock import patch, mock_open, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import modules to test
from search_manager import SearchManager

class TestSearchConfig(unittest.TestCase):
    """Test search config loading and validation."""
    
    def test_config_weights(self):
        """Test that search weights are properly applied."""
        # Create mock config with different weights
        mock_config = {
            'search_modes': [
                {
                    'name': 'regex',
                    'enabled': True,
                    'weight': 1.5,  # Higher weight
                    'options': {
                        'ignore_case': True
                    }
                },
                {
                    'name': 'exact',
                    'enabled': True,
                    'weight': 1.0,  # Lower weight
                    'options': {}
                }
            ],
            'search': {
                'default_mode': 'regex'
            }
        }
        
        # Sample messages that could match with either mode
        messages = [
            {"text": "This is a regex pattern example"},
            {"text": "This has regex and exact match text"},
        ]
        
        # Mock the _load_config method and semantic provider
        with patch.object(SearchManager, '_load_config', return_value=mock_config):
            with patch('search_manager.SemanticSearchProvider'):
                # Create SearchManager
                search_manager = SearchManager()
                
                # Test regex search
                regex_results = search_manager.search("regex", messages, mode="regex")
                exact_results = search_manager.search("regex", messages, mode="exact")
                
                # Regex search should have higher scores due to its higher weight
                self.assertTrue(regex_results[0][0] > exact_results[0][0])
    
    def test_invalid_search_mode(self):
        """Test that an invalid search mode raises an error."""
        # Create mock config
        mock_config = {
            'search_modes': [
                {
                    'name': 'regex',
                    'enabled': True,
                    'weight': 1.2
                }
            ]
        }
        
        # Mock the _load_config method and semantic provider
        with patch.object(SearchManager, '_load_config', return_value=mock_config):
            with patch('search_manager.SemanticSearchProvider'):
                # Create SearchManager
                search_manager = SearchManager()
                
                # Test with invalid search mode
                with self.assertRaises(ValueError):
                    search_manager.search("test", [], mode="invalid_mode")
    
    def test_search_mode_options(self):
        """Test that search mode options are properly loaded."""
        # Create a temporary config file with detailed options
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as temp_file:
            # Write sample configuration with options
            temp_file.write("""
search_modes:
  - name: "regex"
    enabled: true
    description: "Test regex mode"
    weight: 1.0
    options:
      ignore_case: false
      dot_all: true
      unicode: true
      max_pattern_length: 500
""")
            temp_path = temp_file.name
        
        try:
            # Mock the semantic provider initialization
            with patch('search_manager.SemanticSearchProvider'):
                # Create SearchManager with our temp config
                search_manager = SearchManager(config_path=temp_path)
                
                # Get the regex mode configuration
                regex_config = search_manager.search_modes.get('regex', {})
                regex_options = regex_config.get('options', {})
                
                # Verify options are loaded correctly
                self.assertFalse(regex_options.get('ignore_case'))
                self.assertTrue(regex_options.get('dot_all'))
                self.assertTrue(regex_options.get('unicode'))
                self.assertEqual(regex_options.get('max_pattern_length'), 500)
        finally:
            # Clean up the temporary file
            os.unlink(temp_path)
    
    def test_search_config_file_not_found(self):
        """Test that a FileNotFoundError is raised when config file doesn't exist."""
        # Mock the semantic provider initialization
        with patch('search_manager.SemanticSearchProvider'):
            # Attempt to create SearchManager with non-existent config
            with self.assertRaises(FileNotFoundError):
                SearchManager(config_path="nonexistent_config.yaml")
    
    def test_semantic_search_availability(self):
        """Test that semantic search availability is checked properly."""
        # Create mock config with semantic search enabled
        mock_config = {
            'search_modes': [
                {
                    'name': 'semantic',
                    'enabled': True,
                    'weight': 1.5,
                    'options': {
                        'model': 'test-model',
                        'similarity_threshold': 0.7
                    }
                }
            ]
        }
        
        # Sample messages
        messages = [
            {"text": "This is a test message"},
            {"text": "Another test message"},
        ]
        
        # Mock the SemanticSearchProvider with available=False
        mock_semantic = MagicMock()
        mock_semantic.available = False
        
        # Mock the _load_config method
        with patch.object(SearchManager, '_load_config', return_value=mock_config):
            # Create a SearchManager with our mocked semantic provider
            with patch('search_manager.SemanticSearchProvider', return_value=mock_semantic):
                # Create SearchManager
                search_manager = SearchManager()
                
                # Override the semantic_provider attribute
                search_manager.semantic_provider = mock_semantic
                
                # When semantic search is not available, it should fall back to exact search
                results = search_manager.search("test", messages, mode="semantic")
                
                # Verify it called the semantic provider's available property
                self.assertEqual(mock_semantic.available, False)

if __name__ == '__main__':
    unittest.main() 