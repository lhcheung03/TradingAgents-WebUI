"""Main entry point for TradingAgents WebUI."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def find_tradingagents_root() -> Path:
    """Find the TradingAgents installation root.

    Searches in order:
    1. TRADINGAGENTS_ROOT env variable
    2. ~/.tradingagents (default data location)
    3. Current working directory and parents
    4. Common installation locations
    """
    # Check environment variable
    if os.environ.get("TRADINGAGENTS_ROOT"):
        return Path(os.environ["TRADINGAGENTS_ROOT"])

    # Check home directory
    home_tradingagents = Path.home() / ".tradingagents"

    # Walk up from current directory to find tradingagents package
    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents):
        # Look for tradingagents package directory
        tg_dir = parent / "tradingagents"
        if tg_dir.exists() and (tg_dir / "graph").exists():
            return parent

        # Also look for common indicators of TradingAgents repo
        if (parent / "pyproject.toml").exists() and (parent / "tradingagents").exists():
            return parent

    # Return home location as fallback (data-only mode)
    return home_tradingagents.parent


def setup_environment():
    """Set up the environment for the webui."""
    root = find_tradingagents_root()

    # Add TradingAgents to Python path if found
    tradingagents_path = root / "tradingagents"
    if tradingagents_path.exists():
        if str(tradingagents_path) not in sys.path:
            sys.path.insert(0, str(tradingagents_path))

    # Load .env files from TradingAgents root
    env_files = [
        root / ".env",
        root / ".env.local",
    ]
    for env_file in env_files:
        if env_file.exists():
            load_dotenv(env_file, override=False)

    return root


ROOT = setup_environment()


def main():
    """Run the web server."""
    import uvicorn
    from tradingagents_webui.server import app

    print(f"TradingAgents WebUI starting...")
    print(f"TradingAgents root: {ROOT}")
    print(f"Open http://localhost:1100 in your browser")

    uvicorn.run(app, host="0.0.0.0", port=1100, log_level="info")


if __name__ == "__main__":
    main()
