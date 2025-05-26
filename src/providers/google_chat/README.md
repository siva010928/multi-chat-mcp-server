# Google Chat MCP Server

## Overview

This project provides a server implementation for the Model Control Protocol (MCP) that integrates with the Google Chat API, allowing AI assistants to interact with Google Chat. Once configured, the MCP client (e.g., Cursor) will manage the server lifecycle automatically when needed.

The Google Chat MCP Server enables AI assistants to perform rich, interactive operations with Google Chat, including sending messages, searching conversations, managing spaces, and accessing user information. It handles all OAuth authentication, token management, and API interactions to provide a seamless experience.

### Key Benefits

- **Seamless Integration**: Works directly with Cursor and other MCP-compatible AI assistants
- **Comprehensive API Coverage**: Supports most Google Chat API operations
- **Enterprise Ready**: Designed for use in Google Workspace environments
- **Advanced Search**: Includes regex, exact, and semantic search capabilities
- **Enhanced User Information**: Provides detailed sender information with messages

### Features

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

## Prerequisites

Before starting, ensure you have:

- **Google Workspace Account**: This tool only works with Google Workspace accounts (formerly G Suite) in an organization. Personal Google accounts cannot access the Google Chat API.
- **Google Cloud Platform Project**: You must be able to create and configure a project in Google Cloud Console.
- **Python 3.9+**: The server requires Python 3.9 or newer.
- **uv**: Recommended package manager for MCP client integration
   ```bash
   pip install uv
   ```
   
   Using `uv` offers several advantages for MCP client integration:
   - Faster dependency resolution and installation (up to 10-100x faster than using just python to run the server)
   - Better caching of packages
   - Improved reproducibility with lockfiles
   - Enhanced compatibility with MCP clients
   - Better handling of complex dependency graphs
   - Improved environment isolation to prevent conflicts
   
- **OAuth Credentials**: From Google Chat API
- **OAuth 2.0 Understanding**: Basic familiarity with OAuth authentication flows is helpful.

## Installation

### 1. Clone and Setup

1. Clone this repository:

   ```bash
   git clone https://github.com/siva010928/multi-chat-mcp-server.git
   cd multi-chat-mcp-server
   ```

2. After following Prerequisites, create a virtual environment and install requirements:

   ```bash
   # Create and activate virtual environment
   python -m venv .venv

   # On Linux/macOS:
   source .venv/bin/activate
   # On Windows (Command Prompt):
   .\.venv\Scripts\activate.bat
   # On Windows (PowerShell):
   .\.venv\Scripts\Activate.ps1

   # Install dependencies
   pip install -r requirements.txt
   ```

### 2. Project Structure

Understanding the project structure will help with configuration:

```
multi-chat-mcp-server/
├── diagrams/                # SVG diagrams and source files
├── docs/                    # Documentation files
├── src/
│   ├── mcp_core/           # Core MCP functionality
│   │   ├── engine/         # Core engine components
│   │   └── tools/          # Core tools
│   ├── providers/
│   │   └── google_chat/     # Google Chat provider implementation
│   │       ├── api/         # API client implementations
│   │       ├── tools/       # MCP tool implementations
│   │       ├── utils/       # Utility functions and helpers
│   │       │   └── search_config.yaml # Search configuration
│   │       ├── credentials.json # OAuth client configuration (place here)
│   │       └── token.json   # Default OAuth token storage location
│   ├── __init__.py
│   ├── mcp_instance.py      # MCP instance configuration
│   └── server.py            # Main server implementation
├── provider-config.yaml     # Provider configuration file
```

## Configuration

### 1. Google Cloud Platform Setup

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

### 2. OAuth Credentials Setup

1. **Set up OAuth credentials**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Select "Web application" as the application type (not Desktop app)
   - Give it a name (e.g., "Google Chat MCP Client")
   - Under "Authorized JavaScript origins" add: `http://localhost:8000`
   - Under "Authorized redirect URIs" add: `http://localhost:8000/auth/callback`
   - Click "Create" and download the JSON file
   - **Important**: Rename the downloaded file to `credentials.json` and place it at the path specified in `provider-config.yaml` (default: `src/providers/google_chat/credentials.json`)
   - This credentials.json file contains the client configuration that Google uses to verify your application's identity during the OAuth flow. Without it, authentication will fail.
   - Reference: [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)

### 3. Provider Configuration

The file paths for credentials, token, and configuration files are defined in `provider-config.yaml`:

