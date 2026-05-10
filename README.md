# TradingAgents WebUI

A modern web interface for the [TradingAgents](https://github.com/TauricResearch/TradingAgents) multi-agent trading framework.

## Prerequisites

- Python 3.10+
- [TradingAgents](https://github.com/TauricResearch/TradingAgents) installed
- TradingAgents virtual environment activated

## Installation

### 1. Activate TradingAgents Environment

```bash
cd /path/to/TradingAgents
source .venv/bin/activate
```

Replace `/path/to/TradingAgents` with your actual TradingAgents folder path.

### 2. Install WebUI

```bash
pip install tradingagents-webui
```

TradingAgents must already be installed. The WebUI uses it as a dependency.

### Install from Source (for development)

```bash
git clone https://github.com/YOUR_USERNAME/TradingAgents-WebUI.git
cd TradingAgents-WebUI
pip install -e .
```

## Usage

### Start the WebUI

```bash
tradingagents-web
```

Then open http://localhost:1100 in your browser.

### Keep Running After Terminal Closes

To run the WebUI in the background so it keeps running after you close the terminal:

```bash
cd /path/to/TradingAgents
source .venv/bin/activate
nohup tradingagents-web > ~/.tradingagents/logs/web.log 2>&1 &
```

This runs it in the background and logs to `~/.tradingagents/logs/web.log`.

**To check if it's running:**
```bash
curl http://localhost:1100/health
```

**To view logs:**
```bash
cat ~/.tradingagents/logs/web.log
```

**To stop:**
```bash
pkill -f "tradingagents_webui"
```

**To restart (if stopped):**
```bash
cd /path/to/TradingAgents
source .venv/bin/activate
nohup tradingagents-web > ~/.tradingagents/logs/web.log 2>&1 &
```

## Configuration

The WebUI auto-detects your TradingAgents installation. Set your API keys in your TradingAgents `.env` file:

```bash
# In your TradingAgents folder, edit .env:
OPENAI_API_KEY=your_key_here
MINIMAX_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

The WebUI reads these keys automatically — no duplicate configuration needed.

## Remote Access

The server binds to `0.0.0.0:1100` so it's accessible from other devices on your network.

**For mobile access via Tailscale:**

1. Ensure Tailscale is running on your Mac
2. Find your Mac's Tailscale IP (e.g., `100.x.x.x`)
3. Access from mobile: `http://<tailscale-ip>:1100`

## Architecture

- **Backend**: FastAPI + WebSocket for real-time agent progress updates
- **Frontend**: Vue 3 (CDN) + TailwindCSS - modern dark theme UI
- **Reports**: Saved to `~/.tradingagents/reports/`
- **Memory**: Uses existing `~/.tradingagents/memory/trading_memory.md`

The WebUI is a thin wrapper that imports from your installed TradingAgents package — no duplicated code, just a different interface.

## Uninstall

```bash
source .venv/bin/activate
pip uninstall tradingagents-webui
```

This removes only the WebUI package. Your TradingAgents installation remains unchanged.

## Troubleshooting

**WebUI won't start?**
- Make sure you're in the TradingAgents venv: `source .venv/bin/activate`
- Check if port 1100 is already in use: `lsof -i :1100`

**Connection refused?**
- Verify the service is running: `curl http://localhost:1100/health`
- Check logs: `cat ~/.tradingagents/logs/web.log`

**API key not found?**
- Verify your `.env` file in TradingAgents folder has the keys
- The WebUI reads from the TradingAgents `.env`, not its own

## License

MIT