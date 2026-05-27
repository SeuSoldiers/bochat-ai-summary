from bochat_sdk.models import MessageContent, MessageResponse

from bochat_ai_summary.history import select_recent_lines


def _msg(msg_id: int, text: str | None, msg_type: str = "text") -> MessageResponse:
    content = MessageContent.text(text) if text is not None else MessageContent.custom({"x": 1})
    return MessageResponse(
        msg_id=msg_id,
        group_id="g1",
        sender_id=f"u{msg_id}",
        sender_name=f"U{msg_id}",
        sender_avatar_url=None,
        content=content,
        msg_type=msg_type,
        created_at="2026-01-01T00:00:00Z",
    )


def test_select_recent_lines_limit_30_boundary():
    messages = [_msg(i, f"text-{i}") for i in range(40)]
    lines = select_recent_lines(messages, 30)
    assert len(lines) == 30
    assert "text-10" in lines[0]
    assert "text-39" in lines[-1]


def test_select_recent_lines_empty():
    assert select_recent_lines([], 30) == []


def test_select_recent_lines_only_non_text():
    messages = [_msg(1, None, "custom"), _msg(2, None, "custom")]
    assert select_recent_lines(messages, 30) == []


def test_select_recent_lines_excludes_sum_command():
    messages = [_msg(1, "正常讨论"), _msg(2, "/sum"), _msg(3, "/sum   "), _msg(4, "继续讨论")]
    lines = select_recent_lines(messages, 30, command_prefix="/sum")
    assert len(lines) == 2
    assert "正常讨论" in lines[0]
    assert "继续讨论" in lines[1]


def test_select_recent_lines_excludes_summary_message():
    summary = "### 主题摘要\nA\n\n### 关键结论\nB\n\n### 待办项\nC"
    messages = [_msg(1, "正常讨论"), _msg(2, summary), _msg(3, "结尾讨论")]
    lines = select_recent_lines(messages, 30)
    assert len(lines) == 2
    assert "正常讨论" in lines[0]
    assert "结尾讨论" in lines[1]
