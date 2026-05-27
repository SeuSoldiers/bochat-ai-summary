from __future__ import annotations

from bochat_sdk import MessageResponse


def compact_message_line(msg: MessageResponse) -> str | None:
    sender = msg.sender_name or msg.sender_id
    text = msg.content.as_text()
    if text:
        return f"[{sender}] {text.strip()}"

    if msg.msg_type == "file":
        payload = msg.content.to_dict()
        filename = payload.get("filename") or payload.get("name")
        if isinstance(filename, str) and filename.strip():
            return f"[{sender}] [文件: {filename.strip()}]"
        return f"[{sender}] [文件消息]"

    return None


def _is_summary_message(text: str) -> bool:
    return "### 主题摘要" in text and "### 关键结论" in text and "### 待办项" in text


def select_recent_lines(
    messages: list[MessageResponse], limit: int, command_prefix: str = "/sum"
) -> list[str]:
    lines: list[str] = []
    for msg in messages:
        text = (msg.content.as_text() or "").strip()
        if text.startswith(command_prefix):
            continue
        if _is_summary_message(text):
            continue
        line = compact_message_line(msg)
        if line:
            lines.append(line)
    if limit <= 0:
        return lines
    return lines[-limit:]
