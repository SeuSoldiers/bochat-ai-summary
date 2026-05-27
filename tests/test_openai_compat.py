import json
import asyncio
from pathlib import Path

import httpx

from bochat_ai_summary.openai_compat import OpenAISettings, load_openai_settings, summarize_messages


class MockTransport(httpx.AsyncBaseTransport):
    def __init__(self, handler):
        self.handler = handler

    async def handle_async_request(self, request):
        return self.handler(request)


def test_load_openai_settings_from_env(monkeypatch):
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    monkeypatch.setenv("OPENAI_MODEL", "m")
    settings = load_openai_settings()
    assert settings.base_url == "https://example.com/v1"
    assert settings.api_key == "k"
    assert settings.model == "m"


def test_load_openai_settings_from_opencode(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    home = tmp_path / "home"
    conf = home / ".config" / "opencode"
    conf.mkdir(parents=True)
    (conf / "opencode.json").write_text(
        json.dumps({"provider": {"mimo": {"baseURL": "https://mimo", "apiKey": "k", "model": "x"}}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(Path, "home", lambda: home)
    settings = load_openai_settings()
    assert settings.base_url == "https://mimo"
    assert settings.api_key == "k"
    assert settings.model == "x"


def test_load_openai_settings_from_opencode_options(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    home = tmp_path / "home"
    conf = home / ".config" / "opencode"
    conf.mkdir(parents=True)
    (conf / "opencode.json").write_text(
        json.dumps(
            {
                "provider": {
                    "mimo": {"options": {"baseURL": "https://mimo-opt", "apiKey": "k2"}, "model": "y"}
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(Path, "home", lambda: home)
    settings = load_openai_settings()
    assert settings.base_url == "https://mimo-opt"
    assert settings.api_key == "k2"
    assert settings.model == "y"


def test_summarize_messages_success(monkeypatch):
    async def fake_post(self, url, json=None, headers=None):
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "主题摘要: ..."}}]},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    out = asyncio.run(summarize_messages(OpenAISettings("https://x", "k", "m"), ["[A] hello"]))
    assert "主题摘要" in out


def test_summarize_messages_http_error(monkeypatch):
    async def fake_post(self, url, json=None, headers=None):
        return httpx.Response(500, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    try:
        asyncio.run(summarize_messages(OpenAISettings("https://x", "k", "m"), ["[A] hello"]))
        assert False, "should raise"
    except httpx.HTTPStatusError:
        assert True
