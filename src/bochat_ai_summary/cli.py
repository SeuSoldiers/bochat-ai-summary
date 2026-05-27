from __future__ import annotations

import argparse
import asyncio
import logging

from .app import run
from .config import load_config
from .openai_compat import load_openai_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="BoChat AI 群聊总结插件")
    parser.add_argument("--config", required=True, help="配置文件路径")
    parser.add_argument("--dry-run", action="store_true", help="只打印总结，不回发群消息")
    parser.add_argument("--once", action="store_true", help="处理一次命令后退出")
    parser.add_argument("--log-level", default="INFO", help="日志级别")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    config = load_config(args.config)
    settings = load_openai_settings()
    asyncio.run(run(config=config, settings=settings, dry_run=args.dry_run, once=args.once))


if __name__ == "__main__":
    main()
