# Multi-Provider MCP Server (Google Chat & Beyond)

<div align="center">
  <h3>A modular, extensible framework for AI assistants to interact with chat platforms, with comprehensive Google Chat MCP support</h3>
</div>

## 🌟 Overview

**Multi-Provider MCP Server** is an open-source tool designed to connect AI assistants with various chat platforms through the Model Control Protocol (MCP) interface. This project aims to help developers working in organizations that use Google Chat, Microsoft Teams, Slack, and other communication platforms to seamlessly integrate their chat spaces with AI assistants.

While other MCP implementations may exist, they often provide only basic functionality that limits real-world applications. This project offers **production-ready Google Chat MCP implementation** with extensive features that address practical, everyday developer needs, as demonstrated in our [example use cases](#real-world-use-cases).

As a developer-first project, Multi-Provider MCP Server enables engineering teams to build their own integrations rather than waiting for official implementations, especially for platforms like Microsoft Teams that don't yet have MCP servers available.

### Supported Providers

- ✅ **Google Chat** - Complete implementation with comprehensive API support
- 🔄 **Slack** - Planned
- 📝 **Microsoft Teams** - Planned (will use Microsoft Graph API)

### Key Benefits

- **Provider Agnostic**: One unified interface for multiple chat platforms
- **Production-Ready Google Chat Integration**: Fully featured Google Chat MCP tools
- **Modular Architecture**: Easy extension to new providers
- **Pre-built Tools**: Rich set of interface tools for each provider
- **Authentication Management**: Built-in OAuth support and token management
- **Dynamic Loading**: Load only the components needed for each provider

## 📸 Real-World Use Cases

The [google_chat_mcp_client_demo_images](./google_chat_mcp_client_demo_images/) directory contains examples of how this tool enables practical workflows for developers:

- **Team Collaboration**: Share errors with logs and get assistance from teammates
- **Code Sharing**: Request and receive scripts directly in chat (e.g., aws-setup.sh)
- **Requirements Management**: Pull and modify requirements files shared in team spaces
- **Issue Resolution**: Follow team instructions to fix errors shared in chat
- **Daily Updates**: Generate summaries of team activities
- **Context-Aware Assistance**: Search for and assist with project-specific concerns
- **Resource Comparison**: Compare shared scripts with local versions
- **Mention Tracking**: Gather and respond to team mentions

These use cases demonstrate how the MCP integration goes beyond simple message sending to become a powerful developer productivity tool that enhances team communication and problem solving.

## 📁 Project Structure

```
multi-chat-mcp-server/
├── docs/                      # Documentation files
├── src/
│   ├── mcp_core/              # Core MCP functionality
│   │   ├── engine/            # Provider loading mechanism
│   │   │   └── provider_loader.py
│   │   └── tools/             # Core tool registration
│   │       ├── registry.py    # Central tool registry
│   │       └── tool_decorator.py
│   ├── providers/             # Provider-specific implementations
│   │   ├── google_chat/       # Google Chat provider
│   │   │   ├── api/           # API client implementations
│   │   │   ├── tools/         # MCP tool implementations
│   │   │   ├── utils/         # Utility functions & search config
│   │   │   ├── mcp_instance.py
│   │   │   └── server_auth.py
│   │   └── slack/             # Slack provider structure (for future)
│   ├── __init__.py
│   └── server.py              # Main server entry point
├── provider-config.yaml       # Provider configuration
├── requirements.txt           # Project dependencies
└── README.md                  # This file
```

## 🚀 Getting Started

### Prerequisites

- **Python 3.9+**: The server requires Python 3.9 or newer
- **UV Package Manager**: We recommend using UV for dependency management
- **Provider-specific requirements**: Each provider requires specific OAuth scopes and permissions (detailed below)

### Server Configuration

- **Default Host/Port**: The server runs on `localhost:8000` by default
- **Override Options**: Use `--host` and `--port` arguments to change these settings
- **Example**: `python -m src.server --provider google_chat --host 0.0.0.0 --port 8080`

### Quick Setup Steps

1. **Clone this repository**:

```bash
git clone https://github.com/siva010928/multi-chat-mcp-server.git
cd multi-chat-mcp-server
```

2. **Install dependencies**:

```bash
# Using UV (recommended)
uv venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt

# Or using traditional pip
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configure your provider**:
   - **For Google Chat** (production-ready):
     - Create a Google Cloud project and enable the Google Chat API
     - Set up OAuth consent screen and create OAuth credentials
     - Download the credentials.json file to `src/providers/google_chat/credentials.json`
   - **For other providers**:
     - Follow provider-specific setup instructions in their README files
   - Edit `provider-config.yaml` with your provider settings

4. **Run the authentication server**:

```bash
# For Google Chat:
python -m src.server --provider google_chat --local-auth

# For other providers:
python -m src.server --provider <provider_name> --local-auth
```

5. **Configure your MCP client** (e.g., Cursor):
   - Add the MCP server configuration to your MCP client's settings
   - For Google Chat in Cursor, see the [Cursor Integration Guide](src/providers/google_chat/CURSOR_INTEGRATION.md)

### Provider Configuration Schema

The `provider-config.yaml` file follows this structure:

```yaml
providers:
  provider_name:
    # Required fields
    name: "Provider Display Name"  # String: Human-readable name
    description: "Provider description"  # String: Brief description
    token_path: "path/to/token.json"  # String: Relative path for token storage
    
    # Optional fields (provider-specific)
    credentials_path: "path/to/credentials.json"  # String: OAuth credentials
    callback_url: "http://localhost:8000/auth/callback"  # String: OAuth callback URL
    scopes: ["scope1", "scope2", ...]  # Array: OAuth scopes
    # Additional provider-specific settings
```

### OAuth Scopes by Provider

#### Google Chat
- `https://www.googleapis.com/auth/chat.spaces.readonly` - Read space information
- `https://www.googleapis.com/auth/chat.messages` - Read and write messages
- `https://www.googleapis.com/auth/chat.spaces` - Manage spaces
- `https://www.googleapis.com/auth/userinfo.profile` - Access user profile information
- `https://www.googleapis.com/auth/userinfo.email` - Access user email

#### Slack (Planned)
- `chat:write` - Send messages
- Other scopes will be documented as implementation progresses

### Token Management

- **Storage**: OAuth tokens are stored at the path specified by `token_path` in your provider config
- **Refresh**: Tokens are automatically refreshed when they expire
- **Revocation**: If a token is revoked, you'll need to re-authenticate:
  ```bash
  python -m src.server --provider google_chat --local-auth
  ```
- **Security**: Tokens contain sensitive information and should be protected (added to `.gitignore` by default)

## 🔌 Providers

### Currently Supported Providers

#### Google Chat MCP (Production-Ready)

[View Google Chat Provider Documentation](src/providers/google_chat/README.md) | [Cursor Integration Guide](src/providers/google_chat/CURSOR_INTEGRATION.md)

The Google Chat provider offers comprehensive integration with Google Chat API, including:

- **Message Management**:
  - Send text messages to spaces, DMs, and group chats
  - Reply to message threads
  - Update and delete messages
  - Add emoji reactions
  
- **Powerful Search Capabilities**:
  - Regex-based search across all spaces
  - Semantic search for finding conceptually related messages
  - Search by date ranges, filters, and keywords
  
- **Space & User Management**:
  - List accessible spaces and members
  - Get user information and mentions
  - File content sharing

Google Chat MCP is fully tested and ready for production use with AI assistants like Claude in Cursor.

### Future Providers (Planned)

- **Slack**: Message sending/receiving, channel management, file sharing
- **Microsoft Teams**: Message operations, channel access, meeting integration
- **Discord**: Message operations, server management, role handling

## 🔄 How This Project Differs From Other MCP Implementations

### Feature-Rich Tools vs Basic Functionality

While other MCP server implementations might focus on basic message sending and retrieval, this project provides **comprehensive platform API coverage** with tools that enable real developer workflows:

| Feature | This Project | Basic MCP Implementations |
|---------|-------------|--------------------|
| Message Operations | ✅ Send, reply, update, delete, react | ⚠️ Typically just send/receive |
| Advanced Search | ✅ Regex, semantic, filter-based | ❌ Limited or none |
| Space Management | ✅ List, get details, find participants | ⚠️ Basic listing only |
| User Context | ✅ Profile info, mentions, participant tracking | ⚠️ Minimal user info |
| File Handling | ✅ Send files, content sharing | ❌ Limited or none |
| Real-world Use Cases | ✅ Team collaboration examples | ❌ Few practical examples |

### First Google Chat MCP Implementation

To our knowledge, this is the **first open-source Google Chat MCP implementation**, bridging a significant gap for developers using Google Workspace. The Google Chat integration is:

- **Production-ready**: Thoroughly tested in real developer workflows
- **Comprehensive**: Covering nearly all Google Chat API functionality
- **Documented**: With clear examples and integration guides
- **Developer-focused**: Designed for practical daily use in engineering teams

### Developer-First Philosophy

This project emerged from real developer needs, not theoretical use cases:

- Created by developers who use these tools daily
- Designed to solve actual workflow challenges
- Battle-tested in real team environments
- Continuously improved based on real-world feedback

## 🧩 Extending with New Providers

### How to Add a New Provider

Adding a new provider is straightforward with our modular architecture:

1. **Create provider directory structure**:

```
src/providers/your_provider/
├── api/                # API client implementations
├── tools/              # MCP tool implementations
├── utils/              # Utility functions
├── __init__.py
├── mcp_instance.py     # MCP instance configuration
├── server_auth.py      # Authentication handling
└── README.md           # Provider documentation
```

2. **Update provider configuration**:
   - Add your provider configuration to `provider-config.yaml`
   - Configure paths as relative paths from the project root directory
   - Example:
   ```yaml
   providers:
     your_provider:
       name: Your Provider MCP
       description: MCP server for Your Provider
       token_path: src/providers/your_provider/token.json
       credentials_path: src/providers/your_provider/credentials.json
       # other configuration...
   ```

3. **Implement required modules**:
   - `mcp_instance.py`: Create and configure the MCP instance
   - `server_auth.py`: Implement authentication handling
   - API modules: Create client code for your provider's API
   - Tool modules: Implement tools to interact with your provider

4. **Register tools**:
   - Use the provided tool decorator to register your tools

For detailed instructions, see the [Provider Development Guide](PROVIDER_SPECIFIC_DEVELOPMENT_DEMO.md).

### Recommended Provider Directory Structure

```
src/providers/your_provider/
├── api/
│   ├── auth.py            # Authentication utilities
│   ├── messages.py        # Message-related API calls
│   ├── spaces.py          # Spaces/channels/rooms API calls
│   └── users.py           # User-related API calls
├── tools/
│   ├── message_tools.py   # Message-related tools
│   ├── space_tools.py     # Space/channel management tools
│   └── user_tools.py      # User information tools
├── utils/
│   └── helpers.py         # Provider-specific utilities
├── __init__.py
├── mcp_instance.py        # MCP instance creation
└── server_auth.py         # Authentication server
```

## 🛠 Common Tools and Utilities

The MCP Core module provides shared functionality for all providers:

- **Registry System**: Central registration of all tools
- **Provider Loader**: Dynamic loading of provider modules
- **Tool Decorator**: Simplified tool registration

## 📋 MCP Client Configuration

Configure your MCP client (e.g., Cursor) by editing the configuration file:

```json
{
  "mcpServers": {
    "google_chat": {
      "command": "uv",
      "args": [
        "--directory", "/path/to/multi-chat-mcp-server",
        "run", "-m", "src.server",
        "--provider", "google_chat"
      ]
    },
    "slack": {
      "command": "uv",
      "args": [
        "--directory", "/path/to/multi-chat-mcp-server",
        "run", "-m", "src.server",
        "--provider", "slack"
      ]
    }
  }
}
```

## 🧪 Testing

Run tests using pytest:

```bash
# Run all tests
pytest

# Run tests for a specific provider
pytest src/providers/google_chat
```

## 📚 Architecture & Documentation

This project follows a modular architecture with these key components:

- **Core Engine**: Provider loading and configuration
- **Tool Registry**: Central registration system for tools
- **Provider Modules**: Platform-specific implementations
- **MCP Interface**: Standard interface for AI interactions

## ⚠️ Troubleshooting & Known Issues

- **Authentication issues**: Ensure credentials files are correctly placed and formatted
- **Tool availability**: Check that tools are properly registered with the MCP instance
- **Provider-specific issues**: See provider documentation for specific troubleshooting

## 🔮 Future Roadmap

- Additional provider implementations (Teams, Discord)
- Enhanced authentication flows
- More advanced semantic search capabilities
- Improved file attachment handling
- User interface for configuration

## 📄 License & Ownership

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Copyright

Copyright (c) 2025 Sivaprakash Kumar. All rights reserved.

While this is an open-source project that welcomes contributions, all copyright and ownership rights remain with Sivaprakash Kumar. See the [COPYRIGHT](COPYRIGHT) file for more information.

### Contributing

Contributions are welcome! By submitting a contribution, you agree to our [Contributor License Agreement](CONTRIBUTOR_LICENSE_AGREEMENT.md), which ensures that:

1. Contributions become part of the codebase under the same MIT license
2. Copyright ownership of all contributions is assigned to Sivaprakash Kumar
3. You have the legal right to contribute the code

Please read the full CLA before contributing.

## 📝 Documentation

For information on adding support for new providers or extending the Google Chat MCP functionality, see the [Provider Development Guide](PROVIDER_SPECIFIC_DEVELOPMENT_DEMO.md).

## 🔍 Keywords

google chat mcp, multi-provider mcp, google chat claude, google chat ai assistant, mcp server, model control protocol, google workspace ai integration, claude google chat, anthropic claude integration, cursor google chat, slack mcp, chat platform ai integration

## 📞 Contact & Support

For questions, feature requests, or bug reports, please open an issue on our GitHub repository. 