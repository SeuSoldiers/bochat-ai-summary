from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

import httpx


@dataclass(slots=True)
class OpenAISettings:
    base_url: str
    api_key: str
    model: str


def load_openai_settings() -> OpenAISettings:
    env_base_url = os.getenv("OPENAI_BASE_URL", "").strip()
    env_api_key = os.getenv("OPENAI_API_KEY", "").strip()
    env_model = os.getenv("OPENAI_MODEL", "").strip()

    if env_base_url and env_api_key:
        return OpenAISettings(
            base_url=env_base_url.rstrip("/"),
            api_key=env_api_key,
            model=env_model or "mimo-v2.5-pro",
        )

    opencode_file = Path.home() / ".config" / "opencode" / "opencode.json"
    if not opencode_file.exists():
        raise ValueError("未找到 OPENAI_* 环境变量，也未找到 ~/.config/opencode/opencode.json")

    raw = json.loads(opencode_file.read_text(encoding="utf-8"))
    provider = ((raw.get("provider") or {}).get("mimo") or {}) if isinstance(raw, dict) else {}
    if not isinstance(provider, dict):
        raise ValueError("opencode provider.mimo 配置格式错误")

    options = provider.get("options") if isinstance(provider.get("options"), dict) else {}
    base_url = str(provider.get("baseURL", "") or options.get("baseURL", "")).strip().rstrip("/")
    api_key = str(provider.get("apiKey", "") or options.get("apiKey", "")).strip()
    model = str(provider.get("model", "")).strip() or "mimo-v2.5-pro"

    if not base_url or not api_key:
        raise ValueError("opencode provider.mimo 缺少 baseURL/apiKey")

    return OpenAISettings(base_url=base_url, api_key=api_key, model=model)


async def summarize_messages(settings: OpenAISettings, lines: list[str]) -> str:
    if not lines:
        return "最近没有可总结的文本消息。"

    system_prompt = (
        "你是群聊总结助手。请用中文输出，简洁清晰。"
        "必须包含三个小节：主题摘要、关键结论、待办项。"
        "如果没有明确待办项，请写“待办项：暂无明确待办”。"
        "可补充风险点，但不要编造事实。"
    )
    user_prompt = "以下是最近群聊消息，请给出总结：\n\n" + "\n".join(lines)

    payload = {
        "model": settings.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
    }

    url = f"{settings.base_url}/chat/completions"
    headers = {"Authorization": f"Bearer {settings.api_key}"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    choices = data.get("choices") if isinstance(data, dict) else None
    if not isinstance(choices, list) or not choices:
        raise ValueError("OpenAI 响应缺少 choices")

    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise ValueError("OpenAI 响应 message.content 为空")

    return content.strip()
