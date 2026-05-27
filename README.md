# bochat-ai-summary

BoChat 群聊 AI 总结插件（Python + uv）。

- 触发命令：`/sum`
- 处理范围：最近 N 条群消息（默认 30，可配）
- 上下文过滤：自动排除 `/sum` 指令消息与历史总结消息，避免“总结总结”
- 模型调用：OpenAI-Compatible `POST {base_url}/chat/completions`
- 输出：中文总结，包含主题摘要/关键结论/待办项

## 快速开始

```bash
cd community/bochat-ai-summary
cp config.example.yaml config.yaml
cp .env.example .env
# 编辑 config.yaml 和 .env
uv run bochat-ai-summary --config ./config.yaml
```

或：

```bash
./run.sh
```

## 配置

`config.yaml` 字段：

- `base_url`: BoChat 服务地址，如 `http://10.210.126.58:48080`
- `bot_token`: Bot Token
- `command_prefix`: 默认 `/sum`
- `context_window_size`: 上下文窗口大小，默认 30，范围 `1..100`
- `group_whitelist`: 群白名单（支持 `group_id` 或 `group_code`）
- `group_blacklist`: 群黑名单（支持 `group_id` 或 `group_code`）
- `blacklist_first`: 默认 `true`，冲突时黑名单优先
- `response_max_chars`: 回包最大长度，默认 1200
- `dedupe_seconds`: 同群防抖秒数，默认 30

## OpenAI 配置优先级

1. 环境变量：`OPENAI_BASE_URL` / `OPENAI_API_KEY` / `OPENAI_MODEL`
2. 回退：`~/.config/opencode/opencode.json` 的 `provider.mimo`

默认模型：`mimo-v2.5-pro`

## CLI

```bash
uv run bochat-ai-summary --config ./config.yaml
uv run bochat-ai-summary --config ./config.yaml --dry-run
uv run bochat-ai-summary --config ./config.yaml --once
```

## 测试

```bash
uv run pytest
```

## 生产真测步骤（脚本化）

1. 注册并登录新账号（生产 `10.210.126.58:48080`）。
2. 创建新 Bot，获取 `bot_token`。
3. 让 Bot 加入公开群，记录 `group_id/group_code`。
4. 群内先发送 8-12 条虚拟讨论消息（含议题、结论、待办）。
5. 启动插件：`uv run bochat-ai-summary --config ./config.yaml`。
6. 群内发送 `/sum`，确认插件回发总结。
7. 将该群加入 `group_blacklist` 后重启，再发 `/sum`，确认不触发。
8. 在本文档记录测试命令、请求 ID、回包和截图。

## 生产验证记录模板

- 日期：
- 环境地址：
- Bot ID：
- 群 ID / 群号：
- 触发命令：
- 总结回包（摘要）：
- 异常路径验证（OpenAI 不可用）：
- 截图路径：

## 故障排查

- 报错 `缺少 bot_token`：检查 `config.yaml`
- 报错 OpenAI 鉴权失败：检查 `OPENAI_API_KEY` 或 opencode `provider.mimo`
- WS 无消息：确认 Bot 已在目标群且有收消息权限
