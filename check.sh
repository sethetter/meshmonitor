#!/bin/bash
set -e

echo "==> Linting (ruff)..."
./venv/bin/python -m ruff check .

echo "==> Type checking (mypy)..."
./venv/bin/python -m mypy --ignore-missing-imports -- app/*.py

echo "==> Running tests (mypy)..."
./venv/bin/python -m unittest discover

echo "==> All checks passed!"
