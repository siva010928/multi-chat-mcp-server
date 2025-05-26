# Cursor Integration with Google Chat MCP

This document provides detailed instructions for integrating the Google Chat MCP server with the Cursor AI assistant.

## Configuration

1. Edit your `~/.cursor/mcp.json` file to include the Google Chat MCP server:

```json
{
  "mcpServers": {
    "google_chat": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/google-chat-mcp-server",
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

Replace `/path/to/google-chat-mcp-server` with the absolute path to your repository.

> **Note**: While local development can use Python directly, MCP clients like Cursor work best with UV for dependency isolation.

## Custom Rule for Team Communication

To maximize the effectiveness of the Google Chat MCP integration with Cursor, consider adding the following rule to your Cursor custom instructions. This rule automates team communications and information retrieval through Google Chat.

First, find your Google Chat space ID:

1. Use the `mcp_google_chat_get_chat_spaces_tool(random_string="list")` in Cursor
2. Look for the space you want to use as your team chat
3. Note the ID in the format `spaces/YOUR_SPACE_ID` 

Then add this rule to your Cursor custom instructions, replacing `YOUR_SPACE_ID` with your actual space ID:

```
# Google Chat Team Communication Rule

If I say anything that implies communicating with my team—including phrases like:

"Catch me up with [topic/updates/etc.]"
"Update my team"
"Send this to the team"
"Let the team know"
"Share with my team"
"Message the team"
"Convey this to them"
"Team should know this"
"Notify the team"
"Tell everyone"
"Broadcast this"
"Share this update"
"Remind them about [something]"

Interpret this as a command to send a message via the Google Chat MCP agent using:

space_name: spaces/YOUR_SPACE_ID
text: [the content from my message]

For unclear requests:
1. Draft a message
2. Ask "Here's what I'll send to the team. Approve?"
3. Wait for my confirmation

For "catch me up" requests:
1. Search with "semantic" mode first
2. If no results, try "regex" mode
3. Show all results without excessive summarization

Examples:
- "Let team know we're launching tomorrow" → send immediately
- "Share this update with everyone" → show draft for approval
- "Catch me up with project updates" → search and show full results
```

## Usage Tips

1. **Space Discovery**: Use `mcp_google_chat_get_chat_spaces_tool(random_string="list")` to find available spaces.

2. **Search Commands**: Use both semantic and regex search for best results:
   ```
   mcp_google_chat_search_messages_tool(query="meeting", search_mode="semantic")
   ```

3. **Thread Replies**: To reply to existing threads, specify the thread key from a message:
   ```
   mcp_google_chat_reply_to_message_thread_tool(
     space_name="spaces/YOUR_SPACE_ID", 
     thread_key="THREAD_KEY", 
     text="My reply"
   )
   ```

4. **Getting Mentions**: Periodically check for mentions:
   ```
   mcp_google_chat_get_my_mentions_tool()
   ```

## Advanced Customization

You can modify the custom rule to match your team's specific communication style. The key components you might want to customize:

1. **Trigger Phrases**: Add or remove phrases that should trigger team communication
2. **Space ID**: Change the default space for communications
3. **Approval Process**: Adjust when messages require explicit approval
4. **Search Behavior**: Modify how "catch me up" searches are performed

For additional help with Cursor integration, refer to the [Cursor documentation](https://cursor.sh/docs/mcp-configuration). 