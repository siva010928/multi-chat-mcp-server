## Project Overview

This project provides a server implementation for the Model Control Protocol (MCP) that integrates with the Google Chat API, allowing AI assistants to interact with Google Chat. Once configured, the MCP client (e.g., Cursor) will manage the server lifecycle automatically when needed.

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

### File Handling
- **`mcp_google_chat_send_file_message_tool`** - Send a message with file contents
  - Parameters:
    - `space_name` (string, required): Space identifier
    - `file_path` (string, required): Path to the file
    - `message_text` (string, optional): Accompanying message
  - Returns: Created message object

- **`mcp_google_chat_send_file_content_tool`** - Send file content as a message (workaround for attachments)
  - Parameters:
    - `space_name` (string, required): Space identifier
    - `file_path` (string, optional): Path to the file to send
  - Returns: Created message object

- **`mcp_google_chat_upload_attachment_tool`** - Upload a file attachment to a Google Chat space
  - Parameters:
    - `space_name` (string, required): Space identifier
    - `file_path` (string, required): Path to the file to upload
    - `message_text` (string, optional): Text message to accompany the attachment
  - Returns: The created message object with the attachment

### Batch Operations
- **`mcp_google_chat_batch_send_messages_tool`** - Send multiple messages in one operation
  - Parameters:
    - `messages` (array of objects, required): List of message objects to send
  - Returns: Results for each message

### Conversation Analysis
- **`mcp_google_chat_get_conversation_participants_tool`** - Get information about conversation participants
  - Parameters:
    - `space_name` (string, required): Space identifier
    - `start_date` (string, optional): Date in YYYY-MM-DD format
    - `end_date` (string, optional): Date in YYYY-MM-DD format
    - `max_messages` (integer, optional): Maximum number of messages to analyze (default: 100)
  - Returns: Array of participant information objects

- **`mcp_google_chat_summarize_conversation_tool`** - Generate a summary of a conversation
  - Parameters:
    - `space_name` (string, required): Space identifier
    - `message_limit` (integer, optional): Maximum messages to include (default: 10)
    - `start_date` (string, optional): Date in YYYY-MM-DD format
    - `end_date` (string, optional): Date in YYYY-MM-DD format
    - `page_token` (string, optional): Token for retrieving the next page of results
    - `filter_str` (string, optional): Custom filter string in Google Chat API format
  - Returns: Dictionary with space details, participant list, and recent messages

## Configuration Customization

### Constants Configuration

You can customize various aspects of the Google Chat MCP server by modifying constants in `src/google_chat/constants.py`:

- `DEFAULT_TOKEN_PATH`: Path where the OAuth token is stored
- `CREDENTIALS_FILE`: Path to the OAuth credentials file
- `SCOPES`: OAuth scopes required for the application
- `DEFAULT_CALLBACK_URL`: Callback URL for the OAuth flow
- `SEARCH_CONFIG_YAML_PATH`: Path to the search configuration file

### Search Configuration

The `search_config.yaml` file in the root directory controls how the search functionality works:

```yaml
search_modes:
  - name: "regex"  # Default search mode
    enabled: true
    description: "Regular expression pattern matching - case insensitive by default."
    weight: 1.2
    options:
      ignore_case: true
      dot_all: false
      unicode: true
      max_pattern_length: 1000
    
  - name: "exact"
    enabled: true
    description: "Basic case-insensitive substring matching - fastest but least flexible."
    weight: 1.0
    
  - name: "semantic"
    enabled: true
    description: "Meaning-based semantic search - best for concept searching."
    weight: 1.5
    options:
      model: "all-MiniLM-L6-v2"
      cache_embeddings: true
      cache_max_size: 10000
      similarity_threshold: 0.2
      similarity_metric: "cosine"

search:
  default_mode: "regex"  # The search mode to use by default
  max_results_per_space: 50
  combine_results_strategy: "weighted_score"
```

You can modify this file to:
- Change the default search mode (regex, semantic, exact, hybrid)
- Adjust weights for different search modes
- Configure semantic search parameters like model and threshold
- Set maximum results returned per search

The LLM will use the default search mode unless explicitly specifying a different mode in the `search_mode` parameter.

### Agent Rules for Tool Execution

When using these tools with an AI assistant, you can define custom rules to guide how the tools are used. For example, in Cursor, you can set up specific rules for when and how the Google Chat tools should be executed:

**Example Rule for Team Communication:**
```
If I say anything that semantically implies communicating with my team—including phrases like:
"Update my team," "Send this to the team," "Let the team know," etc.

Then interpret this as a command to send a message via the send_message tool with:
space_name: spaces/YOUR_SPACE_ID
text: [content from my message]

For search operations, start with semantic mode, then fall back to regex if needed.
Show me message drafts for approval when the intent or content is unclear.
```

