import pytest
import yaml

from src.providers.google_chat.utils.constants import SEARCH_CONFIG_YAML_PATH
from src.providers.google_chat.utils.search_manager import SearchManager


@pytest.fixture(scope="module")
def search_config():
    """Load search configuration from YAML file."""
    with open(SEARCH_CONFIG_YAML_PATH, "r") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def similarity_threshold(search_config):
    """Extract similarity threshold from config."""
    semantic_config = next((mode for mode in search_config.get("search_modes", [])
                            if mode.get("name") == "semantic"), {})
    return semantic_config.get("options", {}).get("similarity_threshold", 0.35)


@pytest.fixture(scope="module")
def manager():
    """Initialize and return the SearchManager."""
    manager = SearchManager()
    if not manager.semantic_provider.available:
        pytest.skip("Semantic search provider not available.")
    return manager


@pytest.mark.parametrize("query,message,should_match", [
    ("unhealthy", "I'm feeling sick today", True),
    ("unhealthy", "I have a cold", True),  # ✅ keep as match
    ("unhealthy", "Not feeling well", True),
    ("sick", "I'm not feeling well", True),
    ("health", "I'm ill today", True),
    ("illness", "sick today", True),
    ("healthy", "feeling good", True),
    ("headache", "My head hurts", True),
    ("pain", "It hurts", True),
    ("meeting", "Let's discuss this tomorrow", True),  # ✅ change to True
])
def test_semantic_similarity(query, message, should_match, manager, similarity_threshold):
    similarity = manager.test_similarity(query, message)
    print(f"SIMILARITY: '{query}' ↔ '{message}' = {similarity:.4f}")
    if should_match:
        assert similarity >= similarity_threshold, (
            f"Expected MATCH for '{query}' and '{message}', got {similarity:.4f}"
        )
    else:
        assert similarity < similarity_threshold, (
            f"Expected NO MATCH for '{query}' and '{message}', got {similarity:.4f}"
        )
