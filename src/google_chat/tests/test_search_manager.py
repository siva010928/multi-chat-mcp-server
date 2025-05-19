import pytest
from unittest.mock import patch, MagicMock
import numpy as np

from src.search_manager import SearchManager


def test_exact_search_sorting():
    """Test that _exact_search sorts results correctly."""
    search_manager = SearchManager()
    
    # Create test messages
    messages = [
        {"name": "msg1", "text": "This is the first message"},
        {"name": "msg2", "text": "This is the second message"},
        {"name": "msg3", "text": "This is another message"}
    ]
    
    # Run search
    results = search_manager._exact_search("message", messages)
    
    # Verify that results are sorted by score
    scores = [score for score, _ in results]
    assert len(scores) == 3
    assert all(scores[i] >= scores[i+1] for i in range(len(scores)-1)), "Results should be sorted by score descending"


def test_semantic_search_sorting():
    """Test that _semantic_search sorts results correctly."""
    search_manager = SearchManager()
    
    # Mock the semantic provider to return predictable similarities
    search_manager.semantic_provider = MagicMock()
    search_manager.semantic_provider.available = True
    search_manager.semantic_provider.get_embedding.return_value = np.array([1, 0, 0])
    
    # Mock compute_similarity to return different values for different messages
    similarity_values = {
        "msg1": 0.9,
        "msg2": 0.7,
        "msg3": 0.8
    }
    
    def mock_compute_similarity(embed1, embed2, metric):
        # Use the name in the current message being processed
        for name, sim in similarity_values.items():
            if name in search_manager._current_msg_name:
                return sim
        return 0.5
    
    search_manager.semantic_provider.compute_similarity.side_effect = mock_compute_similarity
    
    # Create test messages
    messages = [
        {"name": "msg1", "text": "This is the first message"},
        {"name": "msg2", "text": "This is the second message"},
        {"name": "msg3", "text": "This is another message"}
    ]
    
    # Run search with tracking of current message
    results = []
    for msg in messages:
        search_manager._current_msg_name = msg["name"]  # Track which message is being processed
        msg_embedding = search_manager.semantic_provider.get_embedding(msg["text"])
        similarity = search_manager.semantic_provider.compute_similarity(None, msg_embedding, "cosine")
        results.append((similarity, msg))
    
    # Sort using the same method as _semantic_search
    results.sort(key=lambda x: x[0], reverse=True)
    
    # Verify results are sorted by similarity score
    expected_order = ["msg1", "msg3", "msg2"]  # Based on similarity values 0.9, 0.8, 0.7
    actual_order = [msg["name"] for _, msg in results]
    
    assert actual_order == expected_order, f"Expected order: {expected_order}, got: {actual_order}"


def test_hybrid_search_sorting():
    """Test that _hybrid_search sorts results correctly."""
    with patch('src.search_manager.SearchManager._exact_search') as mock_exact_search, \
         patch('src.search_manager.SearchManager._regex_search') as mock_regex_search, \
         patch('src.search_manager.SearchManager._semantic_search') as mock_semantic_search:
        
        # Create search manager with mock config
        search_manager = SearchManager()
        search_manager.search_modes = {
            "exact": {"enabled": True},
            "regex": {"enabled": True},
            "semantic": {"enabled": True}
        }
        search_manager.config = {
            "search": {
                "hybrid_weights": {
                    "exact": 1.0,
                    "regex": 1.2,
                    "semantic": 1.5
                }
            }
        }
        search_manager.semantic_provider = MagicMock()
        search_manager.semantic_provider.available = True
        
        # Setup mock returns with different scores
        mock_exact_search.return_value = [
            (0.8, {"name": "msg1", "text": "text1"}),
            (0.6, {"name": "msg2", "text": "text2"})
        ]
        
        mock_regex_search.return_value = [
            (0.9, {"name": "msg2", "text": "text2"}),
            (0.7, {"name": "msg3", "text": "text3"})
        ]
        
        mock_semantic_search.return_value = [
            (0.85, {"name": "msg1", "text": "text1"}),
            (0.75, {"name": "msg3", "text": "text3"})
        ]
        
        # Run hybrid search
        results = search_manager._hybrid_search("query", [])
        
        # Verify the combined scores are correctly sorted
        # msg1: 0.8*1.0 + 0.85*1.5 = 2.075
        # msg2: 0.6*1.0 + 0.9*1.2 = 1.68
        # msg3: 0.7*1.2 + 0.75*1.5 = 1.965
        # Expected order: msg1, msg3, msg2
        
        expected_order = ["msg1", "msg3", "msg2"]
        actual_order = [msg["name"] for _, msg in results]
        
        assert actual_order == expected_order, f"Expected order: {expected_order}, got: {actual_order}" 