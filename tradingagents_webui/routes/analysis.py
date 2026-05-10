"""Analysis routes - start analysis and stream progress via WebSocket."""

import asyncio
import json
import os
import uuid
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse


router = APIRouter(prefix="/api", tags=["analysis"])

_active_runs: Dict[str, dict] = {}


class AnalysisState:
    """Tracks the state of an analysis run."""

    def __init__(self, run_id: str, config: dict):
        self.run_id = run_id
        self.config = config
        self.status = "pending"
        self.progress = 0
        self.messages = []
        self.agent_states = {}
        self.final_state = None
        self.error = None
        self.started_at = datetime.now()
        self._websocket: Optional[WebSocket] = None

    def set_websocket(self, ws: WebSocket):
        self._websocket = ws

    async def send_update(self, data: dict):
        if self._websocket:
            try:
                await self._websocket.send_json(data)
            except Exception:
                pass

    async def update_status(
        self, status: str, progress: int = None, message: str = None, agent: str = None
    ):
        self.status = status
        if progress is not None:
            self.progress = progress
        if message:
            self.messages.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "agent": agent or "system",
                    "message": message,
                    "type": "info",
                }
            )
        await self.send_update(
            {
                "type": "status_update",
                "status": self.status,
                "progress": self.progress,
                "messages": self.messages[-20:],
                "agent_states": self.agent_states,
            }
        )

    async def update_agent_state(
        self, agent_name: str, state: str, message: str = None
    ):
        self.agent_states[agent_name] = {
            "state": state,
            "message": message or "",
            "updated_at": datetime.now().isoformat(),
        }
        if message:
            self.messages.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "agent": agent_name,
                    "message": message,
                    "type": "agent_message",
                }
            )
        await self.send_update(
            {
                "type": "agent_update",
                "agent_states": self.agent_states,
                "messages": self.messages[-20:],
            }
        )

    async def complete(self, final_state: dict):
        self.status = "completed"
        self.progress = 100
        self.final_state = final_state
        await self.send_update(
            {
                "type": "completed",
                "status": "completed",
                "progress": 100,
                "final_state": final_state,
            }
        )

    async def fail(self, error: str):
        self.status = "failed"
        self.error = error
        self.messages.append(
            {
                "timestamp": datetime.now().isoformat(),
                "agent": "system",
                "message": f"ERROR: {error}",
                "type": "error",
            }
        )
        await self.send_update(
            {
                "type": "error",
                "status": "failed",
                "error": error,
                "messages": self.messages[-20:],
            }
        )


def _check_api_key_configured(provider: str) -> dict:
    """Check if the required API key is configured for the given provider."""
    key_map = {
        "openai": ("OPENAI_API_KEY", False),
        "google": ("GOOGLE_API_KEY", False),
        "anthropic": ("ANTHROPIC_API_KEY", False),
        "xai": ("XAI_API_KEY", False),
        "deepseek": ("DEEPSEEK_API_KEY", False),
        "qwen": ("DASHSCOPE_API_KEY", False),
        "glm": ("ZHIPU_API_KEY", False),
        "minimax": ("MINIMAX_API_KEY", False),
        "openrouter": ("OPENROUTER_API_KEY", False),
        "azure": ("AZURE_OPENAI_API_KEY", True),
        "ollama": (None, True),
    }

    if provider.lower() not in key_map:
        return {"configured": True, "env_var": None}

    env_var, skip_check = key_map[provider.lower()]
    if skip_check or not env_var:
        return {"configured": True, "env_var": None}

    return {"configured": bool(os.environ.get(env_var)), "env_var": env_var}


