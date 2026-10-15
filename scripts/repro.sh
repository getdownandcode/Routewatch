#!/usr/bin/env bash
set -euo pipefail

# CostWatch 3-run reproducibility audit script
echo "=== Starting CostWatch 3-Run Reproducibility Audit ==="

# Execute via python run.py --repro
.venv/bin/python run.py --repro

echo "=== Audit Completed Successfully ==="