```yaml
# File: provider-config.yaml

providers:
  google_chat:
    token_path: src/providers/google_chat/token.json
    credentials_path: src/providers/google_chat/credentials.json
    search_config_path: src/providers/google_chat/utils/search_config.yaml
    # Other configuration...
```

> **Note**: The token path is specified in `provider-config.yaml` as a relative path from the project root. The server automatically converts it to an absolute path when needed.

## Authentication

### Initial Authentication Setup

1. **Authenticate with Google**:
   - The token path is already configured in `provider-config.yaml`:
     ```yaml
     providers:
       google_chat:
         token_path: src/providers/google_chat/token.json
         # other configuration...
     ```
   - Run the authentication server:
     ```bash
     python -m src.server --provider google_chat --local-auth
     ```
   - Visit http://localhost:8000/auth in your browser
   - Follow the OAuth flow to grant permissions
   - After successful authentication, a `token.json` file will be generated at the path specified in `provider-config.yaml`
   - This token will be used for all future API requests, and the MCP server will automatically refresh it when needed

> **Note**: The token path is specified in `provider-config.yaml` as a relative path from the project root. The server automatically converts it to an absolute path when needed.

## MCP Client Integration

### Configure Your MCP Client

Add the Google Chat MCP server to your MCP client's configuration. For Cursor, edit your `~/.cursor/mcp.json` file:

```json
{
  "mcpServers": {
    "google_chat": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/multi-chat-mcp-server",
        "run",
        "-m", 
        "src.server",
        "--provider",
        "google_chat"
      ]
    }
  }
}
```

Replace `/path/to/multi-chat-mcp-server` with the absolute path to your repository.

> **IMPORTANT**: 
> - For MCP client integration with Cursor, use `uv` as shown above
> - For local development and testing, use Python directly as shown in the earlier installation steps
> - The paths in `provider-config.yaml` should be relative to the project root. The server automatically converts them to absolute paths when needed.

> **Note**: After completing this setup, you can close this project. The MCP client (e.g., Cursor) will automatically start and manage the server process when you use trigger Google Chat MCP tools by requesting your AI assistant via convo.

## Using Google Chat MCP Tools

After setting up the server and configuring your MCP client, you can start using the Google Chat MCP tools with AI assistants like Claude in Cursor. The tools allow you to interact with Google Chat directly from your AI assistant conversation.

### Conversational Interaction Examples

You can use natural language to instruct your AI assistant to perform actions in Google Chat:

- **Team Communication**:
  - "Update my team about the project status"
  - "Send a message to our team space about the upcoming release"
  - "Reply to the latest thread in our project space"

- **Information Retrieval**:
  - "Catch me up with my team space"
  - "Find messages about deployment issues from last week"
  - "Check if anyone has mentioned me recently"
  - "Summarize today's conversation in the engineering space"

- **Collaboration**:
  - "Share this code snippet with my team"
  - "Send this error log to the support space and ask for help"
  - "Get the latest requirements document that was shared in our team chat"
  
This conversational interaction is the most effective way to use the Google Chat integration, as it simulates natural human communication patterns while leveraging the power of AI to process and manage your chat interactions.

## Available Tools Reference

The following tools are available to interact with Google Chat:

### Chat Space Management
- **`get_chat_spaces_tool`** - List all Google Chat spaces you have access to
  - Implementation: [`src/providers/google_chat/tools/space_tools.py`](../../../src/providers/google_chat/tools/space_tools.py)
  - Parameters: 
    - `random_string` (string, required): Dummy parameter for no-parameter tools
  - Returns: Array of space objects with details like name, type, display name

- **`get_space_messages_tool`** - List messages from a specific space with date filtering
  - Implementation: [`src/providers/google_chat/tools/message_tools.py`](../../../src/providers/google_chat/tools/message_tools.py)
  - Parameters: 
    - `space_name` (string, required): Space identifier (e.g., "spaces/AAQAtjsc9v4")
    - `days_window` (integer, optional): Number of days to look back (default: 3)
    - `offset` (integer, optional): Number of days to offset from today (default: 0)
    - `include_sender_info` (boolean, optional): Whether to include detailed sender information
    - `page_size` (integer, optional): Maximum number of messages to return (default: 25, max: 1000)
    - `page_token` (string, optional): Token for retrieving the next page of results
    - `filter_str` (string, optional): Custom filter string in Google Chat API format
    - `order_by` (string, optional): Ordering format like "createTime DESC"
    - `show_deleted` (boolean, optional): Whether to include deleted messages
  - Returns: Dictionary containing an array of message objects and a nextPageToken for pagination

