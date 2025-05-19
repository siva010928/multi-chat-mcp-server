## Project Overview

This project provides a server implementation for the Model Control Protocol (MCP) that integrates with the Google Chat API, allowing AI assistants to interact with Google Chat. Once configured, the MCP client (e.g., Cursor) will manage the server lifecycle automatically when needed.

## Architecture Diagrams

The following diagrams provide a visual representation of the Google Chat MCP server's architecture and workflows:

### System Architecture
![System Architecture](diagrams/architectural_diagram.svg)
*High-level architecture diagram showing the main components of the Google Chat MCP system and their interactions.*

### Authentication Flow
![Authentication Flow](diagrams/authentication_flow_diagram.svg)
*Detailed authentication flow showing the OAuth 2.0 process used to authenticate with Google Chat API.*

### Data Flow
![Data Flow](diagrams/data_flow_diagram.svg)
*Complete data flow sequence from user request through the MCP client, server, authentication, and API interactions.*

### User Workflow
![User Workflow](diagrams/user_flow_diagram.svg)
*End-to-end user workflow covering setup, configuration, and usage patterns for the Google Chat MCP.*

### Tools Structure
![Tools Structure](diagrams/tools_diagram.svg)
*Structured overview of all available tools and their parameters for interacting with Google Chat.*

## Features

- Authentication with Google Chat API using OAuth 2.0
- Sending and reading messages across spaces and direct messages
- Pagination support for large result sets
- Enhanced sender information with complete user profiles
- Managing spaces and members
- Adding emoji reactions to messages
- Searching messages using text queries
- Sending file contents as messages
- Finding mentions of your username in messages
- Getting user profile information
- Working with message threads and replies
- Batch sending of multiple messages
- Conversation summarization and participant analysis

## Setup

### Prerequisites

- **Google Workspace Account**: This tool only works with Google Workspace accounts (formerly G Suite) in an organization. Personal Google accounts cannot access the Google Chat API.
- **Google Cloud Platform Project**: You must be able to create and configure a project in Google Cloud Console.
- **OAuth 2.0 Understanding**: Basic familiarity with OAuth authentication flows is helpful.
- **Python 3.9+**: The server requires Python 3.9 or newer.
- **UV Package Manager**: This project uses UV for dependency management.

### 1. Installation

1. Clone this repository:

```bash
git clone https://github.com/twlabs/AIFSD-google-chat-mcp.git
cd AIFSD-google-chat-mcp
```

2. Install UV if you don't have it already:

```bash
# Install UV using pip
pip install uv

# Or on macOS using Homebrew
brew install uv
```

3. Create a virtual environment and install requirements using UV (recommended):

```bash
# Create virtual environment and install requirements in one step
uv venv .venv

# Activate the environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install requirements
uv pip install -r requirements.txt
```

4. Alternatively, you can use traditional pip:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
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
      "/path/to/google-chat-mcp-server",
      "run",
      "-m",
      "src.server",
      "--token-path",
      "/path/to/google-chat-mcp-server/token.json"
    ]
  }
}
```

Replace `/path/to/google-chat-mcp-server` with the actual path to your repository.

**Important File Locations:**
- `credentials.json`: Must be placed in the root directory of the project
- `token.json`: Generated in the root directory after authentication, can be configured with `--token-path`
- `search_config.yaml`: Located in the root directory, configures search behavior

> **Note**: After completing this setup, you can close this project. The MCP client (e.g., Cursor) will automatically start and manage the server process when you use Google Chat MCP tools in your AI assistant. You don't need to manually start the server each time - the AI tool's MCP client will handle starting and stopping the server as needed. Once you've authenticated and configured everything, you can move on to other projects while still having access to all the Google Chat MCP functionality.

### 4. Running Tests

The project includes a comprehensive test suite. To run the tests:

```bash
# Activate your virtual environment if not already active
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run all tests with coverage report
python -m pytest

# Run specific test modules
python -m pytest src/tools/tests/test_user_tools.py

# Run tests with detailed coverage information
python -m pytest src/tools/tests/ --cov=src.tools --cov-report=term-missing -v
```

The test structure is organized as follows:

```
src/
  tools/tests/           - Tests for MCP tools
  google_chat/tests/     - Tests for core functionality
