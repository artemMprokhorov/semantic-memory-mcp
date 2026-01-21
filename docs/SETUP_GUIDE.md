# Setup Guide

## Prerequisites

- **Docker** & **Docker Compose** (v2.0+)
- **ngrok** account (free tier works)
- **4GB+ RAM** recommended (embedding model needs ~2GB)
- **macOS / Linux** (Windows with WSL2 should work)

## Step-by-Step Installation

### 1. Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/neural-memory-mcp.git
cd neural-memory-mcp
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:

```bash
# API Authentication
NEURAL_API_KEY=your_secure_random_key_here

# Server Config  
FLASK_PORT=5000
FLASK_DEBUG=false

# Optional: Custom model (default works well)
# EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

Generate a secure API key:

```bash
openssl rand -hex 32
```

### 3. Build & Start

```bash
docker-compose up -d --build
```

First start takes 2-3 minutes (downloads embedding model).

Verify it's running:

```bash
docker logs neural-memory-mcp
```

You should see:
```
✅ Model loaded successfully on cpu
✅ Calibration saved...
🚀 Server running on port 5000
```

### 4. Setup ngrok

Install ngrok if needed:

```bash
# macOS
brew install ngrok

# Linux
snap install ngrok
```

Authenticate (one time):

```bash
ngrok config add-authtoken YOUR_NGROK_TOKEN
```

Start tunnel:

```bash
ngrok http 5000
```

Note the HTTPS URL (e.g., `https://abc123.ngrok-free.app`)

### 5. Connect to Claude.ai

1. Open [claude.ai](https://claude.ai)
2. Go to **Settings** → **Integrations** (or **Feature Preview**)
3. Find **Remote MCP Servers**
4. Click **Add**
5. Enter:
   - **Name**: Neural Memory
   - **URL**: `https://YOUR_NGROK_URL/sse?api_key=YOUR_API_KEY`
6. Save

### 6. Test Connection

In Claude, try:

> "Use neural_stats to check my memory"

Should return statistics about your (empty) memory.

## Persistent ngrok URL

Free ngrok URLs change on restart. For stable URL:

**Option A: ngrok paid plan** — Get static subdomain

**Option B: Reserved domain** (free):

```bash
ngrok http 5000 --domain=your-chosen-name.ngrok-free.app
```

## Directory Structure After Setup

```
neural-memory-mcp/
├── data/
│   ├── memory.db                    # Your notes
│   └── embedding_calibration.json   # Drift detection
├── logs/
│   └── backup.log
├── .env                             # Your config (DO NOT COMMIT)
└── ...
```

## Auto-Start on Boot

### macOS (launchd)

Create `~/Library/LaunchAgents/com.neural-memory.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.neural-memory</string>
    <key>WorkingDirectory</key>
    <string>/path/to/neural-memory-mcp</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/docker-compose</string>
        <string>up</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
```

Load it:

```bash
launchctl load ~/Library/LaunchAgents/com.neural-memory.plist
```

### Linux (systemd)

Create `/etc/systemd/system/neural-memory.service`:

```ini
[Unit]
Description=Neural Memory MCP
After=docker.service

[Service]
WorkingDirectory=/path/to/neural-memory-mcp
ExecStart=/usr/bin/docker-compose up
ExecStop=/usr/bin/docker-compose down
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable:

```bash
sudo systemctl enable neural-memory
sudo systemctl start neural-memory
```

## Next Steps

- [MCP Integration](MCP_INTEGRATION.md) — Detailed Claude.ai setup
- [API Reference](API_REFERENCE.md) — All available tools
- [Troubleshooting](TROUBLESHOOTING.md) — Common issues
