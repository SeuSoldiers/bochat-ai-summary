from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(slots=True)
class AppConfig:
    base_url: str
    bot_token: str
    command_prefix: str = "/sum"
    context_window_size: int = 30
    group_whitelist: list[str] | None = None
    group_blacklist: list[str] | None = None
    blacklist_first: bool = True
    response_max_chars: int = 1200
    dedupe_seconds: int = 30

    def __post_init__(self) -> None:
        self.group_whitelist = self.group_whitelist or []
        self.group_blacklist = self.group_blacklist or []
        self.context_window_size = max(1, min(100, int(self.context_window_size)))
        self.response_max_chars = max(200, int(self.response_max_chars))
        self.dedupe_seconds = max(1, int(self.dedupe_seconds))


def load_config(path: str | Path) -> AppConfig:
    file_path = Path(path)
    raw = yaml.safe_load(file_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("config.yaml 内容必须是对象")

    if "bot_token" not in raw or not str(raw["bot_token"]).strip():
        raise ValueError("config.yaml 缺少 bot_token")
    if "base_url" not in raw or not str(raw["base_url"]).strip():
        raise ValueError("config.yaml 缺少 base_url")

    return AppConfig(**raw)
