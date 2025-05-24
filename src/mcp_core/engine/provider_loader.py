"""
Provider loader module for MCP.

This module provides functions to load provider configuration and modules.
It includes caching to avoid loading the configuration multiple times.
"""

import importlib
import logging
import os
import threading
import yaml
from typing import Dict, Any, Tuple, Optional

# Set up logger
logger = logging.getLogger(__name__)

# Path to the provider configuration file
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "provider-config.yaml")

# Cache for provider configurations
_provider_configs: Dict[str, Dict[str, Any]] = {}
_config_lock = threading.RLock()  # Use RLock to allow recursive acquisition

# Cache for the full configuration
_full_config: Optional[Dict[str, Any]] = None

def load_provider_config(provider_name: str) -> Dict[str, Any]:
    """
    Load configuration for a specific provider from the provider-config.yaml file.

    This function caches the configuration to avoid loading it multiple times.

    Args:
        provider_name: The name of the provider to load configuration for.

    Returns:
        A dictionary containing the provider's configuration.

    Raises:
        ValueError: If the provider is not found in the configuration.
    """
    # Check if the configuration is already cached
    with _config_lock:
        if provider_name in _provider_configs:
            logger.debug(f"Using cached configuration for provider: {provider_name}")
            return _provider_configs[provider_name]

        try:
            # Load the full configuration if not already loaded
            if _full_config is None:
                _load_full_config()

            if provider_name not in _full_config['providers']:
                raise ValueError(f"Provider '{provider_name}' not found in configuration")

            # Cache the provider configuration
            _provider_configs[provider_name] = _full_config['providers'][provider_name]

            return _provider_configs[provider_name]
        except Exception as e:
            logger.error(f"Error loading provider configuration: {str(e)}")
            raise

def _load_full_config() -> None:
    """
    Load the full configuration from the provider-config.yaml file.

    This function is called by load_provider_config if the configuration is not already loaded.

    Raises:
        ValueError: If the configuration file is invalid.
    """
    global _full_config

    try:
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)

        if not config or 'providers' not in config:
            raise ValueError(f"Invalid configuration file: {CONFIG_PATH}")

        _full_config = config
        logger.info(f"Loaded full configuration with {len(config['providers'])} providers")
    except Exception as e:
        logger.error(f"Error loading full configuration: {str(e)}")
        raise

def load_provider_modules(provider_name: str) -> Tuple[Any, Any, Any]:
    """
    Dynamically import and return the provider's modules.

    Args:
        provider_name: The name of the provider to load modules for.

    Returns:
        A tuple containing (mcp_instance, server_auth, tools) modules.

    Raises:
        ImportError: If any of the required modules cannot be imported.
    """
    try:
        # Import the provider's modules
        mcp_instance = importlib.import_module(f"src.providers.{provider_name}.mcp_instance")
        server_auth = importlib.import_module(f"src.providers.{provider_name}.server_auth")

        # Import all tool modules
        tools_package = f"src.providers.{provider_name}.tools"
        tools = importlib.import_module(tools_package)

        # Import all tool modules in the tools package
        for module_name in dir(tools):
            if not module_name.startswith('_') and module_name.endswith('_tools'):
                importlib.import_module(f"{tools_package}.{module_name}")

        return mcp_instance, server_auth, tools
    except ImportError as e:
        logger.error(f"Error importing provider modules: {str(e)}")
        raise

def get_available_providers() -> Dict[str, Dict[str, Any]]:
    """
    Get a list of all available providers from the configuration.

    This function uses the cached configuration if available.

    Returns:
        A dictionary mapping provider names to their configurations.
    """
    with _config_lock:
        try:
            # Load the full configuration if not already loaded
            if _full_config is None:
                _load_full_config()

            return _full_config['providers']
        except Exception as e:
            logger.error(f"Error getting available providers: {str(e)}")
            return {}

def get_provider_config_value(provider_name: str, key: str) -> Any:
    """
    Get a specific configuration value for a provider.

    This function uses the cached configuration if available.

    Args:
        provider_name: The name of the provider to get the configuration value for.
        key: The key of the configuration value to get.

    Returns:
        The configuration value.

    Raises:
        KeyError: If the key is not found in the provider configuration.
        ValueError: If the provider is not found in the configuration.
    """
    try:
        config = load_provider_config(provider_name)
        if key not in config:
            raise KeyError(f"Key '{key}' not found in configuration for provider '{provider_name}'")
        return config[key]
    except Exception as e:
        logger.error(f"Error getting provider configuration value: {str(e)}")
        raise

def initialize_provider_config(provider_name: str) -> Dict[str, Any]:
    """
    Initialize the configuration for a provider.

    This function loads the configuration for a provider and caches it.
    It should be called at startup to ensure the configuration is loaded
    before it's needed by other components.

    Args:
        provider_name: The name of the provider to initialize the configuration for.

    Returns:
        A dictionary containing the provider's configuration.

    Raises:
        ValueError: If the provider is not found in the configuration.
    """
    logger.info(f"Initializing configuration for provider: {provider_name}")
    return load_provider_config(provider_name)