async def run_analysis_bg(state: AnalysisState):
    """Background task that runs the TradingAgents analysis."""
    try:
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        from tradingagents.default_config import DEFAULT_CONFIG

        await state.update_status(
            "initializing", 5, "Setting up analysis configuration..."
        )

        config = DEFAULT_CONFIG.copy()
        config["llm_provider"] = state.config.get("provider", "openai")
        config["deep_think_llm"] = state.config.get("model", "gpt-5.4")
        config["quick_think_llm"] = state.config.get("model", "gpt-5.4-mini")
        config["max_debate_rounds"] = state.config.get("max_debate_rounds", 1)

        data_vendors = state.config.get("data_vendors", {})
        if data_vendors:
            config["data_vendors"] = data_vendors

        await state.update_status("running", 10, "Initializing agents...")

        graph = TradingAgentsGraph(debug=True, config=config)

        ticker = state.config.get("ticker", "UNKNOWN")
        date = state.config.get("date", datetime.now().strftime("%Y-%m-%d"))

        agents = [
            "Market Analyst",
            "Sentiment Analyst",
            "News Analyst",
            "Fundamentals Analyst",
            "Bull Researcher",
            "Bear Researcher",
            "Research Manager",
            "Aggressive Analyst",
            "Neutral Analyst",
            "Conservative Analyst",
            "Trader",
            "Portfolio Manager",
        ]

        for agent in agents:
            await state.update_agent_state(agent, "idle")

        await state.update_status("running", 15, f"Analyzing {ticker} for {date}...")

        for agent in agents[:4]:
            await state.update_agent_state(agent, "running", "Gathering data...")

        final_state, signal = graph.propagate(ticker, date)

        for agent in agents[:4]:
            await state.update_agent_state(agent, "completed", "Analysis complete")

        for agent in agents[4:8]:
            await state.update_agent_state(
                agent, "running", "Research debate in progress..."
            )

        for agent in agents[4:8]:
            await state.update_agent_state(agent, "completed", "Research complete")

        await state.update_agent_state(
            "Trader", "running", "Formulating trading decision..."
        )
        await state.update_agent_state("Trader", "completed", "Trading decision made")

        await state.update_agent_state(
            "Portfolio Manager", "running", "Evaluating risk..."
        )
        await state.update_agent_state(
            "Portfolio Manager", "completed", "Final decision ready"
        )

        report_content = ""
        if final_state:
            sections = [
                ("Market Report", final_state.get("market_report", "")),
                ("Sentiment Report", final_state.get("sentiment_report", "")),
                ("News Report", final_state.get("news_report", "")),
                ("Fundamentals Report", final_state.get("fundamentals_report", "")),
            ]

            for title, content in sections:
                if content:
                    report_content += f"\n## {title}\n\n{content}\n"

            if final_state.get("investment_debate_state", {}).get("judge_decision"):
                report_content += f"\n## Investment Decision\n\n{final_state['investment_debate_state']['judge_decision']}\n"

            if final_state.get("trader_investment_plan"):
                report_content += f"\n## Trader Investment Plan\n\n{final_state['trader_investment_plan']}\n"

            if final_state.get("final_trade_decision"):
                report_content += f"\n## Final Trade Decision\n\n{final_state['final_trade_decision']}\n"

        await state.update_status("saving", 95, "Saving report...")

        report_id = f"{date}_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        _save_report(
            report_id, ticker, date, report_content, {"signal": signal, "progress": 100}
        )

        state.report_path = str(_REPORTS_DIR / f"{report_id}.md")
        state.report_id = report_id

        await state.complete(final_state)

    except Exception as e:
        error_msg = f"Analysis failed: {str(e)}\n{traceback.format_exc()}"
        await state.fail(error_msg)


def _save_report(
    report_id: str, ticker: str, date: str, content: str, metadata: dict = None
):
    """Save a report to disk."""
    _REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"{report_id}.md"
    filepath = _REPORTS_DIR / filename

    header = f"""# Trading Analysis Report

**Ticker:** {ticker}
**Date:** {date}
**Report ID:** {report_id}
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

"""
    full_content = header + content

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_content)

    metadata_file = _REPORTS_DIR / f"{report_id}_meta.json"
    meta = metadata or {}
    meta.update(
        {
            "report_id": report_id,
            "ticker": ticker,
            "date": date,
            "filename": filename,
            "created_at": datetime.now().isoformat(),
        }
    )
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)


