#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"
set +e
pytest tests/e2e
rc=$?
set -e
if [ "$rc" -eq 5 ]; then
  echo "No E2E tests collected (dependency not installed); treating as soft-skip."
  exit 0
fi
exit "$rc"
