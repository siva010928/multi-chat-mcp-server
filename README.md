# Multi-Provider MCP Server

<div align="center">
  <h3>A modular, extensible framework for AI assistants to interact with chat platforms</h3>
</div>

## 🌟 Overview

**Multi-Provider MCP Server** is the first open-source accelerator tool designed to connect AI assistants with various chat platforms through a unified Model Control Protocol (MCP) interface. This framework allows AI assistants like Claude to seamlessly interact with supported chat platforms, with current implementation for Google Chat and planned support for other providers.

### Supported Providers

- ✅ **Google Chat** - Full implementation with comprehensive API support
- 🔄 **Slack** - In progress (structure ready for implementation)
- 📝 **Microsoft Teams** - Planned
- 📝 **Discord** - Planned

### Key Benefits

- **Provider Agnostic**: One unified interface for multiple chat platforms
- **Modular Architecture**: Easy extension to new providers
- **Pre-built Tools**: Rich set of interface tools for each provider
- **Authentication Management**: Built-in OAuth support and token management
- **Dynamic Loading**: Load only the components needed for each provider

## 📁 Project Structure

```
google-chat-mcp-server-main/
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
│   │   │   ├── utils/         # Utility functions
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
git clone https://github.com/siva010928/google-chat-mcp-server.git
cd google-chat-mcp-server-main
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
   - Edit `provider-config.yaml` with your provider settings
   - Follow provider-specific setup instructions (see provider READMEs)

4. **Run the authentication server** (if needed by your provider):

```bash
python -m src.server --provider google_chat --local-auth
```

5. **Configure your MCP client** (e.g., Cursor):
   - Add the MCP server configuration to your MCP client's settings

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

#### Google Chat

[View Google Chat Provider Documentation](src/providers/google_chat/README.md)

The Google Chat provider offers comprehensive integration with Google Chat API, including:
- Message sending and retrieval
- Advanced search capabilities
- Space management
- User information access
- File attachments

### Future Providers (Planned)

- **Slack**: Message sending/receiving, channel management, file sharing
- **Microsoft Teams**: Message operations, channel access, meeting integration
- **Discord**: Message operations, server management, role handling

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
        "--directory", "/path/to/google-chat-mcp-server-main",
        "run", "-m", "src.server",
        "--provider", "google_chat"
      ]
    },
    "slack": {
      "command": "uv",
      "args": [
        "--directory", "/path/to/google-chat-mcp-server-main",
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

For information on adding support for new providers, see the [Provider Development Guide](PROVIDER_SPECIFIC_DEVELOPMENT_DEMO.md).

## 📞 Contact & Support

For questions, feature requests, or bug reports, please open an issue on our GitHub repository. 