_REPORTS_DIR = Path.home() / ".tradingagents" / "reports"


@router.post("/start")
async def start_analysis(config: dict):
    """Start a new analysis run."""
    ticker = config.get("ticker")
    date = config.get("date")
    provider = config.get("provider", "openai")
    model = config.get("model", "")

    if not ticker or not date:
        raise HTTPException(status_code=400, detail="ticker and date are required")

    if not model:
        raise HTTPException(status_code=400, detail="model is required")

    api_key_status = _check_api_key_configured(provider)
    if not api_key_status["configured"]:
        raise HTTPException(
            status_code=400,
            detail=f"API key not configured for {provider}. Please set {api_key_status['env_var']} environment variable.",
        )

    run_id = str(uuid.uuid4())[:8]

    state = AnalysisState(run_id, config)
    _active_runs[run_id] = state

    asyncio.create_task(run_analysis_bg(state))

    return JSONResponse(
        {"run_id": run_id, "status": "started", "ticker": ticker, "date": date}
    )


@router.get("/status/{run_id}")
async def get_status(run_id: str):
    """Get the current status of an analysis run."""
    if run_id not in _active_runs:
        raise HTTPException(status_code=404, detail="Run not found")

    state = _active_runs[run_id]
    return JSONResponse(
        {
            "run_id": run_id,
            "status": state.status,
            "progress": state.progress,
            "messages": state.messages[-20:],
            "agent_states": state.agent_states,
            "error": state.error,
            "report_id": getattr(state, "report_id", None),
        }
    )


@router.get("/memory")
async def get_memory_entries():
    """Get entries from the trading memory log."""
    memory_path = Path.home() / ".tradingagents" / "memory" / "trading_memory.md"

    if not memory_path.exists():
        return JSONResponse({"entries": [], "pending_count": 0, "total_count": 0})

    try:
        text = memory_path.read_text(encoding="utf-8")
    except Exception:
        return JSONResponse({"entries": [], "pending_count": 0, "total_count": 0})

    entries = []
    for raw in text.split("<!-- ENTRY_END -->\n\n"):
        if not raw.strip():
            continue

        import re

        tag_match = re.search(
            r"\[(\d{4}-\d{2}-\d{2})\s*\|\s*([A-Z]+)\s*\|\s*([^\]]+)\s*\|\s*(\w+)\]", raw
        )
        if tag_match:
            date_str, ticker, rating, status = tag_match.groups()
            decision_match = re.search(
                r"DECISION:\n(.*?)(?=\nREFLECTION:|\Z)", raw, re.DOTALL
            )
            decision = decision_match.group(1).strip() if decision_match else ""

            entries.append(
                {
                    "date": date_str,
                    "ticker": ticker,
                    "rating": rating,
                    "status": status,
                    "pending": status == "pending",
                    "decision": decision,
                    "reflection": "",
                }
            )

    pending = [e for e in entries if e.get("pending")]

    return JSONResponse(
        {
            "entries": entries[-50:],
            "pending_count": len(pending),
            "total_count": len(entries),
        }
    )


@router.websocket("/ws/{run_id}")
async def websocket_endpoint(websocket: WebSocket, run_id: str):
    """WebSocket endpoint for real-time progress updates."""
    if run_id not in _active_runs:
        await websocket.close(code=404)
        return

    state = _active_runs[run_id]
    state.set_websocket(websocket)

    await websocket.accept()

    try:
        await websocket.send_json(
            {
                "type": "connected",
                "run_id": run_id,
                "status": state.status,
                "progress": state.progress,
                "agent_states": state.agent_states,
            }
        )

        while True:
            data = await websocket.receive_text()

            if data == "ping":
                await websocket.send_text("pong")
            elif data == "get_status":
                await websocket.send_json(
                    {
                        "type": "status",
                        "status": state.status,
                        "progress": state.progress,
                        "agent_states": state.agent_states,
                        "messages": state.messages[-10:],
                    }
                )

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