### Messaging
- **`send_message_tool`** - Send a text message to a Google Chat space
  - Implementation: [`src/providers/google_chat/tools/message_tools.py`](../../../src/providers/google_chat/tools/message_tools.py)
  - Parameters: 
    - `space_name` (string, required): Space identifier
    - `text` (string, required): Message content
  - Returns: Created message object

- **`reply_to_message_thread_tool`** - Reply to an existing thread in a space
  - Implementation: [`src/providers/google_chat/tools/message_tools.py`](../../../src/providers/google_chat/tools/message_tools.py)
  - Parameters:
    - `space_name` (string, required): Space identifier
    - `thread_key` (string, required): Thread identifier
    - `text` (string, required): Reply content
    - `file_path` (string, optional): Path to a file to attach
  - Returns: Created message object

- **`update_chat_message_tool`** - Update an existing message
  - Implementation: [`src/providers/google_chat/tools/message_tools.py`](../../../src/providers/google_chat/tools/message_tools.py)
  - Parameters:
    - `message_name` (string, required): Full resource name of message
    - `new_text` (string, required): Updated text content
  - Returns: Updated message object

- **`delete_chat_message_tool`** - Delete a message
  - Implementation: [`src/providers/google_chat/tools/message_tools.py`](../../../src/providers/google_chat/tools/message_tools.py)
  - Parameters:
    - `message_name` (string, required): Full resource name of message
  - Returns: Empty response on success

### Message Interactions
- **`add_emoji_reaction_tool`** - Add an emoji reaction to a message
  - Implementation: [`src/providers/google_chat/tools/message_tools.py`](../../../src/providers/google_chat/tools/message_tools.py)
  - Parameters:
    - `message_name` (string, required): Message identifier
    - `emoji` (string, required): Unicode emoji character
  - Returns: Created reaction object

- **`get_chat_message_tool`** - Get details about a specific message
  - Implementation: [`src/providers/google_chat/tools/message_tools.py`](../../../src/providers/google_chat/tools/message_tools.py)
  - Parameters:
    - `message_name` (string, required): Message identifier
    - `include_sender_info` (boolean, optional): Whether to include detailed sender information
  - Returns: Full message object

### Search & Filtering
- **`search_messages_tool`** - Search for messages across spaces
  - Implementation: [`src/providers/google_chat/tools/search_tools.py`](../../../src/providers/google_chat/tools/search_tools.py)
  - Parameters:
    - `query` (string, required): Search text
    - `search_mode` (string, optional): Search strategy to use ("regex", "semantic", "exact", or "hybrid")
    - `spaces` (array of strings, optional): List of spaces to search in
    - `max_results` (integer, optional): Maximum number of results (default: 50)
    - `include_sender_info` (boolean, optional): Whether to include detailed sender information
    - `days_window` (integer, optional): Number of days to look back (default: 3)
    - `offset` (integer, optional): Number of days to offset from today (default: 0)
    - `filter_str` (string, optional): Custom filter string in Google Chat API format
  - Returns: Dictionary with matching message objects and nextPageToken for pagination

- **`get_my_mentions_tool`** - Find messages that mention you
  - Implementation: [`src/providers/google_chat/tools/search_tools.py`](../../../src/providers/google_chat/tools/search_tools.py)
  - Parameters:
    - `days` (integer, optional): Number of days to look back (default: 7)
    - `spaces` (array of strings, optional): Limit search to specific spaces
    - `include_sender_info` (boolean, optional): Whether to include detailed sender information (default: True)
    - `page_size` (integer, optional): Maximum number of messages to return (default: 50)
    - `page_token` (string, optional): Token for retrieving the next page of results
    - `offset` (integer, optional): Number of days to offset from today (default: 0)
  - Returns: Dictionary with messages mentioning you and nextPageToken for pagination

### User Information
- **`get_my_user_info_tool`** - Get your Google Chat user details
  - Implementation: [`src/providers/google_chat/tools/user_tools.py`](../../../src/providers/google_chat/tools/user_tools.py)
  - Parameters: 
    - `random_string` (string, required): Dummy parameter for no-parameter tools
  - Returns: User object with details like email, display name

- **`get_user_info_by_id_tool`** - Get information about a specific user by their ID
  - Implementation: [`src/providers/google_chat/tools/user_tools.py`](../../../src/providers/google_chat/tools/user_tools.py)
  - Parameters:
    - `user_id` (string, required): The ID of the user to get information for
  - Returns: User object with details like email, display name, profile photo

