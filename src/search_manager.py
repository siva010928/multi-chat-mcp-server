"""
Search Manager - Centralized system for advanced message searching
"""
import logging
import os
import re
from collections import defaultdict
from typing import Optional

import yaml

from src.google_chat.constants import SEARCH_CONFIG_YAML_PATH

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("search_manager")

# Optional imports for semantic search, with fallbacks
try:
    import numpy as np
    HAS_NUMPY = True
    logger.info("NumPy is available for vector operations")
except ImportError:
    HAS_NUMPY = False
    logger.warning("NumPy is not available - semantic search will be limited")

class SearchManager:
    """Manages search operations across different search modes based on configuration."""
    
    def __init__(self, config_path: str = ("%s" % SEARCH_CONFIG_YAML_PATH)):
        """Initialize the search manager with the provided configuration file."""
        logger.info(f"Initializing SearchManager with config: {config_path}")
        self.config = self._load_config(config_path)
        self.search_modes = {}
        self._initialize_search_modes()
        
        # Initialize semantic search provider if enabled
        semantic_config = self.search_modes.get("semantic", {}).get("options", {})
        model_name = semantic_config.get("model", "all-MiniLM-L6-v2")
        cache_size = semantic_config.get("cache_max_size", 10000)
        logger.info(f"Setting up semantic provider with model: {model_name}")
        self.semantic_provider = SemanticSearchProvider(model_name, cache_size)
    
    def _load_config(self, config_path: str) -> dict:
        """Load search configuration from a YAML file."""
        if not os.path.exists(config_path):
            logger.error(f"Search configuration file not found: {config_path}")
            raise FileNotFoundError(f"Search configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logger.info(f"Loaded configuration with {len(config.get('search_modes', []))} search modes")
        return config
    
    def _initialize_search_modes(self):
        """Initialize the enabled search modes based on configuration."""
        for mode in self.config.get('search_modes', []):
            if mode.get('enabled', False):
                self.search_modes[mode['name']] = mode
                logger.info(f"Enabled search mode: {mode['name']}")
    
    def get_default_mode(self) -> str:
        """Get the default search mode from configuration."""
        default = self.config.get('search', {}).get('default_mode', 'exact')
        logger.info(f"Using default search mode: {default}")
        return default
        
    def search(self, query: str, messages: list[dict], mode: Optional[str] = None) -> list[tuple[float, dict]]:
        """
        Search messages using the specified mode.
        
        Args:
            query: The search query
            messages: list of message objects to search through
            mode: Search mode (exact, regex, semantic, hybrid)
                  If None, uses the default mode from config
                  
        Returns:
            list of tuples (score, message) sorted by relevance score (descending)
        """
        logger.info(f"Starting search with query: '{query}', mode: {mode or 'default'}, message count: {len(messages)}")
        
        if mode is None:
            mode = self.get_default_mode()
            
        if mode == "hybrid":
            logger.info("Using hybrid search mode")
            return self._hybrid_search(query, messages)
        elif mode == "exact":
            logger.info("Using exact search mode")
            return self._exact_search(query, messages)
        elif mode == "regex":
            logger.info("Using regex search mode")
            return self._regex_search(query, messages)
        elif mode == "semantic":
            logger.info("Using semantic search mode")
            return self._semantic_search(query, messages)
        else:
            logger.error(f"Unknown search mode: {mode}")
            raise ValueError(f"Unknown search mode: {mode}")
            
    def _exact_search(self, query: str, messages: list[dict]) -> list[tuple[float, dict]]:
        """Perform exact (case-insensitive substring) matching."""
        results = []
        query_lower = query.lower()
        weight = self.search_modes.get("exact", {}).get("weight", 1.0)
        
        for msg in messages:
            text = msg.get("text", "").lower()
            if query_lower in text:
                # Basic scoring based on number of matches and position of first match
                match_count = text.count(query_lower)
                position_factor = 1.0 - (text.find(query_lower) / (len(text) + 1)) if text else 0
                score = weight * (0.6 + 0.2 * match_count + 0.2 * position_factor)
                results.append((score, msg))
                
        # Sort by score (descending)
        results.sort(reverse=True)
        return results
        
    def _regex_search(self, query: str, messages: list[dict]) -> list[tuple[float, dict]]:
        """Perform regular expression matching."""
        results = []
        weight = self.search_modes.get("regex", {}).get("weight", 1.0)
        regex_options = self.search_modes.get("regex", {}).get("options", {})
        
        # Compile the regex pattern
        flags = 0
        if regex_options.get("ignore_case", True):
            flags |= re.IGNORECASE
        if regex_options.get("dot_all", False):
            flags |= re.DOTALL
        if regex_options.get("unicode", True):
            flags |= re.UNICODE
            
        try:
            # Limit the pattern length for safety
            max_length = regex_options.get("max_pattern_length", 1000)
            if len(query) > max_length:
                query = query[:max_length]
                
            pattern = re.compile(query, flags)
            
            for msg in messages:
                text = msg.get("text", "")
                if text:
                    matches = list(pattern.finditer(text))
                    if matches:
                        # Score based on number of matches and position of first match
                        match_count = len(matches)
                        first_pos = matches[0].start() / len(text) if matches else 1.0
                        position_factor = 1.0 - first_pos
                        score = weight * (0.6 + 0.2 * min(match_count, 5) + 0.2 * position_factor)
                        results.append((score, msg))
        except re.error:
            # Fallback to exact search if regex is invalid
            return self._exact_search(query, messages)
        
        # Sort by score (descending)
        results.sort(reverse=True)
        return results
        
    def _semantic_search(self, query: str, messages: list[dict]) -> list[tuple[float, dict]]:
        """Perform semantic (meaning-based) matching."""
        results = []
        semantic_config = self.search_modes.get("semantic", {}).get("options", {})
        weight = self.search_modes.get("semantic", {}).get("weight", 1.5)
        similarity_threshold = semantic_config.get("similarity_threshold", 0.6)
        similarity_metric = semantic_config.get("similarity_metric", "cosine")
        
        # If semantic search isn't available, fall back to exact search
        if not self.semantic_provider.available:
            logger.warning("Semantic search not available, falling back to exact search")
            return self._exact_search(query, messages)
            
        # Get query embedding
        logger.info(f"Getting embedding for query: '{query}'")
        query_embedding = self.semantic_provider.get_embedding(query)
        if query_embedding is None:
            logger.error("Failed to get embedding for query, falling back to exact search")
            return self._exact_search(query, messages)
            
        # Compare with each message
        logger.info(f"Comparing query against {len(messages)} messages with similarity threshold {similarity_threshold}")
        match_count = 0
        for msg in messages:
            text = msg.get("text", "")
            if text:
                msg_embedding = self.semantic_provider.get_embedding(text)
                if msg_embedding is not None:
                    similarity = self.semantic_provider.compute_similarity(
                        query_embedding, msg_embedding, similarity_metric
                    )
                    
                    # Only include results above threshold
                    if similarity >= similarity_threshold:
                        score = weight * similarity
                        results.append((score, msg))
                        match_count += 1
                        logger.debug(f"Match found with score {score:.4f}: {text[:50]}...")
        
        logger.info(f"Semantic search found {match_count} matches above threshold {similarity_threshold}")
        
        # Sort by score (descending)
        results.sort(reverse=True)
        return results
    
    def _hybrid_search(self, query: str, messages: list[dict]) -> list[tuple[float, dict]]:
        """Combine results from multiple search methods."""
        # Get weights for each mode
        hybrid_weights = self.config.get('search', {}).get('hybrid_weights', {})
        
        # Run each enabled search mode
        all_results = {}
        msg_scores = defaultdict(float)
        
        # Run exact search
        if "exact" in self.search_modes and self.search_modes["exact"].get("enabled", False):
            exact_results = self._exact_search(query, messages)
            for score, msg in exact_results:
                msg_id = msg.get("name", "")
                if msg_id:
                    all_results[msg_id] = msg
                    # Apply hybrid weight
                    msg_scores[msg_id] += score * hybrid_weights.get("exact", 1.0)
        
        # Run regex search
        if "regex" in self.search_modes and self.search_modes["regex"].get("enabled", False):
            regex_results = self._regex_search(query, messages)
            for score, msg in regex_results:
                msg_id = msg.get("name", "")
                if msg_id:
                    all_results[msg_id] = msg
                    # Apply hybrid weight
                    msg_scores[msg_id] += score * hybrid_weights.get("regex", 1.2)
                    
        # Run semantic search if available
        if ("semantic" in self.search_modes and 
            self.search_modes["semantic"].get("enabled", False) and 
            self.semantic_provider.available):
            semantic_results = self._semantic_search(query, messages)
            for score, msg in semantic_results:
                msg_id = msg.get("name", "")
                if msg_id:
                    all_results[msg_id] = msg
                    # Apply hybrid weight
                    msg_scores[msg_id] += score * hybrid_weights.get("semantic", 1.5)
        
        # Combine and sort results
        combined_results = []
        for msg_id, score in msg_scores.items():
            combined_results.append((score, all_results[msg_id]))
        
        # Sort by combined score (descending)
        combined_results.sort(reverse=True)
        return combined_results

class SemanticSearchProvider:
    """Provider for semantic search using free, lightweight models."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", cache_size: int = 10000):
        self.model_name = model_name
        self.cache_size = cache_size
        self.model = None
        self.cache = {}  # Simple cache for embeddings
        self._initialize()
        
    def _initialize(self):
        """Initialize the semantic search model."""
        try:
            # Try to import sentence-transformers - a lightweight embedding library
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading SentenceTransformer model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.available = True
            logger.info("Semantic search provider initialized successfully")
        except ImportError:
            logger.error("sentence-transformers not installed. Semantic search will be unavailable.")
            logger.error("To enable semantic search, install: pip install sentence-transformers")
            self.available = False
            
    def get_embedding(self, text: str):
        """Get embedding for a text string, with caching."""
        if not self.available or not text:
            logger.debug("Cannot get embedding: model unavailable or empty text")
            return None
            
        # Check cache first
        if text in self.cache:
            logger.debug("Using cached embedding")
            return self.cache[text]
            
        # Generate new embedding
        try:
            logger.debug(f"Generating new embedding for text: {text[:30]}...")
            embedding = self.model.encode(text, show_progress_bar=False)
            
            # Cache with simple LRU mechanism (just delete one if over size)
            if len(self.cache) >= self.cache_size:
                # Remove one item (in practice, would use a proper LRU cache)
                if self.cache:
                    self.cache.pop(next(iter(self.cache)))
            
            self.cache[text] = embedding
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None
        
    def compute_similarity(self, embedding1, embedding2, metric: str = "cosine"):
        """Compute similarity between two embeddings."""
        if not HAS_NUMPY or embedding1 is None or embedding2 is None:
            logger.warning("Cannot compute similarity: NumPy unavailable or invalid embeddings")
            return 0.0
            
        try:
            if metric == "cosine":
                # Cosine similarity
                dot = np.dot(embedding1, embedding2)
                norm1 = np.linalg.norm(embedding1)
                norm2 = np.linalg.norm(embedding2)
                similarity = dot / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0.0
                logger.debug(f"Computed cosine similarity: {similarity:.4f}")
                return similarity
            elif metric == "dot":
                # Dot product
                similarity = np.dot(embedding1, embedding2)
                logger.debug(f"Computed dot product similarity: {similarity:.4f}")
                return similarity
            elif metric == "euclidean":
                # Euclidean distance converted to similarity
                dist = np.linalg.norm(embedding1 - embedding2)
                similarity = 1.0 / (1.0 + dist)  # Convert distance to similarity
                logger.debug(f"Computed euclidean similarity: {similarity:.4f}")
                return similarity
            else:
                logger.warning(f"Unknown similarity metric: {metric}")
                return 0.0
        except Exception as e:
            logger.error(f"Error computing similarity: {str(e)}")
            return 0.0 