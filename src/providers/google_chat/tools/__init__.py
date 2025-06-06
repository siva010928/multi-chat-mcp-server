# src/tools/__init__.py - Import all tool modules to ensure registration

# Import tool modules to register tools with MCP
from src.providers.google_chat.tools import message_tools
from src.providers.google_chat.tools import space_tools
from src.providers.google_chat.tools import search_tools
from src.providers.google_chat.tools import user_tools

# Print a debug message to confirm this file is being loaded
print("Initialized tools package - importing all tool modules")
