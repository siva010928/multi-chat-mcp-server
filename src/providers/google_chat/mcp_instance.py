"""
MCP instance for Google Chat provider.

This module creates a FastMCP instance for the Google Chat provider.
"""

import logging
from fastmcp import FastMCP
from src.mcp_core.engine.provider_loader import get_provider_config_value
from src.mcp_core.tools.tool_decorator import tool_decorator_factory

# Set up logger
logger = logging.getLogger(__name__)

# Provider name
PROVIDER_NAME = "google_chat"

# Get configuration values
name = get_provider_config_value(
    PROVIDER_NAME, 
    "name"
)
description = get_provider_config_value(
    PROVIDER_NAME, 
    "description"
)

# Create MCP instance with configuration values
logger.info(f"Creating FastMCP instance for Google Chat with name: {name}")
mcp = FastMCP(name, description=description)

# Create a tool decorator that registers tools with both the MCP instance and the central registry
tool = tool_decorator_factory(PROVIDER_NAME, mcp)