- **`get_message_with_sender_info_tool`** - Get a message with enhanced sender details
  - Implementation: [`src/providers/google_chat/tools/message_tools.py`](../../../src/providers/google_chat/tools/message_tools.py)
  - Parameters:
    - `message_name` (string, required): Full resource name of message
  - Returns: Full message object with additional sender_info field containing detailed user profile

- **`list_messages_with_sender_info_tool`** - List messages with enhanced sender information
  - Implementation: [`src/providers/google_chat/tools/message_tools.py`](../../../src/providers/google_chat/tools/message_tools.py)
  - Parameters:
    - `space_name` (string, required): Space identifier
    - `days_window` (integer, optional): Number of days to look back (default: 3)
    - `offset` (integer, optional): Number of days to offset from today (default: 0)
    - `limit` (integer, optional): Maximum number of messages (default: 10)
    - `page_token` (string, optional): Token for retrieving the next page of results
  - Returns: Dictionary with messages array and nextPageToken for pagination, with sender_info included

### Space Management
- **`manage_space_members_tool`** - Add or remove members from a space
  - Implementation: [`src/providers/google_chat/tools/space_tools.py`](../../../src/providers/google_chat/tools/space_tools.py)
  - Parameters:
    - `space_name` (string, required): Space identifier
    - `operation` (string, required): Either "add" or "remove"
    - `user_emails` (array of strings, required): Email addresses to add/remove
  - Returns: Response with operation results

- **`get_conversation_participants_tool`** - Get information about participants in a conversation
  - Implementation: [`src/providers/google_chat/tools/space_tools.py`](../../../src/providers/google_chat/tools/space_tools.py)
  - Parameters:
    - `space_name` (string, required): Space identifier
    - `max_messages` (integer, optional): Maximum messages to analyze (default: 100)  
    - `days_window` (integer, optional): Number of days to look back (default: 3)
    - `offset` (integer, optional): Number of days to offset from today (default: 0)
  - Returns: List of user objects with participant details

- **`summarize_conversation_tool`** - Generate a summary of a conversation
  - Implementation: [`src/providers/google_chat/tools/space_tools.py`](../../../src/providers/google_chat/tools/space_tools.py)
  - Parameters:
    - `space_name` (string, required): Space identifier
    - `message_limit` (integer, optional): Maximum messages to include (default: 10)
    - `days_window` (integer, optional): Number of days to look back (default: 3)
    - `offset` (integer, optional): Number of days to offset from today (default: 0)
    - `page_token` (string, optional): Token for retrieving the next page of results
    - `filter_str` (string, optional): Custom filter string in Google Chat API format
  - Returns: Dictionary with space details, participants, and messages

### File Handling
- **`upload_attachment_tool`** - Upload a file as an attachment to a message
  - Implementation: [`src/providers/google_chat/tools/message_tools.py`](../../../src/providers/google_chat/tools/message_tools.py)
  - Parameters:
    - `space_name` (string, required): Space identifier
    - `file_path` (string, required): Path to the file to upload
    - `message_text` (string, optional): Additional text to include with the attachment
    - `thread_key` (string, optional): Thread to reply to
  - Returns: Created message object with attachment

- **`send_file_message_tool`** - Send file contents as a message
  - Implementation: [`src/providers/google_chat/tools/message_tools.py`](../../../src/providers/google_chat/tools/message_tools.py)
  - Parameters:
    - `space_name` (string, required): Space identifier
    - `file_path` (string, required): Path to the file whose contents to send
    - `message_text` (string, optional): Additional text to include with the file content
    - `thread_key` (string, optional): Thread to reply to
  - Returns: Created message object

- **`send_file_content_tool`** - Send file content as a formatted message
  - Implementation: [`src/providers/google_chat/tools/message_tools.py`](../../../src/providers/google_chat/tools/message_tools.py)
  - Parameters:
    - `space_name` (string, required): Space identifier
    - `file_path` (string, optional): Path to the file to send (defaults to sample file if not provided)
    - `thread_key` (string, optional): Thread to reply to
  - Returns: Created message object

### Batch Operations
- **`batch_send_messages_tool`** - Send multiple messages in one operation
  - Implementation: [`src/providers/google_chat/tools/message_tools.py`](../../../src/providers/google_chat/tools/message_tools.py)
  - Parameters:
    - `messages` (array, required): List of message objects to send, each containing:
      - `space_name` (string, required): Space identifier
      - `text` (string, required): Message content
      - `thread_key` (string, optional): Thread to reply to
      - `cards_v2` (object, optional): Card content
  - Returns: Dictionary with results for each message

