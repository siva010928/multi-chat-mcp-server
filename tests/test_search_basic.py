#!/usr/bin/env python
"""
Basic unit tests for search functionality
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

class TestSearchManager(unittest.TestCase):
    """Test search manager functionality."""
    
    def test_default_search_mode(self):
        """Test that the default search mode is properly set to regex."""
        # Create a mock config with regex as the default
        mock_config = {
            'search_modes': [
                {
                    'name': 'regex',
                    'enabled': True,
                    'description': 'Regular expression search',
                    'weight': 1.2
                },
                {
                    'name': 'semantic',
                    'enabled': True,
                    'description': 'Semantic search',
                    'weight': 1.0
                }
            ],
            'search': {
                'default_mode': 'regex'
            }
        }
        
        # Mock the _load_config method to return our mock config and the semantic provider
        with patch.object(SearchManager, '_load_config', return_value=mock_config):
            with patch('search_manager.SemanticSearchProvider') as mock_semantic:
                # Create a SearchManager instance
                search_manager = SearchManager()
                
                # Verify the default mode is regex
                default_mode = search_manager.get_default_mode()
                self.assertEqual(default_mode, 'regex')
    
    def test_search_manager_initialization(self):
        """Test SearchManager initialization and configuration."""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as temp_file:
            # Write sample configuration
            temp_file.write("""
search_modes:
  - name: "regex"
    enabled: true
    description: "Regular expression pattern matching"
    weight: 1.2
    options:
      ignore_case: true
  
  - name: "semantic"
    enabled: false
    description: "Semantic search"
    weight: 1.5

search:
  default_mode: "regex"
""")
            temp_path = temp_file.name
        
        try:
            # Mock the semantic provider initialization
            with patch('search_manager.SemanticSearchProvider'):
                # Create SearchManager with our temp config
                search_manager = SearchManager(config_path=temp_path)
                
                # Verify the config was loaded and processed correctly
                self.assertIn('regex', search_manager.search_modes)
                self.assertNotIn('semantic', search_manager.search_modes)  # Should be excluded because enabled=false
                self.assertEqual(search_manager.get_default_mode(), 'regex')
                
        except FileNotFoundError:
            self.fail(f"SearchManager failed to load config from {temp_path}")
        finally:
            # Clean up the temporary file
            os.unlink(temp_path)
    
    def test_regex_search(self):
        """Test regex search functionality."""
        # Mock config with regex enabled
        mock_config = {
            'search_modes': [
                {
                    'name': 'regex',
                    'enabled': True,
                    'weight': 1.2,
                    'options': {
                        'ignore_case': True
                    }
                }
            ]
        }
        
        # Sample messages for testing
        messages = [
            {"text": "This message contains CICD pipeline info"},
            {"text": "Another message about CI/CD workflow"},
            {"text": "This message is about something else"}
        ]
        
        # Mock the _load_config method and semantic provider
        with patch.object(SearchManager, '_load_config', return_value=mock_config):
            with patch('search_manager.SemanticSearchProvider'):
                # Create SearchManager
                search_manager = SearchManager()
                
                # Perform regex search
                results = search_manager.search("ci[/\\-_ ]?cd|cicd", messages, mode="regex")
                
                # Verify results
                self.assertEqual(len(results), 2)
                # Results should be sorted by score (highest first)
                messages_text = [msg['text'] for _, msg in results]
                self.assertTrue("CICD" in messages_text[0] or "CI/CD" in messages_text[0])
                self.assertTrue("CICD" in messages_text[1] or "CI/CD" in messages_text[1])
    
    def test_exact_search_fallback(self):
        """Test that an invalid regex falls back to exact search."""
        # Mock config with regex enabled
        mock_config = {
            'search_modes': [
                {
                    'name': 'regex',
                    'enabled': True,
                    'weight': 1.2,
                    'options': {
                        'ignore_case': True
                    }
                },
                {
                    'name': 'exact',
                    'enabled': True,
                    'weight': 1.0
                }
            ]
        }
        
        # Sample messages for testing
        messages = [
            {"text": "This message contains CICD pipeline info"},
            {"text": "Another message about CI/CD workflow"},
            {"text": "This message is about something else"}
        ]
        
        # Expected results from exact search
        expected_results = [
            (0.9, messages[0]),  # Higher score for first match
            (0.8, messages[1]),  # Lower score for second match
        ]
        
        # Mock the _load_config method and semantic provider
        with patch.object(SearchManager, '_load_config', return_value=mock_config):
            with patch('search_manager.SemanticSearchProvider'):
                # Create SearchManager
                search_manager = SearchManager()
                
                # Mock the _exact_search method to return our expected results
                with patch.object(search_manager, '_exact_search', return_value=expected_results):
                    # Perform regex search with an invalid regex pattern that should fall back to exact search
                    results = search_manager.search("ci(", messages, mode="regex")
                    
                    # Verify results
                    self.assertEqual(len(results), 2)
                    self.assertEqual(results, expected_results)

    def test_cicd_pattern_matching(self):
        """Test that the CICD regex pattern properly matches different formats."""
        # Mock config with regex enabled
        mock_config = {
            'search_modes': [
                {
                    'name': 'regex',
                    'enabled': True,
                    'weight': 1.2,
                    'options': {
                        'ignore_case': True
                    }
                }
            ]
        }
        
        # Sample messages with various CICD formats
        messages = [
            {"text": "We need to update the CICD pipeline"},
            {"text": "Working on the CI/CD workflow"},
            {"text": "Issues with the CI-CD integration"},
            {"text": "Set up CI_CD for the project"},
            {"text": "CI CD implementation needs testing"},
            {"text": "This message has no relevant content"}
        ]
        
        # Mock the _load_config method and semantic provider
        with patch.object(SearchManager, '_load_config', return_value=mock_config):
            with patch('search_manager.SemanticSearchProvider'):
                # Create SearchManager
                search_manager = SearchManager()
                
                # Perform regex search with pattern to match various CICD formats
                results = search_manager.search("ci[ /\\-_]?cd|cicd", messages, mode="regex")
                
                # Verify all variations are found (5 matches)
                self.assertEqual(len(results), 5)
                
                # Check specific variations
                messages_text = [msg['text'].lower() for _, msg in results]
                self.assertTrue(any("cicd" in text for text in messages_text))
                self.assertTrue(any("ci/cd" in text for text in messages_text))
                self.assertTrue(any("ci-cd" in text for text in messages_text))
                self.assertTrue(any("ci_cd" in text for text in messages_text))
                self.assertTrue(any("ci cd" in text for text in messages_text))

if __name__ == '__main__':
    unittest.main() 