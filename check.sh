#!/bin/bash
set -e

echo "==> Linting (ruff)..."
python -m ruff check .

echo "==> Type checking (mypy)..."
python -m mypy --ignore-missing-imports *.py

echo "==> All checks passed!"
