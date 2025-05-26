# Repository Rename Guide

This guide will help you rename your repository from `google-chat-mcp-server` to `multi-chat-mcp-server` both on GitHub and locally.

## Steps to Rename Your Repository

### 1. GitHub Repository Rename

1. Go to your repository on GitHub: https://github.com/siva010928/google-chat-mcp-server
2. Click on "Settings" tab
3. Under the "General" section, find the "Repository name" field
4. Change the name from `google-chat-mcp-server` to `multi-chat-mcp-server`
5. Click "Rename" button

GitHub will automatically set up redirects from the old URL to the new one, but it's still recommended to update all references to the old name.

### 2. Update Local Repository

After renaming the repository on GitHub, update your local clone:

```bash
# Navigate to your repository directory
cd /Users/siva010928/Documents/google-chat-mcp-server-main

# Verify current remote URL
git remote -v

# Update remote URL to new repository name
git remote set-url origin https://github.com/siva010928/multi-chat-mcp-server.git

# Verify the new URL is set correctly
git remote -v

# Optional: Rename local directory to match
cd ..
mv google-chat-mcp-server-main multi-chat-mcp-server
cd multi-chat-mcp-server
```

### 3. Update Local References

We've already updated references in these files:
- README.md
- CONTRIBUTING.md
- src/providers/google_chat/CURSOR_INTEGRATION.md

You may want to check any other files that might reference the old repository name.

### 4. Commit and Push Changes

```bash
# Commit changes to renamed references
git add .
git commit -m "chore: Update references after repository rename"

# Push changes to the renamed repository
git push origin main
```

### 5. Update Dependent Projects

If you have other projects or documentation that reference this repository, make sure to update them with the new name.

### 6. Update mcp.json Configuration

Update your Cursor MCP configuration at `~/.cursor/mcp.json` to use the new directory name:

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
    }
  }
}
``` 