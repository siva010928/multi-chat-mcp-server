"""
Constants for Google Chat MCP Server integration.
"""

# OAuth and API
DEFAULT_TOKEN_PATH = "/Users/siva010928/Documents/google-chat-mcp-server-main/src/providers/google_chat/token.json"
CREDENTIALS_FILE = "/Users/siva010928/Documents/google-chat-mcp-server-main/src/providers/google_chat/credentials.json"

# Google Chat API endpoints
GOOGLE_CHAT_API_BASE = "https://chat.googleapis.com/v1"
GOOGLE_PEOPLE_API_BASE = "https://people.googleapis.com/v1"

# OAuth scopes
SCOPES = [
    'https://www.googleapis.com/auth/chat.spaces.readonly',
    'https://www.googleapis.com/auth/chat.messages',
    'https://www.googleapis.com/auth/chat.messages.create',
    'https://www.googleapis.com/auth/chat.spaces',
    'https://www.googleapis.com/auth/userinfo.profile',  # For user profile info
    'https://www.googleapis.com/auth/userinfo.email',    # For user email
    'openid'                                            # OpenID Connect
]

# Default callback for local auth server
DEFAULT_CALLBACK_URL = "http://localhost:8000/auth/callback"

# Limits and Defaults
MAX_MESSAGE_LENGTH = 4096
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 1000

# Regex patterns
SPACE_ID_PATTERN = r"^spaces\/[A-Za-z0-9]+$"
MESSAGE_ID_PATTERN = r"^spaces\/[A-Za-z0-9]+\/messages\/[A-Za-z0-9\.\-_]+$"

# Miscellaneous
USER_AGENT = "GoogleChat-MCP/1.0"

# Search configuration path (absolute path)
SEARCH_CONFIG_YAML_PATH = "/Users/siva010928/Documents/google-chat-mcp-server-main/src/providers/google_chat/utils/search_config.yaml"
