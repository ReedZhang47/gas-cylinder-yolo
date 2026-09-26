#!/usr/bin/env bash
set -euo pipefail
MODE="${1:-}"
if [[ "$MODE" != smoke && "$MODE" != full ]]; then
  echo 'Usage: launch_detached.sh smoke|full' >&2
  exit 2
fi
mkdir -p /workspace/logs
LOG="/workspace/logs/qwen21_${MODE}_$(date -u +%Y%m%dT%H%M%SZ).log"
setsid bash /workspace/scripts/run_train.sh "$MODE" > "$LOG" 2>&1 < /dev/null &
echo "pid=$! log=$LOG"
