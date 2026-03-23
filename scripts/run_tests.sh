#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"

# baseline lanes
pytest tests/unit tests/integration tests/e2e

# blocking lane entrypoints for CI reuse
scripts/test_adapter_runtime_mocks.sh
scripts/test_integration_postgres.sh
scripts/test_e2e_full.sh
