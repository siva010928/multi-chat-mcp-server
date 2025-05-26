# Provider Development Guide

This guide provides detailed instructions for adding a new provider to the Multi-Provider MCP Server framework.

## Table of Contents

1. [Overview](#overview)
2. [Directory Structure](#directory-structure)
3. [Provider Registration](#1-provider-registration)
4. [Core Files Implementation (MANDATORY)](#2-core-files-implementation-mandatory)
5. [API Implementation (FLEXIBLE)](#3-api-implementation-flexible)
6. [Tool Implementation (FLEXIBLE)](#4-tool-implementation-flexible)
7. [Search Configuration (OPTIONAL)](#5-search-configuration-optional)

## Overview

The Multi-Provider MCP Server framework is designed to be extensible, allowing you to add support for new chat platforms by implementing a standard set of interfaces.

### Key Concepts

- **Provider**: A module that integrates a specific chat platform (e.g., Google Chat, Slack) with the MCP framework
- **MCP (Model Control Protocol)**: A standardized interface that AI assistants use to interact with external systems
- **Tools**: Functions exposed via MCP that enable AI assistants to perform actions in the chat platform
- **API Client**: Low-level code that communicates directly with the chat platform's API

### Provider Architecture

Each provider follows a consistent structure where:
1. **Core files** (`mcp_instance.py`, `server_auth.py`, `api/auth.py`) follow strict patterns
2. **API and tool implementations** can be flexible based on your chat platform's requirements

## Directory Structure

Create a new directory for your provider under `src/providers/`:

```
src/providers/your_provider/
├── api/                # API client implementations
│   ├── auth.py         # 🔴 MANDATORY - Authentication handling
│   ├── messages.py     # 🟡 FLEXIBLE - Message-related API calls
│   ├── spaces.py       # 🟡 FLEXIBLE - Spaces/channels API calls
│   └── users.py        # 🟡 FLEXIBLE - User-related API calls
├── tools/              # MCP tool implementations
│   ├── message_tools.py # 🟡 FLEXIBLE - Message tools
│   ├── space_tools.py   # 🟡 FLEXIBLE - Space management tools
│   └── user_tools.py    # 🟡 FLEXIBLE - User info tools
├── utils/              # Utility functions
│   └── search_config.yaml # 🟢 OPTIONAL - Search configuration
├── __init__.py         # Package initialization (usually empty)
├── mcp_instance.py     # 🔴 MANDATORY - MCP instance configuration
├── server_auth.py      # 🔴 MANDATORY - Authentication server
└── README.md           # Provider documentation
```

### File Classifications:
- 🔴 **MANDATORY**: Must follow exact structure and patterns
- 🟡 **FLEXIBLE**: Can be customized based on your chat platform's API
- 🟢 **OPTIONAL**: Only needed for specific features

## 1. Provider Registration

### ⚠️ CRITICAL: Directory Naming

**The provider directory name must exactly match the key in `provider-config.yaml`**

For example:
```
Directory: src/providers/my_chat_platform/
Config key: providers.my_chat_platform
```

### Update provider-config.yaml

Add your provider configuration:

```yaml
providers:
  your_provider:  # 🔴 MUST match directory name exactly
    name: "Your Provider Name"
    description: "Description of your provider"
    token_path: "src/providers/your_provider/token.json"
    credentials_path: "src/providers/your_provider/credentials.json"
    callback_url: "http://localhost:8000/auth/callback"
    port: 8000  # Optional: custom port for auth server
    scopes:
      - "scope1"
      - "scope2"
    search_config_path: "src/providers/your_provider/utils/search_config.yaml"  # Optional
```

**Note**: All paths are relative to the project root directory.

## 2. Core Files Implementation (MANDATORY)

These three files must follow the exact patterns shown below for proper integration with the framework.

### 🔴 mcp_instance.py (MANDATORY STRUCTURE)

```python
"""
MCP instance for Your Provider.

This module creates a FastMCP instance for your provider.
"""

import logging
from fastmcp import FastMCP
from src.mcp_core.engine.provider_loader import get_provider_config_value
from src.mcp_core.tools.tool_decorator import tool_decorator_factory

# Set up logger
logger = logging.getLogger(__name__)

# 🔴 CRITICAL: Provider name must match directory name and config key
PROVIDER_NAME = "your_provider"

# Get configuration values
name = get_provider_config_value(PROVIDER_NAME, "name")
description = get_provider_config_value(PROVIDER_NAME, "description")

# Create MCP instance
logger.info(f"Creating FastMCP instance for {name}")
mcp = FastMCP(name, description=description)

# 🔴 CRITICAL: Create tool decorator for central registration
tool = tool_decorator_factory(PROVIDER_NAME, mcp)
```

### 🔴 server_auth.py (MANDATORY STRUCTURE)

This file handles OAuth authentication and **MUST** include the `run_auth_server()` function as it's called by `server.py` during local authentication.

```python
import asyncio
import os
import signal
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse, JSONResponse

from src.providers.your_provider.api.auth import get_credentials, save_credentials, refresh_token
from src.mcp_core.engine.provider_loader import get_provider_config_value

# Provider name 
PROVIDER_NAME = "your_provider"

# Get configuration values
TOKEN_PATH = get_provider_config_value(PROVIDER_NAME, "token_path")
CREDENTIALS_PATH = get_provider_config_value(PROVIDER_NAME, "credentials_path")
CALLBACK_URL = get_provider_config_value(PROVIDER_NAME, "callback_url")
SCOPES = get_provider_config_value(PROVIDER_NAME, "scopes")

app = FastAPI(title="Your Provider Auth Server")

@app.get("/auth")
async def start_auth(callback_url: Optional[str] = Query(None)):
    """Start OAuth flow by redirecting to provider's authorization URL."""
    try:
        # Check if we already have valid credentials
        if get_credentials():
            return JSONResponse(content={"message": "Already authenticated"})

        # 🟡 CUSTOMIZE: Build OAuth authorization URL for your provider
        auth_url = f"https://auth.yourprovider.com/oauth?client_id=XYZ&redirect_uri={callback_url or CALLBACK_URL}&scope={' '.join(SCOPES)}&response_type=code"
        return RedirectResponse(auth_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auth/callback")
async def auth_callback(code: str = Query(...)):
    """Handle OAuth redirect and exchange code for token."""
    try:
        # 🟡 CUSTOMIZE: Exchange code for token using your provider's API
        token = await exchange_code_for_token(code)
        save_credentials(token)
        return JSONResponse(content={"message": "Authentication successful"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def status():
    """Check token availability."""
    creds = get_credentials()
    return {"authenticated": bool(creds)}

@app.post("/auth/refresh")
async def refresh():
    """Force a manual token refresh."""
    success, message = await refresh_token()
    if not success:
        raise HTTPException(400, detail=message)
    return {"message": message}

# 🔴 CRITICAL: This function is called by server.py for local authentication
def run_auth_server(host: str = "localhost", port: int = 8000):
    """
    Run auth server with signal handling.
    
    This function is called by server.py when using --local-auth flag:
    
    server.py usage:
    if args.local_auth:
        port = provider_config.get('port', args.port)
        callback_url = provider_config.get('callback_url', f"http://{args.host}:{port}/auth/callback")
        print(f"Starting local authentication server for {args.provider} at http://{args.host}:{port}")
        print("Available endpoints:")
        print("  - /auth   : Start OAuth authentication flow")
        print("  - /status : Check authentication status") 
        print("  - /auth/callback : OAuth callback endpoint")
        print(f"Callback URL: {callback_url}")
        print(f"Token will be stored at: {provider_config.get('token_path', 'default location')}")
        print("Press CTRL+C to stop the server")
        server_auth_module.run_auth_server(port=port, host=args.host)
    """
    config = uvicorn.Config(app, host=host, port=port)
    server = uvicorn.Server(config)

    # Handle graceful shutdown
    def signal_handler(signum, frame):
        print("\nReceived signal to terminate. Shutting down...")
        asyncio.create_task(server.shutdown())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print(f"\nAuth server running at: http://{host}:{port}")
    print(f"Default callback URL: {CALLBACK_URL}")
    server.run()

# 🟡 CUSTOMIZE: Implement this function for your provider's OAuth flow
async def exchange_code_for_token(code: str):
    """Exchange OAuth code for access token - implement for your provider."""
    # Your implementation here
    pass
```

### 🔴 api/auth.py (MANDATORY STRUCTURE)

This file manages token storage and must use the `_token_info` pattern for sharing credentials across all imports.

```python
import datetime
import logging
import os
import sys
from typing import Optional, Dict, Any
from pathlib import Path

from src.mcp_core.engine.provider_loader import get_provider_config_value

# Set up logging
logger = logging.getLogger(__name__)

# Provider name
PROVIDER_NAME = "your_provider"

# Get configuration values
DEFAULT_TOKEN_PATH = get_provider_config_value(PROVIDER_NAME, "token_path")
SCOPES = get_provider_config_value(PROVIDER_NAME, "scopes")

# Ensure token path is absolute
if not os.path.isabs(DEFAULT_TOKEN_PATH):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
    DEFAULT_TOKEN_PATH = os.path.join(project_root, DEFAULT_TOKEN_PATH)
    logger.info(f"Converted token path to absolute path: {DEFAULT_TOKEN_PATH}")

# 🔴 CRITICAL: Module-level token storage for sharing across all imports
if not hasattr(sys.modules[__name__], '_token_info'):
    setattr(sys.modules[__name__], '_token_info', {
        'credentials': None,
        'last_refresh': None,
        'token_path': DEFAULT_TOKEN_PATH
    })

def get_token_info() -> Dict[str, Any]:
    """Get the module-level token info dictionary."""
    return getattr(sys.modules[__name__], '_token_info')

# For backward compatibility
token_info = get_token_info()

def set_token_path(path: str) -> None:
    """Set the global token path for OAuth storage."""
    token_info = get_token_info()
    token_info['token_path'] = path
    logger.info(f"Token path set to: {path}")

# 🔴 CRITICAL: This function must be available and working
def get_credentials(token_path: Optional[str] = None):
    """
    Gets valid user credentials from storage or memory.
    
    🔴 CRITICAL: All API modules must call this function before making API requests.
    """
    token_info = get_token_info()

    if token_path is None:
        token_path = token_info['token_path']

    creds = token_info['credentials']

    # If no credentials in memory, try to load from file
    if not creds:
        token_path = Path(token_path)
        if token_path.exists():
            try:
                # 🟡 CUSTOMIZE: Load credentials using your provider's method
                # For Google: Credentials.from_authorized_user_file(str(token_path), SCOPES)
                # For others: implement your own loading logic
                creds = load_credentials_from_file(str(token_path))
                token_info['credentials'] = creds
            except Exception as e:
                logger.error(f"Error loading credentials from file: {str(e)}")
                return None

    # If we have credentials that need refresh
    if creds and needs_refresh(creds):
        try:
            # 🟡 CUSTOMIZE: Refresh credentials using your provider's method
            creds = refresh_credentials(creds)
            save_credentials(creds, token_path)
        except Exception as e:
            logger.error(f"Error refreshing credentials: {str(e)}")
            return None

    return creds if is_valid(creds) else None

def save_credentials(creds, token_path: Optional[str] = None) -> None:
    """Save credentials to file and update in-memory cache."""
    token_info = get_token_info()

    if token_path is None:
        token_path = token_info['token_path']

    # Save to file
    token_path = Path(token_path)
    with open(token_path, 'w') as token:
        # 🟡 CUSTOMIZE: Save credentials using your provider's format
        token.write(serialize_credentials(creds))

    # Update in-memory cache
    token_info['credentials'] = creds
    token_info['last_refresh'] = datetime.datetime.utcnow()

async def refresh_token(token_path: Optional[str] = None) -> tuple[bool, str]:
    """Attempt to refresh the current token."""
    # 🟡 CUSTOMIZE: Implement token refresh logic for your provider
    pass

# 🟡 CUSTOMIZE: Implement these helper functions for your provider
def load_credentials_from_file(file_path: str):
    """Load credentials from file - implement for your provider."""
    pass

def needs_refresh(creds) -> bool:
    """Check if credentials need refresh - implement for your provider."""
    pass

def refresh_credentials(creds):
    """Refresh credentials - implement for your provider."""
    pass

def is_valid(creds) -> bool:
    """Check if credentials are valid - implement for your provider."""
    pass

def serialize_credentials(creds) -> str:
    """Serialize credentials to string - implement for your provider."""
    pass
```

## 3. API Implementation (FLEXIBLE)

🟡 **API modules can be customized based on your chat platform's requirements, but must always use `get_credentials()` from `auth.py` before making API calls.**

### Pattern for API Modules

```python
import logging
from typing import Dict, Optional, Any

# 🟡 CUSTOMIZE: Import your provider's SDK or HTTP client
from your_provider_sdk import YourProviderClient

# 🔴 CRITICAL: Always import get_credentials from auth.py
from src.providers.your_provider.api.auth import get_credentials

logger = logging.getLogger(__name__)

async def create_message(space_name: str, text: str, **kwargs) -> Dict[str, Any]:
    """Creates a new message in a space."""
    try:
        # 🔴 CRITICAL: Always get credentials before API calls
        creds = get_credentials()
        if not creds:
            raise Exception("No valid credentials found. Please authenticate first.")

        # 🟡 CUSTOMIZE: Use your provider's SDK/API method
        client = YourProviderClient(credentials=creds)
        response = client.messages.create(
            space=space_name,
            text=text,
            **kwargs
        )

        return response

    except Exception as e:
        logger.error(f"Failed to create message: {str(e)}")
        raise Exception(f"Failed to create message: {str(e)}")

# Implement other API functions following the same pattern:
# - Always call get_credentials() first
# - Handle errors gracefully
# - Return structured data
```

## 4. Tool Implementation (FLEXIBLE)

🟡 **Tools can be customized, but must use the `tool` decorator from your provider's `mcp_instance.py`.**

### Pattern for Tool Implementation

```python
import logging

# 🟡 FLEXIBLE: Import your API functions
from src.providers.your_provider.api.messages import create_message

# 🔴 CRITICAL: Always import tool from your provider's mcp_instance
from src.providers.your_provider.mcp_instance import tool

logger = logging.getLogger(__name__)

# 🔴 CRITICAL: Use @tool() decorator for central registration
@tool()
async def send_message_tool(space_name: str, text: str) -> dict:
    """
    Send a text message to a space.

    Args:
        space_name: The resource name of the space to send the message to
        text: Text content of the message
              
    Returns:
        The created message object
    """
    # Ensure proper space name format (customize as needed)
    if not space_name.startswith('spaces/'):
        space_name = f"spaces/{space_name}"
        
    try:
        logger.info(f"Sending message to {space_name}")
        return await create_message(space_name, text)
    except Exception as e:
        logger.error(f"Failed to send message: {str(e)}")
        raise ValueError(f"Failed to send message: {str(e)}")

# Implement additional tools following the same pattern:
# - Use @tool() decorator from mcp_instance
# - Clear docstrings with parameter descriptions
# - Proper error handling
# - Return structured data
```

## 5. Search Configuration (OPTIONAL)

🟢 **Only needed if your provider supports advanced search functionality.**

Add to provider-config.yaml:
```yaml
providers:
  your_provider:
    # Other config...
    search_config_path: "src/providers/your_provider/utils/search_config.yaml"
```

Create `utils/search_config.yaml`:
```yaml
search_modes:
  - name: "regex"
    enabled: true
    description: "Regular expression pattern matching"
    weight: 1.2
    options:
      ignore_case: true
      
  - name: "exact"
    enabled: true
    description: "Basic case-insensitive substring matching"
    weight: 1.0

search:
  default_mode: "regex"
  max_results_per_space: 50
```

---

## Summary of Critical Requirements

### 🔴 MANDATORY (Must Follow Exactly)

1. **Directory name** = **config key** in `provider-config.yaml`
2. **`mcp_instance.py`**: Use exact structure with `tool_decorator_factory`
3. **`server_auth.py`**: Must include `run_auth_server()` function (called by server.py)
4. **`api/auth.py`**: Must use `_token_info` pattern and provide `get_credentials()` function
5. **All tools**: Must use `@tool()` decorator from your provider's `mcp_instance`
6. **All API modules**: Must call `get_credentials()` before making API requests

### 🟡 FLEXIBLE (Customize as Needed)

- API function implementations (messages, spaces, users, etc.)  
- Tool implementations (beyond using the `@tool` decorator)
- OAuth flow specifics in `server_auth.py` endpoints
- Credential loading/saving logic in `auth.py` helper functions

### 🟢 OPTIONAL

- Search configuration and related tools
- Additional utility functions
- Custom error handling beyond the basic patterns

Following these patterns ensures your provider integrates seamlessly with the Multi-Provider MCP Server framework while giving you flexibility to adapt to your specific chat platform's API.