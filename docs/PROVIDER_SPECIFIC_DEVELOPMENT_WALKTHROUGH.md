# Provider Development Guide

This guide shows you how to add a new chat provider to the Multi-Provider MCP Server framework with maximum flexibility for your specific use cases.

## Table of Contents

1. [Overview](#overview)
2. [Core Requirements](#core-requirements)
3. [Example Provider Setup](#example-provider-setup)
4. [Running Your Provider](#running-your-provider)
5. [Authentication Flow Explained](#authentication-flow-explained)

## Overview

The Multi-Provider MCP Server framework is designed for **maximum flexibility**. You can create providers for any chat platform with any tools you need for your specific use cases.

### What You Must Follow (Only 3 Files)

🔴 **MANDATORY** - These 3 files follow strict patterns:
- `mcp_instance.py` - Creates MCP instance and tool decorator
- `server_auth.py` - OAuth server with `run_auth_server()` function  
- `api/auth.py` - Token management with `get_credentials()` function

🟡 **COMPLETELY FLEXIBLE** - Everything else:
- Your API modules (any structure, any functions)
- Your tools (any functionality you need)
- Directory structure beyond the 3 core files

### Key Rule
**Always call `get_credentials()` before any chat provider API calls** - this ensures proper authentication across your entire provider.

## Core Requirements

### 1. Directory Structure (Minimal)

```
src/providers/your_provider/
├── api/
│   └── auth.py         # 🔴 MANDATORY - Token management
├── mcp_instance.py     # 🔴 MANDATORY - MCP setup
├── server_auth.py      # 🔴 MANDATORY - OAuth server
└── [your custom files] # 🟡 FLEXIBLE - Anything you need
```

### 2. Provider Registration

Add to `provider-config.yaml` (directory name must match config key):

```yaml
providers:
  your_provider:  # 🔴 MUST match directory name exactly
    name: "Your Provider Name"
    description: "Your provider description"
    token_path: "src/providers/your_provider/token.json"
    credentials_path: "src/providers/your_provider/credentials.json"
    callback_url: "http://localhost:8000/auth/callback"
    port: 8000
    scopes:
      - "your_required_scope1"
      - "your_required_scope2"
```

## Example Provider Setup

Let's create a complete working example for a fictional "ChatPlatform" provider.

### Step 1: Create `mcp_instance.py`

```python
"""MCP instance for ChatPlatform provider."""

import logging
from fastmcp import FastMCP
from src.mcp_core.engine.provider_loader import get_provider_config_value
from src.mcp_core.tools.tool_decorator import tool_decorator_factory

logger = logging.getLogger(__name__)

# 🔴 CRITICAL: Must match directory name and config key
PROVIDER_NAME = "chatplatform"

# Get config values
name = get_provider_config_value(PROVIDER_NAME, "name")
description = get_provider_config_value(PROVIDER_NAME, "description")

# Create MCP instance
logger.info(f"Creating FastMCP instance for {name}")
mcp = FastMCP(name, description=description)

# 🔴 CRITICAL: Create centralized tool decorator
tool = tool_decorator_factory(PROVIDER_NAME, mcp)
```

### Step 2: 🔴 Create api/auth.py (MANDATORY STRUCTURE)

This file manages token storage and must use the `_token_info` pattern for sharing credentials across all imports.

```python
"""Authentication management for ChatPlatform."""

import datetime
import json
import logging
import os
import sys
from typing import Optional, Dict, Any
from pathlib import Path

# Example: Using requests for HTTP calls (customize for your provider)
import requests

from src.mcp_core.engine.provider_loader import get_provider_config_value

logger = logging.getLogger(__name__)
PROVIDER_NAME = "chatplatform"

# Get configuration
DEFAULT_TOKEN_PATH = get_provider_config_value(PROVIDER_NAME, "token_path")
CREDENTIALS_PATH = get_provider_config_value(PROVIDER_NAME, "credentials_path")
SCOPES = get_provider_config_value(PROVIDER_NAME, "scopes")

# Make token path absolute
if not os.path.isabs(DEFAULT_TOKEN_PATH):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
    DEFAULT_TOKEN_PATH = os.path.join(project_root, DEFAULT_TOKEN_PATH)

# 🔴 CRITICAL: Module-level token storage for sharing across imports
if not hasattr(sys.modules[__name__], '_token_info'):
    setattr(sys.modules[__name__], '_token_info', {
        'credentials': None,
        'last_refresh': None,
        'token_path': DEFAULT_TOKEN_PATH
    })

def get_token_info() -> Dict[str, Any]:
    return getattr(sys.modules[__name__], '_token_info')

token_info = get_token_info()

def get_credentials(token_path: Optional[str] = None):
    """
    🔴 CRITICAL: This function MUST work - all API calls depend on it.
    
    Returns valid credentials or None if authentication needed.
    """
    token_info = get_token_info()
    
    if token_path is None:
        token_path = token_info['token_path']
    
    creds = token_info['credentials']
    
    # Load from file if not in memory
    if not creds:
        token_path = Path(token_path)
        if token_path.exists():
            try:
                with open(token_path, 'r') as f:
                    token_data = json.load(f)
                    creds = create_credentials_from_token(token_data)
                    token_info['credentials'] = creds
            except Exception as e:
                logger.error(f"Error loading credentials: {e}")
                return None
    
    # Refresh if needed
    if creds and is_expired(creds):
        try:
            creds = refresh_credentials(creds)
            save_credentials(creds)
        except Exception as e:
            logger.error(f"Error refreshing credentials: {e}")
            return None
    
    return creds if (creds and is_valid(creds)) else None

def save_credentials(creds, token_path: Optional[str] = None):
    """Save credentials to file and memory."""
    token_info = get_token_info()
    
    if token_path is None:
        token_path = token_info['token_path']
    
    # Save to file
    with open(token_path, 'w') as f:
        json.dump(serialize_credentials(creds), f)
    
    # Update memory
    token_info['credentials'] = creds
    token_info['last_refresh'] = datetime.datetime.utcnow()
```

### Step 3: 🔴 Create server_auth.py (MANDATORY STRUCTURE)

This file handles OAuth authentication and **MUST** include the `run_auth_server()` function as it's called by `server.py` during local authentication.


```python
"""OAuth authentication server for ChatPlatform."""

import asyncio
import json
import signal
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse, JSONResponse

from src.providers.chatplatform.api.auth import (
    get_credentials, save_credentials, exchange_code_for_token, create_credentials_from_token
)
from src.mcp_core.engine.provider_loader import get_provider_config_value

PROVIDER_NAME = "chatplatform"

# Get configuration
CREDENTIALS_PATH = get_provider_config_value(PROVIDER_NAME, "credentials_path")
CALLBACK_URL = get_provider_config_value(PROVIDER_NAME, "callback_url")
SCOPES = get_provider_config_value(PROVIDER_NAME, "scopes")

app = FastAPI(title="ChatPlatform Auth Server")

@app.get("/auth")
async def start_auth(callback_url: Optional[str] = Query(None)):
    """Start OAuth flow."""
    try:
        if get_credentials():
            return JSONResponse(content={"message": "Already authenticated"})

        # Load client credentials
        with open(CREDENTIALS_PATH, 'r') as f:
            client_creds = json.load(f)

        # 🟡 CUSTOMIZE: Build authorization URL for your provider
        auth_url = (
            f"https://auth.chatplatform.com/oauth/authorize"
            f"?client_id={client_creds['client_id']}"
            f"&redirect_uri={callback_url or CALLBACK_URL}"
            f"&scope={' '.join(SCOPES)}"
            f"&response_type=code"
        )
        
        return RedirectResponse(auth_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auth/callback")
async def auth_callback(code: str = Query(...)):
    """Handle OAuth callback."""
    try:
        token_data = await exchange_code_for_token(code)
        creds = create_credentials_from_token(token_data)
        save_credentials(creds)
        return JSONResponse(content={"message": "Authentication successful"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def check_auth_status():
    """Check authentication status."""
    creds = get_credentials()
    return {"authenticated": bool(creds)}

# 🔴 CRITICAL: This function is called by server.py for local auth
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

    def signal_handler(signum, frame):
        print("\nShutting down auth server...")
        asyncio.create_task(server.shutdown())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print(f"\nAuth server running at: http://{host}:{port}")
    server.run()
```

### Step 4: Create Your Custom API and Tools

#### Now you have complete freedom! Here's an example:

#### 🟡 **API modules can be customized based on your chat platform's requirements, but must always use `get_credentials()` from `auth.py` before making API calls.**

### API Implementation (FLEXIBLE)

```python
# api/messaging.py - Your custom API module
from src.providers.chatplatform.api.auth import get_credentials
import requests

async def send_message(room_id: str, text: str):
    """Send message using ChatPlatform API."""
    # 🔴 CRITICAL: Always get credentials first
    creds = get_credentials()
    if not creds:
        raise Exception("Not authenticated")
    
    # Your custom API call
    response = requests.post(
        f"https://api.chatplatform.com/rooms/{room_id}/messages",
        headers={"Authorization": f"Bearer {creds['access_token']}"},
        json={"text": text}
    )
    return response.json()
```

#### 🟡 **Tools can be customized, but must use the `tool` decorator from your provider's `mcp_instance.py`.**

### Tool Implementation (FLEXIBLE)

```python
# tools/chat_tools.py - Your custom tools
from src.providers.chatplatform.mcp_instance import tool
from src.providers.chatplatform.api.messaging import send_message

@tool()
async def send_chat_message(room_id: str, message: str) -> dict:
    """Send a message to a chat room."""
    return await send_message(room_id, message)
```
### Common Tool Patterns

When implementing tools, follow these common patterns:

**Tool Decarotor** Each tool must be decorated using @tool() from your provider's mcp_instance.py.
This is critical because:

✅ It registers the tool with the local FastMCP instance

✅ It automatically syncs the tool with the central tool registry

✅ It ensures your tools are discoverable and invokable by MCP-compatible AI agents

1. **Naming**: Use a consistent naming scheme with the _tool suffix
2. **Logging**: Add logging for debugging
3. **Error Handling**: Wrap API calls in try-except blocks with informative error messages
4. **Documentation**: Provide detailed docstrings with parameter descriptions and examples
5. **Serialization**: Ensure return values can be serialized to JSON

Remember that these tools will be directly called by AI assistants through the MCP protocol, so they should be designed with clear interfaces and helpful documentation.

## Running Your Provider

### 1. Setup OAuth Credentials

Create `credentials.json` in your provider directory:
```json
{
  "client_id": "your_oauth_client_id",
  "client_secret": "your_oauth_client_secret"
}
```

### 2. Start Authentication

```bash
python -m src.server --provider chatplatform --local-auth
```

This will:
- Start the auth server at `http://localhost:8000`
- Show available endpoints:
  - `/auth` - Start OAuth flow
  - `/status` - Check auth status  
  - `/auth/callback` - OAuth callback
- Create `token.json` after successful authentication

### 3. Run MCP Server

After authentication:
```bash
python -m src.server --provider chatplatform
```

Your provider is now running and ready for MCP connections!

## Authentication Flow Explained

Here's exactly what happens when you authenticate:

### 1. Server Startup
```bash
python -m src.server --provider chatplatform --local-auth
```

`server.py` calls your `run_auth_server()` function:
```python
# In server.py
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
    server_auth_module.run_auth_server(port=port, host=args.host)
```

### 2. OAuth Flow
1. **User visits** `http://localhost:8000/auth`
2. **Redirect** to your chat provider's OAuth page
3. **User grants permission**
4. **Provider redirects** back to `/auth/callback?code=ABC123`
5. **Code exchange** for access/refresh tokens via `exchange_code_for_token()`
6. **Tokens saved** to `token.json` and stored in `_token_info` module variable

### 3. Token Usage
- All API calls use `get_credentials()` which:
  - Checks `_token_info` module variable first (fast)
  - Loads from `token.json` if needed
  - Auto-refreshes expired tokens
  - Returns `None` if authentication required

### 4. Cross-Module Sharing
The `_token_info` module variable ensures credentials are shared across all imports:
```python
# In api/auth.py
_token_info = {'credentials': ..., 'last_refresh': ..., 'token_path': ...}

# Any module importing from auth.py gets the same token_info
from src.providers.chatplatform.api.auth import get_credentials
# Always returns the same shared credentials
```

This design ensures your provider works seamlessly with any chat platform's OAuth 2.0 flow while giving you complete flexibility for your specific use cases and API structure.

## Quick Start Guide

### Prerequisites

Before getting started with provider development, make sure you have the following prerequisites installed:

1. **Python 3.8+**: Required for running the MCP server
2. **uv**: Recommended package manager for MCP client integration
   ```bash
   pip install uv
   ```
   
   Using `uv` offers several advantages over standard Python virtual environments:
   - Faster dependency resolution and installation
   - Better caching of packages
   - Improved reproducibility with lockfiles
   - Enhanced compatibility with MCP clients
   
   While standard Python/pip can work for MCP client integration, `uv` is highly recommended for a smoother development experience and better performance.

3. **Git**: For version control
4. **OAuth Credentials**: From the chat platform you're integrating with

### Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/multi-chat-mcp-server.git
   cd multi-chat-mcp-server
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # Using uv (recommended)
   uv venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   
   # Or using standard Python
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   # Using uv (recommended)
   uv pip install -r requirements.txt
   
   # Or using standard pip
   pip install -r requirements.txt
   ```

4. **Copy your OAuth credentials**:
   Save your OAuth credentials as `credentials.json` in your provider directory.

### Test Integration

After developing your provider, you can test it with:

1. **Any MCP client**: Connect your MCP client to the server
2. **Claude or other AI assistants in Cursor**: Test with simple commands like:
   - "Catch me up with my team space"
   - "Update my team regarding this update"
   - "Find messages about [topic] in my chat"

This conversational interaction is the most effective way to test your provider's functionality, as it simulates how it will be used in real applications.

## Detailed Setup

### Prerequisites

1. **Python 3.8+**: Required for running the MCP server
2. **uv**: Recommended for MCP client integration
   
   `uv` is a Python packaging management tool that offers significant advantages for MCP client integration:
   - **Performance**: Up to 10-100x faster than pip for dependency resolution
   - **Reliability**: Better handling of complex dependency graphs
   - **Reproducibility**: Advanced lockfile capabilities
   - **Isolation**: Improved environment isolation to prevent conflicts
   - **Compatibility**: Enhanced compatibility with MCP clients and agent tools
   
   Install uv with:
   ```bash
   pip install uv
   ```

3. **OAuth Credentials**: Required for authenticating with your chat platform
   - Client ID
   - Client Secret
   - Redirect URI (usually http://localhost:8000/auth/callback)