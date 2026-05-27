#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

if [[ ! -f config.yaml ]]; then
  echo "missing config.yaml, copy from config.example.yaml"
  exit 1
fi

uv run bochat-ai-summary --config ./config.yaml "$@"
