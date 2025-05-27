# Cursor Integration with Google Chat MCP

This document provides detailed instructions for integrating the **Google Chat MCP server** with the **Cursor AI assistant**, enabling the agent to collaborate inside team chat spaces using MCP tools.

---

## ⚙️ Configuration: Connecting Cursor with Google Chat MCP

1. Edit your `~/.cursor/mcp.json` file to register the Google Chat MCP server:

```json
{
  "mcpServers": {
    "google_chat": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/multi-chat-mcp-server",
        "run",
        "-m", 
        "src.server",
        "--provider", 
        "google_chat"
      ]
    }
  }
}
````

> ✅ Replace `/absolute/path/to/multi-chat-mcp-server` with the **full path** to your repo.
> 💡 We recommend using `uv` for fast startup and dependency isolation.

---

## ✅ Cursor Project Rule: Enable AI Team Messaging via Google Chat

To enable seamless team communication using Google Chat MCP, add this **project rule** to your Cursor environment.

Find your desired chat space (e.g. "Frontend Team" or "DevOps Alerts") and copy the space ID in the format:

```
spaces/AAAAABBBBCCC
```

---

### Step 2: Add Rule File to `.cursor/rules/team-communication.mdc`

Create the following file inside your project:

📄 `.cursor/rules/team-communication.mdc`

```mdc
---
description: Interprets natural language phrases to invoke Google Chat MCP tools for messaging, replying, searching, reacting, uploading, and summarizing
alwaysApply: true
globs:
  - "**/*"
---

- When I say something like:
  - "Send this to [team/space/alias]"
  - "Let the team know"
  - "Update [frontend/backend/devops]"
  - "Reply to that with [text]"
  - "Post this in the thread"
  - "Share this update"
  - "Upload this file"

  → Send a message or reply to a thread:
    - If I mentioned a thread: reply to it
    - If no thread is referenced: post as a new message in the mapped space
    - Support formatting (bold, emoji, code blocks) and space aliases
    - If a file is present, include it either as inline text or attachment

- When I say:
  - "Catch me up on [topic]"
  - "Search for [keyword]"
  - "Find messages about [X]"
  - "Look up what happened regarding [Y]"

  → Search across spaces:
    - Default to `semantic` search with `days_window=3`, `offset=0`
    - If no results, fallback to `days_window=6`, then `30`
    - If the query looks like a pattern (e.g., uses | or \b), switch to `regex`
    - If I say “exactly”, use `exact` search mode
    - If I mention a time like “3 days ago”, use `days_window=1`, `offset=3`
    - If I say “last week”, use `days_window=7`, `offset=7`

- When I say:
  - "Who mentioned me?"
  - "Check my mentions"
  - "Was I tagged in [space/topic]?"

  → Get mentions of the current user:
    - Use `days=7`, `offset=0`
    - If I mention a space, narrow the search

- When I say:
  - "Show recent messages from [space]"
  - "List messages in this chat"
  - "Get the last [N] messages"

  → Fetch raw message history:
    - Use `get_space_messages` or equivalent
    - Use `days_window=3`, or time offset if specified
    - Order by most recent first unless I say “chronologically”

- When I say:
  - "React with 👍"
  - "Add a reaction to that"

  → Add emoji reaction to the last referenced message

- When I say:
  - "Summarize this chat"
  - "Give me a summary of [space/thread]"

  → Use summary tool to generate conversation overview with participants, messages, and highlights

- When I say:
  - "Who’s active in [space]?"
  - "List recent contributors"

  → Get participants in space using `days_window` as inferred from time expressions

- Alias mapping for space names:
  - frontend → spaces/AAA_FRONTEND_ID
  - backend → spaces/BBB_BACKEND_ID
  - devops → spaces/CCC_DEVOPS_ID

- Use confirmation prompts when the request is vague:
  - “Should I send this to frontend?”
  - “Here's what I found. Should I summarize?”

- Avoid summarizing or truncating messages unless explicitly instructed

- Ensure message_count and sender_info are included when useful

- Always handle file-based input by deciding:
  - If it should be shared as an attachment
  - If text content should be embedded directly

- Always behave as a proactive team assistant — reply as a helpful collaborator
```

> ✅ Replace each space ID with your actual values

---

## 🧠 Customize the Rule

You can tweak the rule to fit your org’s communication style:

| Option                | How to customize                                     |
| --------------------- | ---------------------------------------------------- |
| Trigger phrases       | Add phrases like “ping team” or “drop this in infra” |
| Team aliases          | Add new mappings like `qa` → `spaces/XXX_QA_ID`      |
| Message preview rules | Skip preview for specific aliases or short messages  |

---

## 🔗 Additional Resources

* [Cursor Rule Docs](https://docs.cursor.com/context/rules)
* [Cursor Rule Generator (from chat)](https://docs.cursor.com/context/rules#generating-rules)