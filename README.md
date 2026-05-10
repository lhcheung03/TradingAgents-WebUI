# TradingAgents WebUI

A modern web interface for the [TradingAgents](https://github.com/TauricResearch/TradingAgents) multi-agent trading framework.

## Installation

### Prerequisites

- Python 3.10+
- [TradingAgents](https://github.com/TauricResearch/TradingAgents) installed

### Quick Install

```bash
pip install tradingagents-webui
```

That's it! TradingAgents must already be installed (the WebUI uses it as a dependency).

### Install from Source

```bash
git clone https://github.com/YOUR_USERNAME/TradingAgents-WebUI.git
cd TradingAgents-WebUI
pip install -e .
```

## Usage

After installation, run:

```bash
tradingagents-web
```

Then open http://localhost:1100 in your browser.

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

The server binds to `0.0.0.0:1100` so it's accessible from other devices on your network. For mobile access via Tailscale:

1. Ensure Tailscale is running on your Mac
2. Find your Mac's Tailscale IP
3. Access from mobile: `http://<tailscale-ip>:1100`

## Architecture

- **Backend**: FastAPI + WebSocket for real-time updates
- **Frontend**: Vue 3 (CDN) + TailwindCSS
- **Reports**: Saved to `~/.tradingagents/reports/`
- **Memory**: Uses existing `~/.tradingagents/memory/trading_memory.md`

The WebUI is a thin wrapper that imports from your installed TradingAgents package — no duplicated code, just a different interface.

## Uninstall

```bash
pip uninstall tradingagents-webui
```

This removes only the WebUI package. Your TradingAgents installation remains unchanged.

## License

MIT