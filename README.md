# Multi-Chat MCP Server (Google Chat Included)

<div align="center">
  <p style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 5px solid #4285f4; max-width: 800px; margin: 0 auto;">
    <strong>🔥 UNIQUE FEATURE:</strong> Run <strong>multiple chat providers simultaneously</strong> with a single AI assistant!<br>
    Your AI can interact with Google Chat, Slack, Teams, and more—all at once. <br>
    Ask once: <em>"Share this update with both Slack and Google Chat teams"</em><br>
    <a href="#running-multiple-chat-providers-simultaneously">➡️ Learn more about multi-provider capabilities</a>
  </p>
</div>

<div align="center">
  <h3>Multi-Chat MCP Server is an open-source Python framework to build AI-powered chat integrations. Ships with full Google Chat support.</h3>
  
  <p>
    <strong>Keywords:</strong> Google Chat MCP • MCP Server Implementation • AI Chat Integration • Google Workspace Automation • Team Collaboration AI
  </p>
</div>

---

## 🎯 What is Google Chat MCP Server?

**Google Chat MCP Server** is an open-source, production-ready **Model Control Protocol (MCP) server** designed for **Google Chat integration with AI assistants**. Built with an extensible **multi-provider architecture**, this project provides a robust foundation for integrating AI assistants with team chat platforms.

### 🏢 Built for Organizational Security & Privacy

**Important Security Note:** This tool is **designed for local, organizational use only**. We strongly recommend using this with **organization-provided on-premises LLM instances or your local installed LLM Agent Model** rather than cloud-based LLM model's to maintain complete control over your team's chat data and communications.

**Why Local/On-Premises Deployment:**
- **Data Privacy**: Keep sensitive team conversations within your organization
- **Security Compliance**: Meet enterprise security and compliance requirements
- **Full Control**: Maintain complete oversight of data flow and access
- **Custom Policies**: Implement organization-specific security measures

While anyone can adapt this tool for their particular use cases, it's designed with enterprise security as a priority.

### Current Implementation Status

- ✅ **Google Chat Provider** - **Production Ready** with comprehensive API coverage
- 🔄 **Slack Provider** - Planned (contributions welcome)
- 📝 **Microsoft Teams Provider** - Planned (contributions welcome)