**Comprehensive Team Communication Rule Example:**
```
If I say anything that even remotely, semantically or syntactically, implies communicating with my team—including, but not limited to, any of these phrases or their variants:

"Catch me up with [topic/updates/etc.]" (this always triggers a search; start with semantic mode, then regex if semantic yields nothing),
"Update my team," "Send this to the team," "Let the team know,"
"Share with my team," "Message the team," "Convey this to them,"
"Team should know this," "Pass this along to the team,"
"Notify the team," "Inform them," "Tell everyone,"
"Broadcast this," "Share this update with everyone,"
"Remind them about [something]," "Let the group know,"
"Team needs to hear this," "Push this to the group chat,"
"Make sure the team is aware," "Send an alert to the team,"
"Relay this to the team," "Tell the group," "Forward this to the team,"

and any other phrasing with similar intent—you must interpret this as a command to send a message via the send_message tool in the Google Chat MCP agent.

You must always use the following parameters:
space_name: spaces/AAQAXL5fJxI
text: [the content you construct or extract from my message]

Never use any other communication channel (do not use email, Slack, SMS, etc.).
Never switch to another Google Chat space unless I specify it explicitly by name or space ID.
Never skip this action—ever—when a trigger phrase or its equivalent meaning is present.

If you are at all unsure what to send due to missing context, unclear phrasing, or abstraction:
1. Draft a sample message.
2. Show it to me: "Here's what I'll send to the team. Approve?"
3. Wait for my explicit confirmation before sending.

When you are told to "catch me up with" or anything suggesting a search, always start with "semantic" mode to search for relevant messages or updates. If you do not get any results, immediately retry using "regex" mode.
```

You can customize rules like this to:
- Specify which spaces to use by default
- Define trigger phrases for different tools
- Establish search preferences (e.g., try semantic first, then regex)
- Require approval before sending messages
- Set up conversation context handling

These rules help the AI assistant choose appropriate tools and parameters automatically based on your instructions, making interactions more natural without requiring explicit tool commands.

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
5. You're using a different device or location that triggers Google's security checks

> **Token Management Tools**: For manual token management and troubleshooting, the repository includes two utility scripts:
> - `refresh_token.py`: Manually refresh an expired access token
> - `check_token.py`: Validate and examine the current token status

## Pagination Support

Many Google Chat API functions now support pagination for handling large result sets:

### How Pagination Works

- Functions that can return many results accept a `page_size` parameter and return a `nextPageToken` in their response
- The maximum number of results per page varies by endpoint but is typically limited to 1000 items
- When a `nextPageToken` is present in the response, there are more results available

### Using Pagination

1. Make an initial request with desired `page_size` (e.g., 25, 50, 100)
2. Check if the response contains a `nextPageToken` 
3. To get the next page of results, make another request with the same parameters plus the `page_token` parameter set to the `nextPageToken` value from the previous response
4. Repeat until the response no longer includes a `nextPageToken` or returns an empty one

### Example Response Structure

```json
{
  "messages": [
    { /* message 1 */ },
    { /* message 2 */ },
    // ... more messages
  ],
  "nextPageToken": "Eg0KBW1ldGFkGgYKBAgEEAMaKQoJbWFpbF90aW1lGh..."
}
```

### Endpoints Supporting Pagination

The following functions support pagination:
- `get_space_messages`
- `search_messages`
- `get_my_mentions`
- `list_messages_with_sender_info`
- `summarize_conversation`

## Testing

The repository includes a comprehensive test suite to verify functionality:

### Running Tests

Run the full test suite:

```bash
python test_google_chat_tools.py
```

Or use pytest with coverage:

```bash
python -m pytest
```

View the HTML coverage report in the `htmlcov` directory.

### Test Features

The test suite verifies all major functionalities:

1. **Authentication** - Tests that OAuth credentials are valid and properly configured
2. **Space Operations** - Lists spaces and tests space member management
3. **Message Operations** - Tests sending, updating, replying to, and deleting messages
4. **Search Functionality** - Tests the search capabilities including regex and semantic search
5. **User Information** - Verifies user profile data retrieval
6. **Advanced Features** - Tests conversation summaries and participant analysis

### Testing Configuration

For better test organization, create a file called `test_config.py` with your test space ID:

```python
# test_config.py
TEST_SPACE_ID = "spaces/YOUR_TEST_SPACE_ID"
```

This file is git-ignored and allows you to run tests without hardcoding space IDs.

### CI/CD Integration

The repository includes CircleCI configuration for automated testing. To use it:

1. Configure CircleCI with your repository
2. Set up the following environment variables in CircleCI:
   - `GOOGLE_CREDENTIALS` - Base64-encoded credentials.json content
   - `GOOGLE_TOKEN` - Base64-encoded token.json content
   - `TEST_SPACE_ID` - Your test space ID for running integration tests

### Project Structure

- **google_chat.py**: Core library with all API functions
- **server.py**: MCP server and authentication web server
- **server_auth.py**: Authentication helpers
- **test_google_chat_tools.py**: Test suite for all functionality
- **TOKEN_MANAGEMENT.md**: Detailed guide to token management

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

