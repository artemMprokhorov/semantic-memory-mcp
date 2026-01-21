# MCP Integration Guide

## What is MCP?

Model Context Protocol (MCP) is Anthropic's standard for connecting AI assistants to external tools and data sources. Neural Memory implements MCP to give Claude persistent memory.

## Protocol Overview

### Transport: Server-Sent Events (SSE)

Claude.ai connects via SSE to `/sse` endpoint:

```
POST /sse?api_key=YOUR_KEY
Content-Type: application/json

{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
```

Response (SSE format):

```
data: {"jsonrpc": "2.0", "id": 1, "result": {"tools": [...]}}
```

### MCP Methods

| Method | Description |
|--------|-------------|
| `initialize` | Handshake, returns capabilities |
| `tools/list` | Returns available tools schema |
| `tools/call` | Execute a specific tool |

## Tool Definitions

### search_neural_memory

Search notes by semantic similarity.

**Input Schema:**
```json
{
  "query": "string (required)",
  "limit": "integer (default: 5, max: 20)"
}
```

**Example:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "search_neural_memory",
    "arguments": {
      "query": "machine learning projects",
      "limit": 5
    }
  }
}
```

**Response:**
```
Found 3 relevant notes (from 15 total matches):

[ID:42] [technical] (similarity: 0.8234)
Notes about PyTorch training loop optimization...

[ID:17] [project] (similarity: 0.7891)
ML project ideas for 2026...
```

### add_note

Save new note with automatic embedding.

**Input Schema:**
```json
{
  "content": "string (required)",
  "category": "string (default: 'general')"
}
```

**Categories** (suggested):
- `general` — Default
- `technical` — Code, architecture, tools
- `project` — Project-specific notes
- `learning` — Things you're studying
- `ideas` — Random thoughts

### update_note

Modify existing note (re-generates embedding).

**Input Schema:**
```json
{
  "note_id": "integer (required)",
  "content": "string (required)",
  "category": "string (optional)"
}
```

### delete_note

Remove note permanently.

**Input Schema:**
```json
{
  "note_id": "integer (required)"
}
```

### neural_stats

Get memory statistics.

**Input Schema:** (none)

**Response:**
```
Neural Memory Statistics:

Total notes: 142

By category:
  - general: 45
  - technical: 38
  - project: 32
  - learning: 27
```

## Claude.ai Setup

### Adding Remote MCP Server

1. **Open Settings**
   - Click your profile icon
   - Select "Settings"

2. **Find Integrations**
   - Look for "Feature Preview" or "Integrations"
   - Find "Remote MCP Servers"

3. **Add Server**
   - Click "Add Remote MCP Server"
   - Name: `Neural Memory` (or any name)
   - URL: `https://your-ngrok-url.ngrok-free.app/sse?api_key=YOUR_KEY`

4. **Verify**
   - Start new conversation
   - Ask Claude to check neural_stats
   - Should return your memory statistics

### Troubleshooting Connection

**"Server not responding"**
- Check ngrok is running
- Verify URL includes `/sse` path
- Check API key is correct

**"Authentication failed"**
- API key must match `.env` file
- Check for typos in URL parameter

**"Tools not showing"**
- Wait 30 seconds, refresh page
- Try removing and re-adding server

## Usage Tips

### Effective Queries

Semantic search finds conceptual matches, not just keywords:

| Query | Finds |
|-------|-------|
| "how to optimize performance" | Notes about speed, efficiency, caching |
| "project deadlines" | Notes mentioning timelines, due dates |
| "error handling patterns" | Notes about exceptions, validation |

### Organizing Notes

Use categories consistently:

```
Add note: "Flask SSE implementation requires streaming response"
Category: technical
```

Later search "web server streaming" will find it.

### Memory Maintenance

Periodically review with:
- `neural_stats` — Check category distribution
- Search broad terms — Find outdated notes
- Delete irrelevant notes — Keep signal high

## Security Considerations

- API key transmitted in URL (visible in logs)
- For production: use header-based auth
- ngrok free tier: URL changes on restart
- Self-hosted: your data, your responsibility
