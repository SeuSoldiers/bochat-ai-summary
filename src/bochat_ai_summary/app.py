from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field

from bochat_sdk import BochatClient
from bochat_sdk.client import AuthKind
from bochat_sdk.models import MessageResponse

from .config import AppConfig
from .group_access import is_group_allowed
from .history import select_recent_lines
from .openai_compat import OpenAISettings, summarize_messages

LOGGER = logging.getLogger("bochat_ai_summary")


@dataclass(slots=True)
class RuntimeState:
    last_trigger_at: dict[str, float] = field(default_factory=dict)


async def resolve_group_code(client: BochatClient, group_id: str) -> str | None:
    try:
        data = await client._get_json(f"/api/v1/groups/{group_id}", AuthKind.NONE)
    except Exception:
        return None
    group_code = data.get("group_code") if isinstance(data, dict) else None
    return group_code if isinstance(group_code, str) and group_code else None


async def handle_command(
    *,
    client: BochatClient,
    config: AppConfig,
    settings: OpenAISettings,
    state: RuntimeState,
    msg: MessageResponse,
    dry_run: bool,
) -> None:
    group_id = msg.group_id
    group_code = await resolve_group_code(client, group_id)
    if not is_group_allowed(
        group_id=group_id,
        group_code=group_code,
        whitelist=config.group_whitelist or [],
        blacklist=config.group_blacklist or [],
        blacklist_first=config.blacklist_first,
    ):
        LOGGER.info("skip group by policy", extra={"group_id": group_id, "group_code": group_code})
        return

    now = time.monotonic()
    last_at = state.last_trigger_at.get(group_id)
    if last_at is not None and now - last_at < config.dedupe_seconds:
        if not dry_run:
            await client.messages().send_text(group_id, "总结任务处理中，请稍后再试。")
        return
    state.last_trigger_at[group_id] = now

    history = await client.messages().history(group_id=group_id, limit=config.context_window_size)
    lines = select_recent_lines(
        history.messages,
        config.context_window_size,
        command_prefix=config.command_prefix,
    )

    try:
        summary = await summarize_messages(settings, lines)
    except Exception as exc:
        LOGGER.exception("summary failed", extra={"group_id": group_id, "error": str(exc)})
        if not dry_run:
            await client.messages().send_text(group_id, "总结失败：AI 服务暂时不可用，请稍后重试。")
        return

    if len(summary) > config.response_max_chars:
        summary = summary[: config.response_max_chars - 3] + "..."

    if dry_run:
        print(f"[dry-run] group={group_id}\n{summary}")
        return

    await client.messages().send_text(group_id, summary)


async def run(config: AppConfig, settings: OpenAISettings, dry_run: bool = False, once: bool = False) -> None:
    state = RuntimeState()
    client = BochatClient.builder(config.base_url).build()
    client.set_bot_token(config.bot_token)

    session_handle = None
    try:
        session = await client.ws().build()
        session_handle = await session.spawn()
        dispatcher = session_handle.into_dispatcher()
        try:
            conn = await dispatcher.wait_connection_payload(timeout=10)
            LOGGER.info("ws connected", extra={"bot_id": conn.bot_id, "groups": conn.group_ids})
        except TimeoutError:
            LOGGER.warning("ws connection payload timeout, continue listening")

        queue = await dispatcher.subscribe_all_messages(buffer=128)
        ws_mode = True
        try:
            await asyncio.wait_for(queue.get(), timeout=3)
        except TimeoutError:
            ws_mode = False
            LOGGER.warning("ws message stream idle, fallback to polling mode")

        if ws_mode:
            while True:
                event = await queue.get()
                msg = event.as_message_payload()
                if msg is None:
                    continue
                text = (msg.content.as_text() or "").strip()
                if not text.startswith(config.command_prefix):
                    continue

                await handle_command(
                    client=client,
                    config=config,
                    settings=settings,
                    state=state,
                    msg=msg,
                    dry_run=dry_run,
                )

                if once:
                    return
        else:
            watch_groups = list(config.group_whitelist or [])
            if not watch_groups:
                LOGGER.warning("polling mode requires non-empty group_whitelist")
                return

            last_seen: dict[str, int] = {}
            for group_id in watch_groups:
                history = await client.messages().history(group_id=group_id, limit=1)
                last_seen[group_id] = history.messages[-1].msg_id if history.messages else 0

            while True:
                for group_id in watch_groups:
                    history = await client.messages().history(group_id=group_id, limit=50)
                    for msg in history.messages:
                        prev = last_seen.get(group_id, 0)
                        if msg.msg_id <= prev:
                            continue
                        last_seen[group_id] = msg.msg_id
                        text = (msg.content.as_text() or "").strip()
                        if not text.startswith(config.command_prefix):
                            continue
                        await handle_command(
                            client=client,
                            config=config,
                            settings=settings,
                            state=state,
                            msg=msg,
                            dry_run=dry_run,
                        )
                        if once:
                            return
                await asyncio.sleep(2)
    finally:
        if session_handle is not None:
            await session_handle.shutdown()
        await client.close()
