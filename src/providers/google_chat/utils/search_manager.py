"""
Search Manager - Centralized system for advanced message searching
"""
import logging
import os
import re
import unicodedata
from collections import defaultdict
from typing import Optional

import yaml

from src.mcp_core.engine.provider_loader import get_provider_config_value

# Provider name
PROVIDER_NAME = "google_chat"

# Get configuration values
SEARCH_CONFIG_YAML_PATH = get_provider_config_value(
    PROVIDER_NAME, 
    "search_config_path"
)

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
            logger.info(f"Using default mode: {mode}")

        # Verify mode exists in config
        if mode != "hybrid" and mode not in self.search_modes:
            logger.error(f"Search mode '{mode}' not found in configuration or not enabled")
            # Fall back to exact search if mode not found
            return self._exact_search(query, messages)

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
            # Extra debug for semantic mode
            logger.info(f"Semantic provider available: {self.semantic_provider.available}")
            if not self.semantic_provider.available:
                logger.warning("⚠️ Semantic provider not available! Falling back to exact search.")
                return self._exact_search(query, messages)
            return self._semantic_search(query, messages)
        else:
            logger.error(f"Unknown search mode: {mode}")
            raise ValueError(f"Unknown search mode: {mode}")

    def _exact_search(self, query: str, messages: list[dict]) -> list[tuple[float, dict]]:
        """Perform exact (case-insensitive substring) matching."""
        results = []
        # Normalize the query to handle Unicode characters like smart quotes
        normalized_query = unicodedata.normalize('NFKD', query)
        # Explicitly replace smart apostrophes with standard ASCII apostrophes
        normalized_query = normalized_query.replace('\u2019', "'").replace('\u2018', "'")
        query_lower = normalized_query.lower()
        weight = self.search_modes.get("exact", {}).get("weight", 1.0)

        logger.info(f"Exact search normalized query: '{query}' -> '{normalized_query}' -> '{query_lower}'")

        # Define contraction mappings (both directions)
        contraction_pairs = {
            "don't": ["didn't", "do not", "did not"],
            "didn't": ["don't", "did not", "do not"],
            "isn't": ["wasn't", "is not", "was not"],
            "wasn't": ["isn't", "was not", "is not"],
            "can't": ["couldn't", "cannot", "could not"],
            "couldn't": ["can't", "could not", "cannot"],
            "won't": ["wouldn't", "will not", "would not"],
            "wouldn't": ["won't", "would not", "will not"],
            "aren't": ["weren't", "are not", "were not"],
            "weren't": ["aren't", "were not", "are not"],
            "haven't": ["hadn't", "have not", "had not"],
            "hadn't": ["haven't", "had not", "have not"]
        }

        # For expanded forms, create reverse mapping to contracted forms
        expanded_to_contraction = {}
        for contraction, variants in contraction_pairs.items():
            for variant in variants:
                if " " in variant:  # Only add expanded forms
                    if variant not in expanded_to_contraction:
                        expanded_to_contraction[variant] = []
                    expanded_to_contraction[variant].append(contraction)

        # Add expanded forms to contraction pairs for lookup
        contraction_pairs.update(expanded_to_contraction)

        # Create alternative forms to search for
        alternatives = [query_lower]

        # Check for contractions in the query
        for contraction, variants in contraction_pairs.items():
            if contraction.lower() in query_lower:
                # Replace the contraction with each alternative
                for variant in variants:
                    alt_query = query_lower.replace(contraction.lower(), variant.lower())
                    if alt_query != query_lower and alt_query not in alternatives:
                        alternatives.append(alt_query)

        logger.info(f"Exact search with {len(alternatives)} alternatives: {alternatives}")

        for msg in messages:
            # Normalize the text to handle Unicode characters
            original_text = msg.get("text", "")
            normalized_text = unicodedata.normalize('NFKD', original_text)
            # Explicitly replace smart apostrophes with standard ASCII apostrophes
            normalized_text = normalized_text.replace('\u2019', "'").replace('\u2018', "'")
            text = normalized_text.lower()

            # Check each alternative form
            found = False
            for alt_query in alternatives:
                if alt_query in text:
                    found = True
                    logger.info(f"✓ Found match for '{alt_query}' in: '{text[:100]}...'")
                    # Basic scoring based on number of matches and position of first match
                    match_count = text.count(alt_query)
                    position_factor = 1.0 - (text.find(alt_query) / (len(text) + 1)) if text else 0
                    score = weight * (0.6 + 0.2 * match_count + 0.2 * position_factor)
                    # If this isn't the primary query, slightly reduce the score
                    if alt_query != query_lower:
                        score *= 0.9  # Slight penalty for alternative matches
                    results.append((score, msg))
                    break  # Only count each message once, with the first match

        # Sort by score (descending) using only the score value for comparison
        results.sort(key=lambda x: x[0], reverse=True)
        return results

    def _regex_search(self, query: str, messages: list[dict]) -> list[tuple[float, dict]]:
        """Perform regular expression matching."""
        results = []
        weight = self.search_modes.get("regex", {}).get("weight", 1.0)
        regex_options = self.search_modes.get("regex", {}).get("options", {})

        # Normalize the query to handle Unicode characters like smart quotes
        normalized_query = unicodedata.normalize('NFKD', query)
        # Explicitly replace smart apostrophes with standard ASCII apostrophes
        normalized_query = normalized_query.replace('\u2019', "'").replace('\u2018', "'")

        # Special handling for apostrophes to make search more flexible
        contraction_terms = {
            "don't": ["didn't", "don't", "do not", "did not"],
            "didn't": ["don't", "didn't", "did not", "do not"],
            "isn't": ["wasn't", "isn't", "is not", "was not"],
            "wasn't": ["isn't", "wasn't", "was not", "is not"],
            "can't": ["couldn't", "can't", "cannot", "could not"],
            "couldn't": ["can't", "couldn't", "could not", "cannot"],
            "won't": ["wouldn't", "won't", "will not", "would not"],
            "wouldn't": ["won't", "wouldn't", "would not", "will not"]
        }

        # Check if we need special handling for contractions
        flexible_query = normalized_query
        found_contraction = False

        for contraction, alternatives in contraction_terms.items():
            if contraction.lower() in normalized_query.lower():
                # Create a pattern that matches all forms
                parts = []
                for alt in alternatives:
                    if "'" in alt:
                        # For variants with apostrophes, make the apostrophe optional
                        alt_pattern = alt.replace("'", "['']?")
                        parts.append(alt_pattern)
                    else:
                        parts.append(re.escape(alt))

                # Combine alternatives with OR
                pattern_part = "(" + "|".join(parts) + ")"
                flexible_query = re.sub(re.escape(contraction), pattern_part, normalized_query, flags=re.IGNORECASE)
                found_contraction = True
                logger.info(f"Regex search with contraction handling: '{query}' -> '{flexible_query}'")
                break

        if not found_contraction:
            # General handling for any apostrophe
            if "'" in flexible_query:
                # Make apostrophes optional in the pattern
                flexible_query = flexible_query.replace("'", "['']?")
                logger.info(f"Regex search with apostrophe handling: '{query}' -> '{flexible_query}'")
            else:
                logger.info(f"Regex search normalized query: '{query}' -> '{normalized_query}'")

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
            if len(flexible_query) > max_length:
                flexible_query = flexible_query[:max_length]

            # First try with the flexible pattern
            pattern = re.compile(flexible_query, flags)

            for msg in messages:
                # Normalize the text to handle Unicode characters
                original_text = msg.get("text", "")
                normalized_text = unicodedata.normalize('NFKD', original_text)
                # Explicitly replace smart apostrophes with standard ASCII apostrophes
                normalized_text = normalized_text.replace('\u2019', "'").replace('\u2018', "'")

                if normalized_text:
                    matches = list(pattern.finditer(normalized_text))
                    if matches:
                        # Score based on number of matches and position of first match
                        match_count = len(matches)
                        first_pos = matches[0].start() / len(normalized_text) if matches else 1.0
                        position_factor = 1.0 - first_pos
                        score = weight * (0.6 + 0.2 * min(match_count, 5) + 0.2 * position_factor)
                        results.append((score, msg))
        except re.error as e:
            # Log the error and fallback to exact search
            logger.warning(f"Invalid regex pattern '{flexible_query}': {str(e)}. Falling back to exact search.")
            return self._exact_search(query, messages)

        # Sort by score (descending) using only the score value for comparison
        results.sort(key=lambda x: x[0], reverse=True)
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
            logger.warning("⚠️ Semantic search not available, falling back to exact search")
            return self._exact_search(query, messages)

        # Normalize the query to improve matching
        query = query.strip()

        # Get query embedding
        logger.info(f"Getting embedding for query: '{query}'")
        query_embedding = self.semantic_provider.get_embedding(query)
        if query_embedding is None:
            logger.error("⚠️ Failed to get embedding for query, falling back to exact search")
            return self._exact_search(query, messages)

        # Compare with each message
        logger.info(f"Comparing query against {len(messages)} messages with similarity threshold {similarity_threshold}")
        match_count = 0

        # First pass: Calculate all similarities to find distribution
        all_similarities = []
        for msg in messages:
            text = msg.get("text", "")
            if text:
                msg_embedding = self.semantic_provider.get_embedding(text)
                if msg_embedding is not None:
                    similarity = self.semantic_provider.compute_similarity(
                        query_embedding, msg_embedding, similarity_metric
                    )
                    all_similarities.append((similarity, msg))

        # If we have enough similarities, we can use dynamic thresholding
        if len(all_similarities) >= 10:
            # Sort by similarity
            all_similarities.sort(key=lambda x: x[0], reverse=True)

            # Take top 20% as matches if their similarity exceeds min_threshold
            min_threshold = similarity_threshold * 0.8  # minimum 80% of configured threshold
            top_matches_count = max(1, int(len(all_similarities) * 0.2))  # at least 1 match

            for i, (similarity, msg) in enumerate(all_similarities):
                if i < top_matches_count and similarity >= min_threshold:
                    score = weight * similarity
                    results.append((score, msg))
                    match_count += 1
                    logger.debug(f"✓ Match found with score {score:.4f}: {msg.get('text', '')[:50]}...")
        else:
            # Traditional threshold-based approach for small message sets
            for similarity, msg in all_similarities:
                if similarity >= similarity_threshold:
                    score = weight * similarity
                    results.append((score, msg))
                    match_count += 1
                    logger.debug(f"✓ Match found with score {score:.4f}: {msg.get('text', '')[:50]}...")

        logger.info(f"Semantic search found {match_count} matches")

        # Sort by score (descending) using only the score value for comparison
        results.sort(key=lambda x: x[0], reverse=True)
        return results

    def _hybrid_search(self, query: str, messages: list[dict]) -> list[tuple[float, dict]]:
        """Combine results from multiple search methods."""
        # Get weights for each mode
        hybrid_weights = self.config.get('search', {}).get('hybrid_weights', {})
        logger.info(f"Running hybrid search with weights: {hybrid_weights}")

        # Initialize result tracking
        all_results = {}
        msg_scores = defaultdict(float)
        mode_matches = defaultdict(int)

        # Normalize the query to improve matching
        query = query.strip()

        # Run exact search
        if "exact" in self.search_modes and self.search_modes["exact"].get("enabled", False):
            exact_results = self._exact_search(query, messages)
            for score, msg in exact_results:
                msg_id = msg.get("name", "")
                if msg_id:
                    all_results[msg_id] = msg
                    # Apply hybrid weight
                    exact_weight = hybrid_weights.get("exact", 1.0)
                    msg_scores[msg_id] += score * exact_weight
                    mode_matches["exact"] += 1
            logger.info(f"Exact search found {mode_matches['exact']} matches")

        # Run regex search
        if "regex" in self.search_modes and self.search_modes["regex"].get("enabled", False):
            regex_results = self._regex_search(query, messages)
            for score, msg in regex_results:
                msg_id = msg.get("name", "")
                if msg_id:
                    all_results[msg_id] = msg
                    # Apply hybrid weight
                    regex_weight = hybrid_weights.get("regex", 1.2)
                    msg_scores[msg_id] += score * regex_weight
                    mode_matches["regex"] += 1
            logger.info(f"Regex search found {mode_matches['regex']} matches")

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
                    semantic_weight = hybrid_weights.get("semantic", 1.5)
                    msg_scores[msg_id] += score * semantic_weight
                    mode_matches["semantic"] += 1
            logger.info(f"Semantic search found {mode_matches['semantic']} matches")

        # Add bonus for messages that match multiple search modes
        for msg_id, score in list(msg_scores.items()):
            # Count how many modes found this message
            mode_count = sum(1 for mode in ["exact", "regex", "semantic"]
                            if msg_id in [m.get("name", "") for _, m in locals().get(f"{mode}_results", [])])

            if mode_count > 1:
                # Add a bonus for messages found by multiple search modes
                bonus = score * 0.2 * (mode_count - 1)
                msg_scores[msg_id] += bonus
                logger.debug(f"Added multi-mode bonus of {bonus:.2f} to message {msg_id}")

        # Combine and sort results
        combined_results = []
        for msg_id, score in msg_scores.items():
            combined_results.append((score, all_results[msg_id]))

        # Sort by combined score (descending) using only the score value for comparison
        combined_results.sort(key=lambda x: x[0], reverse=True)

        total_matches = len(combined_results)
        logger.info(f"Hybrid search found {total_matches} total unique matches")

        return combined_results

    def compute_similarity(self, query_embedding, msg_embedding, similarity_metric="cosine"):
        """
        Compute similarity between two embeddings.

        Args:
            query_embedding: Embedding vector for query
            msg_embedding: Embedding vector for message
            similarity_metric: Metric to use (cosine, dot, euclidean)

        Returns:
            Similarity score between 0-1 (higher is more similar)
        """
        if similarity_metric == "cosine":
            # Cosine similarity
            from numpy.linalg import norm
            import numpy as np
            cos_sim = np.dot(query_embedding, msg_embedding) / (norm(query_embedding) * norm(msg_embedding))
            return float((cos_sim + 1) / 2)  # Rescale from [-1, 1] to [0, 1]
        elif similarity_metric == "dot":
            # Dot product similarity
            import numpy as np
            return float(np.dot(query_embedding, msg_embedding))
        elif similarity_metric == "euclidean":
            # Euclidean distance (converted to similarity)
            import numpy as np
            dist = np.linalg.norm(query_embedding - msg_embedding)
            return float(1 / (1 + dist))  # Convert distance to similarity (0-1)
        else:
            logger.error(f"Unknown similarity metric: {similarity_metric}")
            return 0.0

    def test_similarity(self, query_text: str, message_text: str) -> float:
        """Test similarity between a query and message text directly."""
        if not self.semantic_provider.available:
            logger.error("Semantic provider not available")
            return 0.0

        query_embedding = self.semantic_provider.get_embedding(query_text)
        msg_embedding = self.semantic_provider.get_embedding(message_text)

        if query_embedding is None or msg_embedding is None:
            logger.error("Failed to generate embeddings")
            return 0.0

        similarity = self.semantic_provider.compute_similarity(
            query_embedding, msg_embedding
        )

        return similarity

