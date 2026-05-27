from bochat_ai_summary.config import AppConfig


def test_context_window_size_is_primary_config():
    cfg = AppConfig(base_url="http://x", bot_token="b", context_window_size=12)
    assert cfg.context_window_size == 12
