# MCP WhatsApp Setup Guide

This guide will walk you through the process of setting up the MCP WhatsApp project.

## Prerequisites

Before you begin, make sure you have the following installed:

- **Node.js** (v16+)
- **npm** (v8+)
- **Python** (v3.9+)
- **pip** (latest version)
- **Claude Desktop** (latest version)
- **Git** (optional, for cloning the repository)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/brunosantos/mcp-whatsapp.git
cd mcp-whatsapp
```

Alternatively, you can download the repository as a ZIP file and extract it.

### 2. Set Up WhatsApp Gateway

Navigate to the WhatsApp Gateway directory:

```bash
cd whatsapp-gateway
```

Install dependencies:

```bash
npm install --save-dev jest ts-jest @types/jest
```

Create a configuration file:

```bash
cp .env.example .env
```

Edit the `.env` file to configure the gateway according to your needs:

```
# Server Configuration
PORT=3000
HOST=localhost

# WhatsApp Configuration
WA_DATA_PATH=./.wwebjs_auth
WA_SESSION_NAME=whatsapp-gateway-session

# WebSocket Configuration
WS_PORT=8090
WS_PATH=/ws

# Logging
LOG_LEVEL=info
LOG_FILE_PATH=./logs/gateway.log

# Security
ALLOWED_ORIGINS=http://localhost:8080
```

Build the TypeScript code:

```bash
npm run build
```

### 3. Set Up MCP WhatsApp Server

Navigate to the MCP WhatsApp Server directory:

```bash
cd ../whatsapp-mcp-server
```

Create a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Set up environment variables (optional):

```bash
# On Linux/macOS
export MCP_HOST=0.0.0.0
export MCP_PORT=8080
export MCP_GATEWAY_HOST=localhost
export MCP_GATEWAY_PORT=8090
export MCP_CACHE_DIR=./cache

# On Windows
set MCP_HOST=0.0.0.0
set MCP_PORT=8080
set MCP_GATEWAY_HOST=localhost
set MCP_GATEWAY_PORT=8090
set MCP_CACHE_DIR=./cache
```

### 4. Configure Claude Desktop

Copy the example configuration file to your Claude Desktop configuration directory:

```bash
# Create Claude Desktop MCP directory if it doesn't exist
mkdir -p ~/.claude-desktop/mcp/
cp example_claude_desktop_config.json ~/.claude-desktop/mcp/whatsapp.json
```

On Windows, the path may be different:

```bash
copy example_claude_desktop_config.json %USERPROFILE%\.claude-desktop\mcp\whatsapp.json
```

Edit the configuration file as needed. The default configuration should work for most setups.

## Running the Services

### 1. Start the WhatsApp Gateway

Navigate to the WhatsApp Gateway directory:

```bash
cd whatsapp-gateway
```

Start the service:

```bash
npm start
```

When you run it for the first time, you'll be asked to scan a QR code. Use the WhatsApp mobile app to complete the authentication.

After around 20 days, you may need to authenticate again.

### 2. Start the MCP WhatsApp Server

Navigate to the MCP WhatsApp Server directory:

```bash
cd whatsapp-mcp-server
```

Activate the virtual environment if you created one:

```bash
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

Start the service:

```bash
python -m src.server
```

### 3. Authentication

When you start the WhatsApp Gateway for the first time, you will need to authenticate with WhatsApp:

1. Open Claude Desktop
2. Connect to the MCP WhatsApp Server (this happens automatically if you configured Claude Desktop correctly)
3. Ask Claude to show the QR code for WhatsApp authentication
4. Scan the QR code with your WhatsApp mobile app (Settings > Linked Devices > Link a Device)

Once authenticated, the WhatsApp Gateway will maintain the session, and you won't need to scan the QR code again unless you log out or the session expires.

## Troubleshooting

### Common Issues

#### WhatsApp Gateway won't start

- Check if the port is already in use by another application
- Ensure you have the correct Node.js version
- Check the logs for more details

#### MCP WhatsApp Server won't start

- Verify that all dependencies are installed
- Check if the port is already in use
- Ensure the Python version is 3.9+
- Look at the error messages in the console

#### Cannot connect to WhatsApp

- Ensure your phone has an active internet connection
- Check if WhatsApp Web is working in your browser
- Verify that the QR code is clear and scannable
- Try restarting both services

#### Claude Desktop doesn't show WhatsApp integration

- Verify that the Claude Desktop configuration file is in the correct location
- Check that the MCP WhatsApp Server is running
- Restart Claude Desktop

### Logs

Log files can be found in the following locations:

- **WhatsApp Gateway**: `whatsapp-gateway/logs/gateway.log`
- **MCP WhatsApp Server**: `whatsapp-mcp-server/logs/mcp-server.log`

Check these logs for detailed error information when troubleshooting.
