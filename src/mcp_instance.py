# src/mcp_instance.py
import logging
from fastmcp import FastMCP

# Set up logger
logger = logging.getLogger(__name__)

# Create MCP instance
logger.info("Creating FastMCP instance")
mcp = FastMCP("Google Chat MCP", description="MCP server for Google Chat API integration")