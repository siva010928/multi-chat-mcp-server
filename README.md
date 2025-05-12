# Google Chat MCP Server

A Model Control Protocol (MCP) server for interacting with Google Chat through Claude and other AI assistants in MCP clients like Cursor.

## Project Overview

This project provides a server implementation for the Model Control Protocol (MCP) that integrates with the Google Chat API, allowing AI assistants to interact with Google Chat. Once configured, the MCP client (e.g., Cursor) will manage the server lifecycle automatically when needed.

## Features

- Authentication with Google Chat API using OAuth 2.0
- Sending and reading messages across spaces and direct messages
- Managing spaces and members
- Adding emoji reactions to messages
- Searching messages using text queries
- Sending file contents as messages
- Finding mentions of your username in messages
- Getting user profile information
- Working with message threads and replies
- Batch sending of multiple messages

## Setup

### Prerequisites

- **Google Workspace Account**: This tool only works with Google Workspace accounts (formerly G Suite) in an organization. Personal Google accounts cannot access the Google Chat API.
- **Google Cloud Platform Project**: You must be able to create and configure a project in Google Cloud Console.
- **OAuth 2.0 Understanding**: Basic familiarity with OAuth authentication flows is helpful.
- **Python 3.9+**: The server requires Python 3.9 or newer.

### 1. Installation

1. Clone this repository:

```bash
git clone https://github.com/twlabs/AIFSD-google-chat-mcp.git
cd AIFSD-google-chat-mcp
```

2. Create a virtual environment (optional but recommended):

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install requirements:

```bash
pip install -r requirements.txt
```

### 2. Authentication Setup

1. **Create a Google Cloud Platform project**:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Google Chat API for your project:
     - Navigate to "APIs & Services" > "Library"
     - Search for "Google Chat API" and enable it
   - Additionally, enable the People API if you plan to use the `get_my_mentions` tool or access user information:
     - Navigate to "APIs & Services" > "Library"
     - Search for "People API" and enable it

   > **Important**: This tool can only be used with Google Workspace accounts in an organization. Personal Google accounts cannot create Google Chat API projects. You must have a Google Workspace account to set up OAuth credentials and use this tool.

2. **Set up OAuth credentials**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Select "Web application" as the application type (not Desktop app)
   - Give it a name (e.g., "Google Chat MCP Client")
   - Under "Authorized JavaScript origins" add: `http://localhost:8000`
   - Under "Authorized redirect URIs" add: `http://localhost:8000/auth/callback`
   - Click "Create" and download the JSON file
   - **Important**: You must rename the downloaded file to `credentials.json` and place it in the root directory of this project. The authentication process specifically looks for this filename and cannot proceed without it.
   - This credentials.json file contains the client configuration that Google uses to verify your application's identity during the OAuth flow. Without it, authentication will fail.
   - Reference: [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)

3. **Authenticate with Google**:
   - Run the authentication server:
     ```bash
     python server.py -local-auth
     ```
   - Visit http://localhost:8000/auth in your browser
   - Follow the OAuth flow to grant permissions
   - After successful authentication, a `token.json` file will be generated in your project root directory
   - This token will be used for all future API requests, and the MCP server will automatically refresh it when needed

### 3. Configure Your MCP Client

Add the Google Chat MCP server to your MCP client's configuration. For Cursor, edit your `~/.cursor/mcp.json` file:

```json
{
  "google_chat": {
    "command": "uv",
    "args": [
      "--directory",
      "/path/to/AIFSD-google-chat-mcp",
      "run",
      "server.py",
      "--token-path",
      "/path/to/AIFSD-google-chat-mcp/token.json"
    ]
  }
}
```

Replace `/path/to/AIFSD-google-chat-mcp` with the actual path to your cloned repository.

> **Note**: After completing this setup, you can close this project. The MCP client (e.g., Cursor) will automatically start and manage the server process when you use Google Chat MCP tools in your AI assistant. You don't need to manually start the server each time - the AI tool's MCP client will handle starting and stopping the server as needed. Once you've authenticated and configured everything, you can move on to other projects while still having access to all the Google Chat MCP functionality.

## Available Tools

The following tools are available to interact with Google Chat:


### Chat Space Management
- **`mcp_google_chat_get_chat_spaces`** - List all Google Chat spaces you have access to
  - Parameters: none
  - Returns: Array of space objects with details like name, type, display name

