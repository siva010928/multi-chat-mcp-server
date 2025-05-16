"""Google Chat MCP Server"""

# Import MCP instance for other modules to use
from src.mcp_instance import mcp

# Import tool modules to register them
import src.tools.message_tools  # noqa
import src.tools.space_tools  # noqa
import src.tools.search_tools  # noqa
import src.tools.user_tools  # noqa
