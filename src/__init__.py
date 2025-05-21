"""Google Chat MCP Server"""

# Import MCP instance for other modules to use
from src.mcp_instance import mcp

# Import tool modules to register them
import src.providers.google_chat.tools.message_tools  # noqa
import src.providers.google_chat.tools.space_tools  # noqa
import src.providers.google_chat.tools.search_tools  # noqa
import src.providers.google_chat.tools.user_tools  # noqa