class SemanticSearchProvider:
    """Provider for semantic search using free, lightweight models."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", cache_size: int = 10000):
        self.model_name = model_name
        self.cache_size = cache_size
        self.model = None
        self.cache = {}  # Simple cache for embeddings
        self.available = False  # Initialize to False by default
        logger.info(f"Initializing SemanticSearchProvider with model: {model_name}")
        self._initialize()

    def _initialize(self):
        """Initialize the semantic search model."""
        try:
            # Try to import sentence-transformers - a lightweight embedding library
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading SentenceTransformer model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.available = True
            logger.info("✓ Semantic search provider initialized successfully")
        except ImportError as e:
            logger.error(f"✗ sentence-transformers not installed: {str(e)}")
            logger.error("✗ Semantic search will be unavailable")
            logger.error("To enable semantic search, install: pip install sentence-transformers")
            self.available = False
        except Exception as e:
            logger.error(f"✗ Failed to initialize semantic search model: {str(e)}")
            self.available = False

    def get_embedding(self, text: str):
        """Get embedding for a text string, with caching."""
        if not self.available or not text:
            logger.debug(f"Cannot get embedding: model available: {self.available}, text empty: {not bool(text)}")
            return None

        # Check cache first
        if text in self.cache:
            logger.debug("Using cached embedding")
            return self.cache[text]

        # Generate new embedding
        try:
            logger.debug(f"Generating new embedding for text: {text[:50]}...")
            embedding = self.model.encode(text, show_progress_bar=False)

            # Cache with simple LRU mechanism (just delete one if over size)
            if len(self.cache) >= self.cache_size:
                # Remove one item (in practice, would use a proper LRU cache)
                if self.cache:
                    self.cache.pop(next(iter(self.cache)))

            self.cache[text] = embedding
            logger.debug(f"✓ Generated embedding with shape: {embedding.shape}")
            return embedding
        except Exception as e:
            logger.error(f"✗ Error generating embedding: {str(e)}")
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