**Key Capability**: All providers can run simultaneously with a unified interface, allowing your AI assistant to seamlessly work across multiple chat platforms at once. [Learn more](#step-4-running-multiple-chat-providers-simultaneously) about this powerful feature.

### 🧭 The Story Behind This Project

> *We even see open-source MCP servers for Google Chat — but not sure about Microsoft Teams or Slack, officially or in open source. However, even the ones that do exist fall short in real-world applicability. They offer limited functionalities that cannot handle full-context workflows like this project demonstrates.*

This **multi-provider MCP framework** was born from a real frustration experienced by development teams trying to leverage AI assistants in their daily workflows.

---

#### **The Original Problem**

Picture this scenario: You're debugging a complex issue, your AI assistant suggests a solution, but you need to check if your teammates have encountered something similar. You switch to Google Chat, scroll through hundreds of messages, copy-paste error logs, wait for responses, then manually relay the solution back to your AI assistant.

This constant context-switching was breaking the flow of productive AI-assisted development.

---

#### **The Breaking Point**

During a critical production incident, a developer spent 30 minutes manually shuttling information between Claude (via Cursor) and the team's Google Chat space. The AI had the technical knowledge to help. The team had the contextual experience.
But there was no bridge connecting these two knowledge sources.

That's when we realized:

> **AI assistants need to be participants in team collaboration — not isolated tools.**

**Our Solution:**
- **Seamless Integration**: AI assistants become active participants in team chat
- **Contextual Awareness**: AI can search team history for similar issues and solutions
- **Collaborative Problem-Solving**: AI can share problems with the team and implement their suggestions
- **Knowledge Bridging**: Connect AI technical knowledge with team experiential knowledge

## 🎯 Built for Developer Extensibility

### 🏗️ Modular Provider Architecture

Each chat platform is implemented as an independent module:

```
src/providers/
├── google_chat/     # ✅ Complete implementation
├── slack/           # 📋 Framework ready for implementation  
└── teams/           # 📋 Framework ready for implementation
```


### 👥 Who's This For?

This project is designed for **two primary audiences**:

#### 🛠️ 1. Developers inside organizations

If you're a developer working in a team that uses **Google Chat**, and you're looking to integrate your **AI IDEs (like Cursor, CodeWhisperer, or Copilot Chat)** with team conversations — this MCP client will save you hours.
No more manually copying logs, checking for context, or waiting for someone to see your question.
Your AI agent can now directly:

* Search your chat history for relevant past discussions
* Share code snippets or error logs automatically
* Receive responses and convert them into actionable fixes
* Summarize ongoing team activities
* Fetch missing config/scripts from shared spaces

#### 💡 2. Open source contributors & AI platform builders

If you're building AI-powered tools, IDE integrations, or internal assistants — this is your starting point for a **multi-provider MCP architecture**.
You can fork this project to:

* Extend support for **Slack**, **Microsoft Teams**, or **custom messaging platforms**
* Build your own custom AI workflows on top of MCP


## 🧩 Google Chat MCP Server – Real-world Usage Showcase

These walkthroughs show how an AI assistant, powered by this MCP server, evolves from a passive tool into an active collaborator — debugging issues, coordinating teams, syncing scripts, and proactively unblocking developers.

---

### 🛠️ Tool Setup & Initialization

<div align="center">
  <img src="google_chat_mcp_client_demo_images/how_google_chat_mcp_tools_registered_with_mcp_client.png" width="80%" alt="Scene 1: Tool Registration with Google Chat"/>
  <p><i><strong>Scene 1: Tool Registration with Google Chat</strong></i></p>
</div>

**The Scenario:** Connecting MCP client to Google Chat.

**What's Happening:** The AI assistant is granted access to all Google Chat tools (e.g., send, search, summarize, attach, reply).

**Why it Matters:** The assistant can now *act* inside Google Chat, not just observe.

---

### 🧯 Debugging & Resolution (Docker Example)

<div align="center">
  <img src="google_chat_mcp_client_demo_images/how_i_asked_mcp_client_to_share_my_error_along_with_logs_to_get_help_from_my_team.png" width="80%" alt="Scene 8: Broadcasting an Error to the Team"/>
  <p><i><strong>Scene 2: Broadcasting an Error to the Team</strong></i></p>
</div>

**What's Happening:** A developer asks the AI to share Docker error logs in chat, prompting real-time team help.

<div align="center">
  <img src="google_chat_mcp_client_demo_images/proof_that_team_member_replied_with_instructions_to_fix_the_errors_i_shared.png" width="80%" alt="Scene 3: Receiving a Fix from a Teammate"/>
  <p><i><strong>Scene 3: Team Responds with a Fix</strong></i></p>
</div>

**Next Step:** A teammate replies with a Dockerfile fix (`COPY requirements.txt .`).

<div align="center">
  <img src="google_chat_mcp_client_demo_images/how_i_asked_mcp_client_to_check_with_response_of_my_error_issues_which_i_shared_recently_and_how_i_asked_to_follow_instructions_of_the_response_from_my_team_to_fix_the_issue.png" width="80%" alt="Scene 4: Agent Applies Suggested Fix"/>
  <p><i><strong>Scene 4: Agent Applies the Fix</strong></i></p>
</div>

**Automation Moment:** The AI assistant edits the Dockerfile per the advice — no manual effort.

<div align="center">
  <img src="google_chat_mcp_client_demo_images/how_mcp_client_properly_followed_my_team_member_instructions_for_the_concern_i_shared.png" width="80%" alt="Scene 5: Verifying the Fix"/>
  <p><i><strong>Scene 5: Verifying the Fix</strong></i></p>
</div>

**Wrap-up:** It verifies the change, confirms `requirements.txt` exists — and the error should be resolved.

---

### 📦 Dependency & Script Sync

<div align="center">
  <img src="google_chat_mcp_client_demo_images/proof_that_mcp_client_again_3rd_time_properly_assisted_the_concern_i_asked_to_then_it_properly_provided_my_local_latest_requirements_file_to_someone_who_facing_the_issues_with_requirements.png" width="80%" alt="Scene 6: Sharing requirements.txt"/>
  <p><i><strong>Scene 6: Sharing `requirements.txt`</strong></i></p>
</div>

**Scenario:** I have requested my team requests to share a working `requirements.txt`.

**Response:** One of my teammate shared their working `requirements.txt`.

<div align="center">
  <img src="google_chat_mcp_client_demo_images/how_i_asked_mcp_client_to_pull_the_lastest_requirements_and_modifying_with_the_local_one_that_i_asked_for_in_team_space_after_someone_shared_the_requirements_file.png" width="80%" alt="Scene 7: Syncing requirements.txt"/>
  <p><i><strong>Scene 7: Syncing Local Copy</strong></i></p>
</div>

**Developer POV:** The AI reviewed the thread and based on my instruction, it updated my local `requirements.txt` with the one that was shared

---

<div align="center">
  <img src="google_chat_mcp_client_demo_images/how_i_asked_my_team_to_share_aws-setup.sh_scrip_in_google_chat_space.png" width="80%" alt="Scene 8: Requesting AWS Setup Script"/>
  <p><i><strong>Scene 8: Requesting AWS Setup Script</strong></i></p>
</div>

**Scenario:** You ask your team for a shared `aws-setup.sh` script.

<div align="center">
  <img src="google_chat_mcp_client_demo_images/how_mcp_client_get_aws-script-from-team-space-and-compare-it-with-local-one-after-team-member-replied-to-my-previous-requesting-aws-setup-script.png" width="80%" alt="Scene 9: Script Consistency Check"/>
  <p><i><strong>Scene 9: Script Consistency Check</strong></i></p>
</div>

**Developer POV:** The AI reviewed the thread and based on my instruction, it compares the team's script with your local version — ensuring you're in sync.

---

### 👀 Team Coordination & Catch-Up

<div align="center">
  <img src="google_chat_mcp_client_demo_images/how_i_asked_to_summarize_my_team_space_today_about_what_is_hapening_like_a_quick_updates.png" width="80%" alt="Scene 10: Summarizing Team Activity"/>
  <p><i><strong>Scene 10: Summarizing Team Activity</strong></i></p>
</div>

**Context:** You've been away. What's new?

**AI Response:** The assistant summarizes key activity in your space: questions, PRs, shared files, blockers.

<div align="center">
  <img src="google_chat_mcp_client_demo_images/how_mcp_client(cursor)_get_my_mentions_from_team_chat_space.png" width="80%" alt="Scene 11: Catching Up on Mentions"/>
  <p><i><strong>Scene 11: Catching Up on Mentions</strong></i></p>
</div>

**Missed a ping?** The AI scans for all mentions and surfaces conversations you were tagged in.

---

### 🔍 AI-Powered Problem Solving from Team Chat Context

<div align="center">
  <img src="google_chat_mcp_client_demo_images/how_mcp_client_again_search_for_any_concerns_in_our_chat_space_related_to_our_project_specifcally_to_assist_them_and_well_it_understand_the_concerns_and_assist_them.png" width="80%" alt="Scene 12: AI Scanning Team Chat for Problems"/>
  <p><i><strong>Scene 12: AI Scanning Team Chat for Problems</strong></i></p>
</div>

**The Scenario:** A developer explicitly asks the AI assistant to help resolve open concerns mentioned by the team in the chat space.

**What's Happening:** The AI scans recent chat messages, identifies technical questions, missing files, and potential blockers related to the project, and prepares to assist.

**Developer Perspective:** The agent isn't just reactive — it understands team context and can search for unresolved issues when prompted.

<div align="center">
  <img src="google_chat_mcp_client_demo_images/proof_that_mcp_client_properly_assisted_the_concern_i_asked_to.png" width="80%" alt="Scene 13: AI Finds the Missing File Path"/>
  <p><i><strong>Scene 13: AI Finds the Missing File Path</strong></i></p>
</div>

**Example Use Case:** A teammate mentioned they couldn't find `ReviewForm.js`.

**AI Response:** The agent searches the local repo, finds the correct path, and replies directly in the chat thread.

**Why it Matters:** Instead of waiting for someone to respond, the AI assistant unblocks teammates in real-time with accurate, repo-aware answers — making onboarding and collaboration faster and smoother.

## 🚀 Quick Start: Google Chat MCP Server Setup

### Prerequisites

- **Python 3.9+**
- **UV Package Manager** (recommended)
- **Google Cloud Project** with Google Chat API enabled
- **MCP Client** (Claude Desktop, Cursor, or other MCP-compatible AI assistant)

### Step 1: Installation

```bash
# Clone the repository
git clone https://github.com/siva010928/multi-chat-mcp-server.git
cd multi-chat-mcp-server

# Install dependencies
uv venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

### Step 2: Google Chat Authentication Setup

```bash
# Set up Google Chat API credentials
# 1. Create Google Cloud project
# 2. Enable Google Chat API
# 3. Download credentials.json to src/providers/google_chat/

# Run authentication
python -m src.server --provider google_chat --local-auth
```

### Step 3: Connect to Your AI Assistant

For **Cursor + Claude integration**, see our detailed [Google Chat MCP Cursor Integration Guide](src/providers/google_chat/CURSOR_INTEGRATION.md).

For other MCP clients, add this configuration:

```json
{
  "mcpServers": {
    "google_chat_mcp": {
      "command": "uv",
      "args": [
        "--directory", "/path/to/multi-chat-mcp-server",
        "run", "-m", "src.server",
        "--provider", "google_chat"
      ]
    }
  }
}
```


### 📖 Detailed Setup Documentation

For comprehensive setup instructions including Google Cloud configuration, OAuth setup, and troubleshooting, see our **[Complete Google Chat MCP Setup Guide](src/providers/google_chat/README.md)** - This detailed implementation guide covers:

- Google Cloud Project setup and API enablement
- OAuth 2.0 configuration and security best practices
- Step-by-step authentication flow
- Common setup issues and their solutions

## Google Chat Tools Supported (will be extended)

Interact with Google Chat using the tools below. Each tool includes its source file and parameters.

### 🧭 Space Management

* `get_chat_spaces_tool` – List spaces
* `manage_space_members_tool` – Add/remove members
* `get_conversation_participants_tool` – Get space participants
* `summarize_conversation_tool` – Summarize conversation

### 💬 Messaging

* `send_message_tool` – Send a message
* `reply_to_message_thread_tool` – Reply in thread
* `update_chat_message_tool` – Update message
* `delete_chat_message_tool` – Delete message

### 😀 Interactions

* `add_emoji_reaction_tool` – React to message
* `get_chat_message_tool` – Get message details

### 🔍 Search & Filters

* `search_messages_tool` – Search messages
* `get_my_mentions_tool` – Find mentions

### 👤 User Info

* `get_my_user_info_tool` – Your profile
* `get_user_info_by_id_tool` – User by ID
* `get_message_with_sender_info_tool` – Message with sender info
* `list_messages_with_sender_info_tool` – List messages with sender info

### 📎 File Handling

* `upload_attachment_tool` – Upload attachment
* `send_file_message_tool` – Send file content
* `send_file_content_tool` – Send formatted file content

### 📦 Batch Operations

* `batch_send_messages_tool` – Send multiple messages

📁 *Source files located under `src/providers/google_chat/tools/`*


## Running Multiple Chat Providers Simultaneously

One of the key advantages of Multi Chat MCP Server is the ability to run **multiple chat providers simultaneously**. Each provider runs in its own server instance, allowing your AI assistant to interact with multiple platforms at once.

For example, you can configure both Google Chat and Slack MCP servers to run simultaneously:

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

With this setup, your AI assistant can:
- Access tools from all configured providers simultaneously
- Execute cross-platform actions with a single command
- Perform platform-specific operations through named providers

#### Real-World Multi-Platform Scenarios

| Scenario | Example Command to AI | What Happens |
|----------|-------------|-------------|
| **Incident Response** | "Share this error log with both our Slack #on-call channel and Google Chat #tech-huddle team" | AI posts the error in both platforms simultaneously, with appropriate formatting for each |
| **Knowledge Consolidation** | "Find all discussions about the authentication issue across Slack #LLMSpace and Google Chat #LLMTools in the last week" | AI searches both platforms and presents a unified summary of all relevant conversations |
| **Cross-Team Coordination** | "Let the frontend team on Slack and backend team on Google Chat know we're delaying the release by 2 days" | AI composes appropriate messages for each team on their preferred platform |
| **Multi-Team Standups** | "Collect status updates from all teams across Slack and Google Chat from standup space and summarize them for last 3 days." | AI retrieves and consolidates information from both platforms into a single summary |

#### Business Value of Multi-Provider Integration

- **Reduce Tool Switching**: No need for developers to constantly switch between chat platforms for smaller use-cases like sharing error logs or instructions or reply
- **Unified Context**: Your AI assistant maintains awareness across all your organization's communication channels

Each provider is defined separately in `provider-config.yaml`, allowing you to extend support for any chat platform while maintaining a unified interface for your AI assistant.


## 🔥 Real-World Workflows Enabled

The demo walkthrough above demonstrates these practical team collaboration workflows:

### Collaborative Problem Solving
- **Error Sharing & Resolution**: AI shares developer errors with team, receives expert guidance, and implements solutions
- **Knowledge Transfer**: Team expertise is captured and applied through AI assistance
- **Proactive Issue Detection**: AI monitors team chat for emerging concerns and offers assistance

### Intelligent Resource Management
- **Script Exchange**: Request and receive team scripts with automatic comparison to local versions
- **Requirements Synchronization**: Pull and merge requirements files from team discussions
- **Context-Aware Sharing**: AI determines optimal file sharing based on team needs

### Enhanced Team Communication
- **Mention Tracking**: Comprehensive monitoring and response to team mentions
- **Activity Summaries**: AI-generated updates on team progress and blockers
- **Semantic Search**: Find conceptually related discussions across team spaces

## 📁 Project Architecture

```
multi-chat-mcp-server/
├── src/
│   ├── providers/
│   │   ├── google_chat/           # ✅Production-Ready Google Chat MCP
│   │   │   ├── api/               # Google Chat API implementation
│   │   │   ├── tools/             # MCP tools for Google Chat
│   │   │   ├── utils/             # Utilities and helpers
│   │   │   ├── README.md          # Setup guide
│   │   │   └── CURSOR_INTEGRATION.md  # Cursor integration
│   │   ├── slack/                 # 📋 Ready for implementation
│   │   └── teams/                 # 📋 Ready for implementation
│   ├── mcp_core/                  # Core MCP functionality
│   └── server.py                  # Multi-provider MCP server
├── provider-config.yaml           # Provider configurations
└── google_chat_mcp_client_demo_images/  # Demo screenshots
```

### Provider Configuration

```yaml
providers:
  google_chat:
    name: "Google Chat MCP Server"
    description: "Production-ready Google Chat MCP integration"
    token_path: "src/providers/google_chat/token.json"
    credentials_path: "src/providers/google_chat/credentials.json"
    callback_url: "http://localhost:8000/auth/callback"
```

## 🔮 Roadmap & Contributing

### Current Implementation Status
- ✅ **Google Chat Provider** - Production ready with comprehensive features
- 📋 **Slack Provider** - Framework ready, implementation needed
- 📋 **Teams Provider** - Framework ready, implementation needed

### How to Contribute

We welcome contributions to extend this framework with additional providers:

1. **Choose a Provider**: Slack, Teams, or any other chat platform
2. **Follow the Architecture**: Use `src/providers/google_chat/` as a reference
3. **Implement Core Features**: Messages, search, user management
4. **Add Provider-Specific Tools**: Leverage unique platform capabilities
5. **Submit Pull Request**: We'll help review and integrate

**Getting Started with Contributions:**
- 📖 **[Provider Development Guide](docs/PROVIDER_SPECIFIC_DEVELOPMENT_WALKTHROUGH)** - Technical implementation details
- 🔗 **[GitHub Issues](https://github.com/siva010928/multi-chat-mcp-server/issues)** - Find tasks or report bugs
- 💬 **[GitHub Discussions](https://github.com/siva010928/multi-chat-mcp-server/discussions)** - Feature requests and ideas
## 📚 Documentation

### Essential Resources

- 📖 **[Complete Google Chat MCP Setup Guide](src/providers/google_chat/README.md)** - Detailed implementation guide
- 🔗 **[Google Chat MCP + Cursor Integration](src/providers/google_chat/CURSOR_INTEGRATION.md)** - Step-by-step Cursor setup
- 🛠️ **[Provider Development Guide](docs/PROVIDER_SPECIFIC_DEVELOPMENT_WALKTHROUGH)** - Extend functionality
- ⚖️ **[Contributor License Agreement](docs/CONTRIBUTOR_LICENSE_AGREEMENT.md)** - Contributing guidelines

## 🔍 Troubleshooting

### Common Google Chat Issues

**Authentication Problems**
```bash
# Re-authenticate Google Chat
python -m src.server --provider google_chat --local-auth
```

**Tool Registration Issues**
- Verify tools appear in your AI assistant
- Check provider configuration in `provider-config.yaml`
- Ensure all Google Chat API scopes are granted

**Connection Problems**
- Confirm Google Chat API is enabled in Google Cloud Console
- Verify credentials.json file placement
- Check network connectivity and firewall settings

## 🏆 Why Choose This MCP Server?

### ✅ Battle-Tested Google Chat Integration
- **Comprehensive API coverage** beyond basic messaging
- **Real-world workflows** tested in development environments
- **Production-ready** with proper error handling and authentication

### ✅ Developer-Friendly Architecture
- **Created by developers** for actual development workflows
- **Modular design** makes it easy to understand and extend
- **Well-documented** with practical examples

### ✅ Community-Extensible Framework
- **Open source** with transparent development
- **Contributor-friendly** architecture and documentation
- **Multi-provider ready** for diverse business needs

## 📞 Support & Community

### Get Help

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/siva010928/multi-chat-mcp-server/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/siva010928/multi-chat-mcp-server/discussions)
- 🛠️ **Development Questions**: Open an issue with technical details

### Contributing

We welcome contributions to expand this multi-provider framework:

1. **Fork** the repository
2. **Create** a feature branch for your provider or enhancement
3. **Follow** the existing architecture patterns
4. **Submit** a pull request
5. **Sign** our [Contributor License Agreement](docs/CONTRIBUTOR_LICENSE_AGREEMENT.md)

## 📄 License & Copyright

### Open Source License
This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

### Copyright Notice
Copyright (c) 2025 Sivaprakash Kumar. All rights reserved.

While this is an open-source project welcoming contributions, all copyright and ownership rights remain with Sivaprakash Kumar. See [COPYRIGHT](docs/COPYRIGHT) for details.

---

<div align="center">
  <h3>🚀 Start Building with Google Chat MCP Server Today!</h3>
  <p>
    <strong>Production-ready Google Chat integration with extensible multi-provider architecture</strong><br>
    Perfect for developers building AI-powered team collaboration tools
  </p>
  
  <p>
    <strong>⭐ Star this repository if it helps your development workflow!</strong><br>
    <strong>🤝 Contribute to expand support for Slack, Teams, and other platforms!</strong>
  </p>
</div>