## Testing

### Running Tests

The project includes a comprehensive test suite. To run the tests:

```bash
# Activate your virtual environment if not already active
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run all tests with coverage report
python -m pytest

# Run tests with detailed coverage information
python -m pytest src/providers/google_chat/tools/tests/ --cov=src.tools --cov-report=term-missing -v
```

### Test Structure

The test structure is organized as follows:

```
src/
  providers/
    google_chat/
      api/tests/       - Tests for API client functionality
      tools/tests/     - Tests for MCP tools
      utils/tests/     - Tests for utility functions
```

Tests can be run directly using `pytest`:

```bash
# Run all tests
python -m pytest

# Run tests with verbose output
python -m pytest -v

# Run a specific test module
python -m pytest src/providers/google_chat/api/tests/test_auth.py

# Run tests with coverage report
python -m pytest --cov=src

# Run tests with detailed coverage information
python -m pytest src/providers/google_chat/tools/tests/ --cov=src.tools --cov-report=term-missing -v
```

## Advanced Integration

### Cursor Integration

For detailed instructions on integrating this MCP server with Cursor, including custom rules for team communication and message handling, see [CURSOR_INTEGRATION.md](CURSOR_INTEGRATION.md).

## 🧩 Google Chat MCP Server – Real-world Usage Showcase

These walkthroughs show how an AI assistant, powered by this MCP server, evolves from a passive tool into an active collaborator — debugging issues, coordinating teams, syncing scripts, and proactively unblocking developers.

---

### 🛠️ Tool Setup & Initialization

<div align="center">
  <img src="../../../google_chat_mcp_client_demo_images/how_google_chat_mcp_tools_registered_with_mcp_client.png" width="80%" alt="Scene 1: Tool Registration with Google Chat"/>
  <p><i><strong>Scene 1: Tool Registration with Google Chat</strong></i></p>
</div>

**The Scenario:** Connecting MCP client to Google Chat.

**What's Happening:** The AI assistant is granted access to all Google Chat tools (e.g., send, search, summarize, attach, reply).

**Why it Matters:** The assistant can now *act* inside Google Chat, not just observe.

---

### 🧯 Debugging & Resolution (Docker Example)

<div align="center">
  <img src="../../../google_chat_mcp_client_demo_images/how_i_asked_mcp_client_to_share_my_error_along_with_logs_to_get_help_from_my_team.png" width="80%" alt="Scene 8: Broadcasting an Error to the Team"/>
  <p><i><strong>Scene 2: Broadcasting an Error to the Team</strong></i></p>
</div>

**What's Happening:** A developer asks the AI to share Docker error logs in chat, prompting real-time team help.

<div align="center">
  <img src="../../../google_chat_mcp_client_demo_images/proof_that_team_member_replied_with_instructions_to_fix_the_errors_i_shared.png" width="80%" alt="Scene 3: Receiving a Fix from a Teammate"/>
  <p><i><strong>Scene 3: Team Responds with a Fix</strong></i></p>
</div>

**Next Step:** A teammate replies with a Dockerfile fix (`COPY requirements.txt .`).

<div align="center">
  <img src="../../../google_chat_mcp_client_demo_images/how_i_asked_mcp_client_to_check_with_response_of_my_error_issues_which_i_shared_recently_and_how_i_asked_to_follow_instructions_of_the_response_from_my_team_to_fix_the_issue.png" width="80%" alt="Scene 4: Agent Applies Suggested Fix"/>
  <p><i><strong>Scene 4: Agent Applies the Fix</strong></i></p>
</div>

**Automation Moment:** The AI assistant edits the Dockerfile per the advice — no manual effort.

<div align="center">
  <img src="../../../google_chat_mcp_client_demo_images/how_mcp_client_properly_followed_my_team_member_instructions_for_the_concern_i_shared.png" width="80%" alt="Scene 5: Verifying the Fix"/>
  <p><i><strong>Scene 5: Verifying the Fix</strong></i></p>
</div>

**Wrap-up:** It verifies the change, confirms `requirements.txt` exists — and the error should be resolved.

---

### 📦 Dependency & Script Sync

