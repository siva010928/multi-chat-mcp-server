"""
Test script for the provider_loader module.

This script tests the provider_loader module to ensure it can load the provider configuration correctly.
"""

import logging
import os
import sys
import pytest

# Add the root directory to the Python path so we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), '..')))

from src.mcp_core.engine.provider_loader import load_provider_config, get_available_providers

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_get_available_providers():
    """Test the get_available_providers function."""
    logger.info("Testing get_available_providers...")
    providers = get_available_providers()
    assert providers, "No providers found in configuration."

    logger.info(f"Found {len(providers)} providers:")
    for provider_name, provider_config in providers.items():
        logger.info(f"  - {provider_name}: {provider_config.get('description', 'No description')}")

@pytest.mark.parametrize("provider_name", ["google_chat", "slack"])
def test_load_provider_config(provider_name):
    """Test the load_provider_config function for a specific provider."""
    logger.info(f"Testing load_provider_config for provider '{provider_name}'...")
    config = load_provider_config(provider_name)
    assert config, f"Failed to load configuration for provider '{provider_name}'"

    logger.info(f"Successfully loaded configuration for provider '{provider_name}':")
    for key, value in config.items():
        logger.info(f"  - {key}: {value}")

def test_load_provider_config_nonexistent():
    """Test the load_provider_config function for a non-existent provider."""
    provider_name = "non_existent_provider"
    logger.info(f"Testing load_provider_config for provider '{provider_name}'...")

    with pytest.raises(ValueError) as excinfo:
        load_provider_config(provider_name)

    assert "not found in configuration" in str(excinfo.value)
    logger.info(f"Successfully caught ValueError for non-existent provider: {str(excinfo.value)}")

if __name__ == "__main__":
    # Run the tests
    test_get_available_providers()
    test_load_provider_config("google_chat")
    test_load_provider_config("slack")
    test_load_provider_config_nonexistent()
    logger.info("All tests passed!")