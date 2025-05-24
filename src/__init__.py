"""Multi-Provider MCP Server"""

# Note: We no longer import MCP instance here as it's now provider-specific
# and loaded dynamically by the server.py script.

# Import tool modules to register them
# These will be loaded dynamically by the provider_loader module
# when the server starts with a specific provider.
