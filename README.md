# Offmind MCP Server

MCP (Model Context Protocol) server for accessing your Offmind tasks in Claude Desktop and Claude Code.

### What is this?

This is a **lightweight MCP client** that connects Claude to your Offmind tasks through a secure proxy API. It handles:
- 🔐 **Secure authentication** via Google OAuth
- 🔄 **Automatic token refresh** with Firebase ID tokens
- 📦 **Zero configuration** - no Firebase credentials needed locally

## 🚀 Quick Install

### Method 1: One-Click Install (Easiest)

1. Download [offmind-mcp.mcpb](https://github.com/vladoun/offmind-mcp/releases/latest/download/offmind-mcp.mcpb)
2. Open **Claude Desktop** → **Settings** → **Extensions** → **Advanced Settings**
3. Click **"Install Extension..."** and select the downloaded `.mcpb` file
4. Restart Claude Desktop

### Method 2: Manual Configuration

1. Open **Claude Desktop** → **Settings** → **Developer** → **Edit Config**
2. Add this configuration:

```json
{
  "mcpServers": {
    "offmind": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/vladoun/offmind-mcp",
        "offmind-mcp"
      ]
    }
  }
}
```

3. Restart Claude Desktop

## 🔐 Authentication

On first use, the MCP server will:
1. Open your browser for Google OAuth sign-in
2. Store a Firebase ID token in `~/.offmind/token.json`
3. Automatically refresh the token when it expires

No configuration needed!

## 🛠️ Available Tools

Once installed, you can ask Claude to:

- **Get tasks**
  - Today's tasks
  - All tasks
  - Incomplete tasks
  - Completed tasks
  - Tasks by date
  - Search tasks

- **Manage tasks**
  - Create new tasks with checklists
  - Toggle task completion
  - Toggle checklist items

- **Recurrent tasks**
  - View recurrent tasks
  - Create new recurrent tasks

## 🔍 Usage Examples

### In Claude Desktop or Claude Code

**List all tasks:**
```
Show me all my tasks
```

**Get today's tasks:**
```
What tasks do I have for today?
```

**Search tasks:**
```
Find tasks related to "meeting"
```

**Create a new task:**
```
Create a task "Buy groceries" for tomorrow with a checklist: milk, eggs, bread
```

**Toggle task completion:**
```
Mark task abc123 as complete
```

**Create a recurrent task:**
```
Create a daily recurrent task "Morning meditation" starting from 2025-09-01
```

## 🐛 Troubleshooting

**Authentication issues**
- Delete `~/.offmind/token.json` and try again
- Make sure the browser opens during OAuth flow
- Check that you're signing in with the correct Google account

**Server not showing in Claude Desktop**
- Verify the configuration in `claude_desktop_config.json`
- Restart Claude Desktop
- Make sure `uv` is installed: `curl -LsSf https://astral.sh/uv/install.sh | sh`

**"Command not found: uvx"**
- Install `uv` first: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Restart your terminal

**Need help?**
- Open an issue: https://github.com/vladoun/offmind-mcp/issues

## 📄 License

MIT
