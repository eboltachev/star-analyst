#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"
set +e
pytest tests/integration/test_adapter_runtime_mocks.py
rc=$?
set -e
if [ "$rc" -eq 5 ]; then
  echo "No tests collected for adapter runtime mocks; treating as soft-skip."
  exit 0
fi
exit "$rc"
