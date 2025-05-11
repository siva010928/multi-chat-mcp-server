# Google Chat MCP Server

A Model Control Protocol (MCP) server for interacting with Google Chat through Claude and other AI assistants in Cursor.

## Project Overview

This project provides a server implementation for the Model Control Protocol (MCP) that integrates with Google Chat API, allowing AI assistants in Cursor to interact with Google Chat.

## Features (Coming Soon)

- Authentication with Google Chat API
- Sending and reading messages
- Managing spaces and members
- Adding emoji reactions
- Searching messages
- And more...

## Development

This project is under active development. More details will be provided as features are implemented.

## License

MIT License

## Features

- Authentication with Google Chat API
- Sending and reading messages
- Managing spaces and members
- Adding emoji reactions
- Searching messages
- Sending file contents as messages
- Finding mentions of your username in messages
- Getting user profile information
- Working with message threads

## Setup

1. Create a virtual environment (optional but recommended):

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install requirements:

```bash
pip install -r requirements.txt
```

3. Configure authentication:

   a. Create a Google Cloud Platform project with the Google Chat API enabled
   b. Create OAuth 2.0 credentials and download them as `credentials.json` to the project root
   c. Run the authentication server:

```bash
python server.py -local-auth
```

4. Visit http://localhost:8000/auth in your browser to authenticate

5. Start the MCP server:

```bash
python server.py
```

6. Configure Cursor to use the server:

Add this to your `~/.cursor/mcp.json` file:

```json
{
  "mcpServers": {
    "GoogleChatMCP": {
      "command": "python",
      "args": [
        "server.py"
      ],
      "cwd": "/path/to/google-chat-mcp-server"
    }
  }
}
```

## Usage Examples

With the server running, you can use Claude in Cursor to:

- List Google Chat spaces: `mcp_google_chat_get_chat_spaces`
- Send a message: `mcp_google_chat_send_message`
- Search for messages: `mcp_google_chat_search_messages`
- Find messages that mention you: `mcp_google_chat_get_my_mentions`
- Get your user info: `mcp_google_chat_get_my_user_info`
- Add emoji reactions: `mcp_google_chat_add_emoji_reaction`
- Send file contents: `mcp_google_chat_send_file_message`

## Authentication & Token Management

The Google Chat MCP server uses OAuth 2.0 authentication with refresh tokens to maintain long-term access to the Google Chat API without frequent manual re-authentication.

> **Detailed Guide**: See [TOKEN_MANAGEMENT.md](TOKEN_MANAGEMENT.md) for comprehensive documentation on token management, authentication, and troubleshooting.

### How Tokens Work

- **Access Token**: Short-lived (usually 1 hour) token for API access
- **Refresh Token**: Long-lived token stored in `token.json` that allows getting new access tokens without re-authenticating
- **Automatic Refresh**: The system automatically refreshes access tokens when they expire

### Token Storage

- Tokens are stored in `token.json` in the project root directory (configurable with `--token-path`)
- The token file contains both access and refresh tokens
- Tokens are also cached in memory for better performance

### Automatic Token Refresh

In most cases, you never need to manually refresh tokens. The server will:

1. Check if the current token is expired before making any API call
2. Automatically use the refresh token to obtain a new access token when needed
3. Save the updated token back to the `token.json` file

### Manual Token Management

#### Checking Token Status

1. **Using the check_token.py utility** (recommended):
   ```bash
   # Simply run the script
   python check_token.py
   
   # Or with a custom token path
   python check_token.py --token-path /path/to/custom/token.json
   ```

2. Using the auth server:
   ```bash
   # Start the auth server
   python server.py -local-auth
   
   # Visit in browser to check token status
   http://localhost:8000/status
   ```

#### Manually Refreshing Tokens

1. **Using the refresh_token.py utility** (recommended):
   ```bash
   # Simply run the script
   python refresh_token.py
   
   # Or with a custom token path
   python refresh_token.py --token-path /path/to/custom/token.json
   ```

2. Using the auth server:
   ```bash
   # Start the auth server
   python server.py -local-auth
   
   # Visit in browser to trigger refresh
   http://localhost:8000/auth/refresh
   ```

3. Using a Python script:
   ```python
   import asyncio
   from google_chat import refresh_token
   
   async def main():
       success, message = await refresh_token()
       print(f"Token refresh status: {success}, {message}")
   
   asyncio.run(main())
   ```

#### Force Re-authentication

If you need to completely re-authenticate (e.g., when changing required permissions):

1. Delete the token file:
   ```bash
   rm token.json
   ```
   
2. Run the authentication server:
   ```bash
   python server.py -local-auth
   ```
   
3. Visit http://localhost:8000/auth to start the authentication flow

### When to Re-authenticate

You'll need to re-authenticate (delete `token.json` and go through the auth flow) in these cases:

1. You modified the `SCOPES` list in the code (added or removed permissions)
2. The refresh token has expired (rare, typically after 6 months of inactivity)
3. You've revoked access for the application in your Google account
4. You want to authenticate with a different Google account

### Troubleshooting

- **Authentication Errors**: If you encounter "Invalid Credentials" errors, try running the manual refresh or re-authenticate completely
- **Missing Permissions**: If you get "Permission Denied" errors, check the `SCOPES` list and re-authenticate after ensuring all required permissions are included

## Development

### Running Tests

Run the full test suite:

```bash
python run_tests.py
```

Or use pytest with coverage:

```bash
python -m pytest
```

View the HTML coverage report in the `htmlcov` directory.

### Project Structure

- **google_chat.py**: Core library with all API functions
- **server.py**: Authentication web server
- **server_auth.py**: Authentication helpers
- **refresh_token.py**: Utility script for refreshing tokens
- **check_token.py**: Utility script for checking token status
- **tests/**: Unit tests for all functionality
- **TOKEN_MANAGEMENT.md**: Detailed guide to token management
- **TESTING.md**: Information about testing setup and coverage

## Testing

The project includes a comprehensive test suite that covers the core functionality. 

To run tests:

```bash
python -m pytest
```

For more detailed information about testing, see [TESTING.md](TESTING.md).

