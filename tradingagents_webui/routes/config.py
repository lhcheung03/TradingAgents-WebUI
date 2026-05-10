"""Config routes - provides LLM provider and model configuration."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
import os


router = APIRouter(prefix="/api/config", tags=["config"])


MODEL_OPTIONS = {
    "openai": {
        "quick": [
            ("GPT-5.4 Mini - Fast, strong coding and tool use", "gpt-5.4-mini"),
            ("GPT-5.4 Nano - Cheapest, high-volume tasks", "gpt-5.4-nano"),
            ("GPT-5.4 - Latest frontier, 1M context", "gpt-5.4"),
            ("GPT-4.1 - Smartest non-reasoning model", "gpt-4.1"),
        ],
        "deep": [
            ("GPT-5.4 - Latest frontier, 1M context", "gpt-5.4"),
            ("GPT-5.2 - Strong reasoning, cost-effective", "gpt-5.2"),
            ("GPT-5.4 Mini - Fast, strong coding and tool use", "gpt-5.4-mini"),
            ("GPT-5.4 Pro - Most capable, expensive", "gpt-5.4-pro"),
        ],
    },
    "anthropic": {
        "quick": [
            (
                "Claude Sonnet 4.6 - Best speed and intelligence balance",
                "claude-sonnet-4-6",
            ),
            ("Claude Haiku 4.5 - Fast, near-instant responses", "claude-haiku-4-5"),
        ],
        "deep": [
            (
                "Claude Opus 4.6 - Most intelligent, agents and coding",
                "claude-opus-4-6",
            ),
            ("Claude Opus 4.5 - Premium, max intelligence", "claude-opus-4-5"),
            (
                "Claude Sonnet 4.6 - Best speed and intelligence balance",
                "claude-sonnet-4-6",
            ),
        ],
    },
    "google": {
        "quick": [
            ("Gemini 3 Flash - Next-gen fast", "gemini-3-flash-preview"),
            ("Gemini 2.5 Flash - Balanced, stable", "gemini-2.5-flash"),
            ("Gemini 2.5 Flash Lite - Fast, low-cost", "gemini-2.5-flash-lite"),
        ],
        "deep": [
            (
                "Gemini 3.1 Pro - Reasoning-first, complex workflows",
                "gemini-3.1-pro-preview",
            ),
            ("Gemini 2.5 Pro - Stable pro model", "gemini-2.5-pro"),
            ("Gemini 3 Flash - Next-gen fast", "gemini-3-flash-preview"),
        ],
    },
    "xai": {
        "quick": [
            ("Grok 4.1 Fast (Non-Reasoning)", "grok-4-1-fast-non-reasoning"),
            ("Grok 4 Fast (Non-Reasoning)", "grok-4-fast-non-reasoning"),
        ],
        "deep": [
            ("Grok 4 - Flagship model", "grok-4-0709"),
            ("Grok 4.1 Fast (Reasoning)", "grok-4-1-fast-reasoning"),
        ],
    },
    "deepseek": {
        "quick": [
            ("DeepSeek V4 Flash - Latest V4 fast model", "deepseek-v4-flash"),
            ("DeepSeek V3.2", "deepseek-chat"),
        ],
        "deep": [
            ("DeepSeek V4 Pro - Latest V4 flagship model", "deepseek-v4-pro"),
            ("DeepSeek V3.2 (thinking)", "deepseek-reasoner"),
            ("DeepSeek V3.2", "deepseek-chat"),
        ],
    },
    "qwen": {
        "quick": [
            ("Qwen 3.5 Flash", "qwen3.5-flash"),
            ("Qwen Plus", "qwen-plus"),
        ],
        "deep": [
            ("Qwen 3.6 Plus", "qwen3.6-plus"),
            ("Qwen 3 Max", "qwen3-max"),
            ("Qwen 3.5 Plus", "qwen3.5-plus"),
        ],
    },
    "glm": {
        "quick": [
            ("GLM-4.7", "glm-4.7"),
            ("GLM-5", "glm-5"),
        ],
        "deep": [
            ("GLM-5.1", "glm-5.1"),
            ("GLM-5", "glm-5"),
        ],
    },
    "minimax": {
        "quick": [
            ("MiniMax-M2.7 - 60 TPS", "MiniMax-M2.7"),
            ("MiniMax-M2.5 - 60 TPS", "MiniMax-M2.5"),
            ("MiniMax-M2.1 - 60 TPS", "MiniMax-M2.1"),
            ("MiniMax-M2.7-highspeed - 100 TPS", "MiniMax-M2.7-highspeed"),
            ("MiniMax-M2.5-highspeed - 100 TPS", "MiniMax-M2.5-highspeed"),
            ("MiniMax-M2.1-highspeed - 100 TPS", "MiniMax-M2.1-highspeed"),
            ("Custom model ID", "custom"),
        ],
        "deep": [
            ("MiniMax-M2.7 - 204K context", "MiniMax-M2.7"),
            ("MiniMax-M2.5 - 204K context", "MiniMax-M2.5"),
            ("MiniMax-M2.1 - 204K context", "MiniMax-M2.1"),
            ("MiniMax-M2.7-highspeed - Fast", "MiniMax-M2.7-highspeed"),
            ("MiniMax-M2.5-highspeed - Fast", "MiniMax-M2.5-highspeed"),
            ("MiniMax-M2.1-highspeed - Fast", "MiniMax-M2.1-highspeed"),
            ("Custom model ID", "custom"),
        ],
    },
}

PROVIDERS = [
    ("OpenAI", "openai", "https://api.openai.com/v1"),
    ("Google", "google", None),
    ("Anthropic", "anthropic", "https://api.anthropic.com/"),
    ("xAI", "xai", "https://api.x.ai/v1"),
    ("DeepSeek", "deepseek", "https://api.deepseek.com"),
    ("Qwen", "qwen", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
    ("GLM", "glm", "https://open.bigmodel.cn/api/paas/v4/"),
    ("MiniMax", "minimax", "https://api.minimaxi.com/v1"),
]


@router.get("")
async def get_config():
    """Return current config including providers, models, and defaults."""
    api_keys = {
        "openai": bool(os.environ.get("OPENAI_API_KEY")),
        "google": bool(os.environ.get("GOOGLE_API_KEY")),
        "anthropic": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "xai": bool(os.environ.get("XAI_API_KEY")),
        "deepseek": bool(os.environ.get("DEEPSEEK_API_KEY")),
        "qwen": bool(os.environ.get("DASHSCOPE_API_KEY")),
        "glm": bool(os.environ.get("ZHIPU_API_KEY")),
        "minimax": bool(os.environ.get("MINIMAX_API_KEY")),
    }

    return JSONResponse(
        {
            "providers": [
                {"name": name, "key": key, "base_url": url}
                for name, key, url in PROVIDERS
            ],
            "models": MODEL_OPTIONS,
            "api_keys_configured": api_keys,
            "defaults": {
                "max_debate_rounds": 1,
                "output_language": "English",
            },
        }
    )