<div align="center">
  <img src="../../../google_chat_mcp_client_demo_images/proof_that_mcp_client_again_3rd_time_properly_assisted_the_concern_i_asked_to_then_it_properly_provided_my_local_latest_requirements_file_to_someone_who_facing_the_issues_with_requirements.png" width="80%" alt="Scene 6: Sharing requirements.txt"/>
  <p><i><strong>Scene 6: Sharing `requirements.txt`</strong></i></p>
</div>

**Scenario:** I have requested my team requests to share a working `requirements.txt`.

**Response:** One of my teammate shared their working `requirements.txt`.

<div align="center">
  <img src="../../../google_chat_mcp_client_demo_images/how_i_asked_mcp_client_to_pull_the_lastest_requirements_and_modifying_with_the_local_one_that_i_asked_for_in_team_space_after_someone_shared_the_requirements_file.png" width="80%" alt="Scene 7: Syncing requirements.txt"/>
  <p><i><strong>Scene 7: Syncing Local Copy</strong></i></p>
</div>

**Developer POV:** The AI reviewed the thread and based on my instruction, it updated my local `requirements.txt` with the one that was shared

---

<div align="center">
  <img src="../../../google_chat_mcp_client_demo_images/how_i_asked_my_team_to_share_aws-setup.sh_scrip_in_google_chat_space.png" width="80%" alt="Scene 8: Requesting AWS Setup Script"/>
  <p><i><strong>Scene 8: Requesting AWS Setup Script</strong></i></p>
</div>

**Scenario:** You ask your team for a shared `aws-setup.sh` script.

<div align="center">
  <img src="../../../google_chat_mcp_client_demo_images/how_mcp_client_get_aws-script-from-team-space-and-compare-it-with-local-one-after-team-member-replied-to-my-previous-requesting-aws-setup-script.png" width="80%" alt="Scene 9: Script Consistency Check"/>
  <p><i><strong>Scene 9: Script Consistency Check</strong></i></p>
</div>

**Developer POV:** The AI reviewed the thread and based on my instruction, it compares the team’s script with your local version — ensuring you're in sync.

---

### 👀 Team Coordination & Catch-Up

<div align="center">
  <img src="../../../google_chat_mcp_client_demo_images/how_i_asked_to_summarize_my_team_space_today_about_what_is_hapening_like_a_quick_updates.png" width="80%" alt="Scene 10: Summarizing Team Activity"/>
  <p><i><strong>Scene 10: Summarizing Team Activity</strong></i></p>
</div>

**Context:** You’ve been away. What’s new?

**AI Response:** The assistant summarizes key activity in your space: questions, PRs, shared files, blockers.

<div align="center">
  <img src="../../../google_chat_mcp_client_demo_images/how_mcp_client(cursor)_get_my_mentions_from_team_chat_space.png" width="80%" alt="Scene 11: Catching Up on Mentions"/>
  <p><i><strong>Scene 11: Catching Up on Mentions</strong></i></p>
</div>

**Missed a ping?** The AI scans for all mentions and surfaces conversations you were tagged in.

---

### 🔍 AI-Powered Problem Solving from Team Chat Context

<div align="center">
  <img src="../../../google_chat_mcp_client_demo_images/how_mcp_client_again_search_for_any_concerns_in_our_chat_space_related_to_our_project_specifcally_to_assist_them_and_well_it_understand_the_concerns_and_assist_them.png" width="80%" alt="Scene 12: AI Scanning Team Chat for Problems"/>
  <p><i><strong>Scene 12: AI Scanning Team Chat for Problems</strong></i></p>
</div>

**The Scenario:** A developer explicitly asks the AI assistant to help resolve open concerns mentioned by the team in the chat space.

**What's Happening:** The AI scans recent chat messages, identifies technical questions, missing files, and potential blockers related to the project, and prepares to assist.

**Developer Perspective:** The agent isn't just reactive — it understands team context and can search for unresolved issues when prompted.

<div align="center">
  <img src="../../../google_chat_mcp_client_demo_images/proof_that_mcp_client_properly_assisted_the_concern_i_asked_to.png" width="80%" alt="Scene 13: AI Finds the Missing File Path"/>
  <p><i><strong>Scene 13: AI Finds the Missing File Path</strong></i></p>
</div>

**Example Use Case:** A teammate mentioned they couldn’t find `ReviewForm.js`.

**AI Response:** The agent searches the local repo, finds the correct path, and replies directly in the chat thread.

**Why it Matters:** Instead of waiting for someone to respond, the AI assistant unblocks teammates in real-time with accurate, repo-aware answers — making onboarding and collaboration faster and smoother.