- **`mcp_google_chat_get_space_messages`** - List messages from a specific space with date filtering
  - Parameters: 
    - `space_name` (string, required): Space identifier (e.g., "spaces/AAQAtjsc9v4")
    - `start_date` (string, required): Date in YYYY-MM-DD format
    - `end_date` (string, optional): Date in YYYY-MM-DD format
  - Returns: Array of message objects from the specified space

### Messaging
- **`mcp_google_chat_send_message`** - Send a text message to a Google Chat space
  - Parameters: 
    - `space_name` (string, required): Space identifier
    - `text` (string, required): Message content
  - Returns: Created message object

- **`mcp_google_chat_reply_to_message_thread`** - Reply to an existing thread in a space
  - Parameters:
    - `space_name` (string, required): Space identifier
    - `thread_key` (string, required): Thread identifier
    - `text` (string, required): Reply content
  - Returns: Created message object

- **`mcp_google_chat_update_chat_message`** - Update an existing message
  - Parameters:
    - `message_name` (string, required): Full resource name of message
    - `new_text` (string, required): Updated text content
  - Returns: Updated message object

- **`mcp_google_chat_delete_chat_message`** - Delete a message
  - Parameters:
    - `message_name` (string, required): Full resource name of message
  - Returns: Empty response on success

### Message Interactions
- **`mcp_google_chat_add_emoji_reaction`** - Add an emoji reaction to a message
  - Parameters:
    - `message_name` (string, required): Message identifier
    - `emoji` (string, required): Unicode emoji character
  - Returns: Created reaction object

- **`mcp_google_chat_get_chat_message`** - Get details about a specific message
  - Parameters:
    - `message_name` (string, required): Message identifier
  - Returns: Full message object

### Search & Filtering
- **`mcp_google_chat_search_messages`** - Search for messages across spaces
  - Parameters:
    - `query` (string, required): Search text
    - `spaces` (array of strings, optional): List of spaces to search in
    - `max_results` (integer, optional): Maximum number of results
  - Returns: Array of matching message objects

- **`mcp_google_chat_get_my_mentions`** - Find messages that mention you
  - Parameters:
    - `days` (integer, optional): Number of days to look back (default: 7)
    - `space_id` (string, optional): Limit search to a specific space
  - Returns: Array of messages mentioning you

### User Information
- **`mcp_google_chat_get_my_user_info`** - Get your Google Chat user details
  - Parameters: none
  - Returns: User object with details like email, display name

### Space Management
- **`mcp_google_chat_manage_space_members`** - Add or remove members from a space
  - Parameters:
    - `space_name` (string, required): Space identifier
    - `operation` (string, required): Either "add" or "remove"
    - `user_emails` (array of strings, required): Email addresses to add/remove
  - Returns: Response with operation results

### File Handling
- **`mcp_google_chat_send_file_message`** - Send a message with file contents
  - Parameters:
    - `space_name` (string, required): Space identifier
    - `file_path` (string, required): Path to the file
    - `message_text` (string, optional): Accompanying message
  - Returns: Created message object

### Batch Operations
- **`mcp_google_chat_batch_send_messages`** - Send multiple messages in one operation
  - Parameters:
    - `messages` (array of objects, required): List of message objects to send
  - Returns: Results for each message

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

### Switching Accounts or Logging Out

To switch to a different Google account or log out from your current account:

1. Delete the token.json file from your project directory:
   ```bash
   rm token.json
   ```

2. If the server is already running, stop it first (e.g., use Ctrl+C)

3. Restart the authentication server:
   ```bash
   python server.py -local-auth
   ```

4. Visit http://localhost:8000/auth in your browser and authenticate with the desired Google account

This process will create a new token.json file with the credentials for the new account.

### When to Re-authenticate

You'll need to re-authenticate (delete `token.json` and go through the auth flow) in these cases:

1. You modified the `SCOPES` list in the code (added or removed permissions)
2. The refresh token has expired (rare, typically after 6 months of inactivity)
3. You've revoked access for the application in your Google account
4. You want to authenticate with a different Google account

### Troubleshooting

- **Authentication Errors**: If you encounter "Invalid Credentials" errors, try running `refresh_token.py` or re-authenticate completely
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
- **server.py**: MCP server and authentication web server
- **server_auth.py**: Authentication helpers
- **refresh_token.py**: Utility script for refreshing tokens
- **check_token.py**: Utility script for checking token status
- **tests/**: Unit tests for all functionality
- **TOKEN_MANAGEMENT.md**: Detailed guide to token management
- **TESTING.md**: Information about testing setup and coverage

## License

MIT License