```

See `TEST_IMPROVEMENTS.md` for detailed information about test coverage and future improvements.

## Available Tools

The following tools are available to interact with Google Chat:


### Chat Space Management
- **`mcp_google_chat_get_chat_spaces_tool`** - List all Google Chat spaces you have access to
  - Parameters: none
  - Returns: Array of space objects with details like name, type, display name

- **`mcp_google_chat_get_space_messages_tool`** - List messages from a specific space with date filtering
  - Parameters: 
    - `space_name` (string, required): Space identifier (e.g., "spaces/AAQAtjsc9v4")
    - `start_date` (string, required): Date in YYYY-MM-DD format
    - `end_date` (string, optional): Date in YYYY-MM-DD format
    - `include_sender_info` (boolean, optional): Whether to include detailed sender information
    - `page_size` (integer, optional): Maximum number of messages to return (default: 25, max: 1000)
    - `page_token` (string, optional): Token for retrieving the next page of results
    - `filter_str` (string, optional): Custom filter string in Google Chat API format
    - `order_by` (string, optional): Ordering format like "createTime DESC"
    - `show_deleted` (boolean, optional): Whether to include deleted messages
  - Returns: Dictionary containing an array of message objects and a nextPageToken for pagination

### Messaging
- **`mcp_google_chat_send_message_tool`** - Send a text message to a Google Chat space
  - Parameters: 
    - `space_name` (string, required): Space identifier
    - `text` (string, required): Message content
  - Returns: Created message object

- **`mcp_google_chat_reply_to_message_thread_tool`** - Reply to an existing thread in a space
  - Parameters:
    - `space_name` (string, required): Space identifier
    - `thread_key` (string, required): Thread identifier
    - `text` (string, required): Reply content
  - Returns: Created message object

- **`mcp_google_chat_update_chat_message_tool`** - Update an existing message
  - Parameters:
    - `message_name` (string, required): Full resource name of message
    - `new_text` (string, required): Updated text content
  - Returns: Updated message object

- **`mcp_google_chat_delete_chat_message_tool`** - Delete a message
  - Parameters:
    - `message_name` (string, required): Full resource name of message
  - Returns: Empty response on success

### Message Interactions
- **`mcp_google_chat_add_emoji_reaction_tool`** - Add an emoji reaction to a message
  - Parameters:
    - `message_name` (string, required): Message identifier
    - `emoji` (string, required): Unicode emoji character
  - Returns: Created reaction object

- **`mcp_google_chat_get_chat_message_tool`** - Get details about a specific message
  - Parameters:
    - `message_name` (string, required): Message identifier
    - `include_sender_info` (boolean, optional): Whether to include detailed sender information
  - Returns: Full message object

### Search & Filtering
- **`mcp_google_chat_search_messages_tool`** - Search for messages across spaces
  - Parameters:
    - `query` (string, required): Search text
    - `search_mode` (string, optional): Search strategy to use ("regex", "semantic", "exact", or "hybrid")
    - `spaces` (array of strings, optional): List of spaces to search in
    - `max_results` (integer, optional): Maximum number of results (default: 50)
    - `include_sender_info` (boolean, optional): Whether to include detailed sender information
    - `start_date` (string, optional): Start date in YYYY-MM-DD format
    - `end_date` (string, optional): End date in YYYY-MM-DD format
    - `filter_str` (string, optional): Custom filter string in Google Chat API format
  - Returns: Dictionary with matching message objects and nextPageToken for pagination

- **`mcp_google_chat_get_my_mentions_tool`** - Find messages that mention you
  - Parameters:
    - `days` (integer, optional): Number of days to look back (default: 7)
    - `space_id` (string, optional): Limit search to a specific space
    - `include_sender_info` (boolean, optional): Whether to include detailed sender information (default: True)
    - `page_size` (integer, optional): Maximum number of messages to return (default: 50)
    - `page_token` (string, optional): Token for retrieving the next page of results
  - Returns: Dictionary with messages mentioning you and nextPageToken for pagination

### User Information
- **`mcp_google_chat_get_my_user_info_tool`** - Get your Google Chat user details
  - Parameters: none
  - Returns: User object with details like email, display name

- **`mcp_google_chat_get_user_info_by_id_tool`** - Get information about a specific user by their ID
  - Parameters:
    - `user_id` (string, required): The ID of the user to get information for
  - Returns: User object with details like email, display name, profile photo

- **`mcp_google_chat_get_message_with_sender_info_tool`** - Get a message with enhanced sender details
  - Parameters:
    - `message_name` (string, required): Full resource name of message
  - Returns: Full message object with additional sender_info field containing detailed user profile

- **`mcp_google_chat_list_messages_with_sender_info_tool`** - List messages with enhanced sender information
  - Parameters:
    - `space_name` (string, required): Space identifier
    - `start_date` (string, optional): Date in YYYY-MM-DD format
    - `end_date` (string, optional): Date in YYYY-MM-DD format
    - `limit` (integer, optional): Maximum number of messages (default: 10)
    - `page_token` (string, optional): Token for retrieving the next page of results
  - Returns: Dictionary with messages array and nextPageToken for pagination, with sender_info included

### Space Management
- **`mcp_google_chat_manage_space_members_tool`** - Add or remove members from a space
  - Parameters:
    - `space_name` (string, required): Space identifier
    - `operation` (string, required): Either "add" or "remove"
    - `user_emails` (array of strings, required): Email addresses to add/remove
  - Returns: Response with operation results

## Date Filtering in Message Search

The `search_messages_tool` supports powerful date filtering capabilities to narrow down your search results by message creation time. This is especially useful for finding messages within specific time frames or recent conversations.

### Date Filter Syntax

Date filtering uses the YYYY-MM-DD format (e.g., "2024-05-01") and supports:

1. **Start date only** - Filter messages after a specific date:
   ```json
   {
     "query": "project status",
     "search_mode": "regex",
     "spaces": ["spaces/AAQAXL5fJxI"],
     "start_date": "2024-05-01"
   }
   ```
   This returns all messages created *after* May 1st, 2024.

2. **Date range** - Filter messages between two dates:
   ```json
   {
     "query": "meeting notes",
     "search_mode": "semantic",
     "spaces": ["spaces/AAQAXL5fJxI"],
     "start_date": "2024-05-01",
     "end_date": "2024-05-31"
   }
   ```
   This returns messages created after May 1st and before May 31st, 2024.

### Important Notes on Date Filtering

- The Google Chat API uses `>` (greater than) for start dates and `<` (less than) for end dates, not `>=` or `<=`.
- For semantic searches, date filtering is treated as a preference rather than a strict requirement. If no messages match the date filter, the search will fall back to finding semantically relevant messages even outside the date range.
- For non-semantic searches (regex, exact), date filtering is strictly enforced.
- When searching with future dates, results will remain empty until messages exist for that timeframe.
- For finding messages on a specific day only, use that day as `start_date` and the next day as `end_date`.

### Best Practices

1. **Finding today's messages:**
   ```json
   {
     "query": ".*",
     "search_mode": "regex",
     "start_date": "2024-05-19"
   }
   ```

2. **Finding messages from a specific month:**
   ```json
   {
     "query": "budget",
     "start_date": "2024-05-01",
     "end_date": "2024-05-31"
   }
   ```

3. **Finding all messages since a specific date:**
   ```json
   {
     "query": ".*",
     "search_mode": "regex",
     "start_date": "2024-01-01"
   }
   ```

## Test Structure

The Google Chat MCP tests are organized into modular test modules:

- `src/tools/tests/test_auth_tools.py` - Authentication related tests
- `src/tools/tests/test_message_tools.py` - Message related tests
- `src/tools/tests/test_search_tools.py` - Search related tests
- `src/tools/tests/test_space_tools.py` - Space related tests

### Running Tests

Tests can be run directly using `pytest`:

```bash
# Run all tests
python -m pytest

# Run tests with verbose output
python -m pytest -v

# Run a specific test module
python -m pytest src/tools/tests/test_auth_tools.py

# Run tests with coverage report
python -m pytest --cov=src

# Run tests matching a specific pattern
python -m pytest -k "search"
```

> Note: The legacy `test_google_chat_tools.py` file now redirects to the modular test structure.