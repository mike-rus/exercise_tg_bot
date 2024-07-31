#!/bin/bash

set -euo pipefail

if [[ $# -gt 0 && "$1" == "--help" ]]; then
    echo "Usage: ./python-linter-formatting.sh [--fix]"
    echo
    echo "Description:"
    echo "This script formats Python files using the Black code formatter. By default, it checks the formatting without making any changes. Use the --fix option to apply formatting changes."
    echo
    echo "Options:"
    echo "  --fix    Apply formatting changes to Python files. If omitted, only checks formatting without making any changes."
    exit 0
fi

cd "$(dirname "$0")"/..

ONLY_CHECK="--diff --check"
if [[ $# -gt 0 && "$1" == "--fix" ]]; then
    ONLY_CHECK=""
fi

git ls-files -z '*.py' | xargs --null black $ONLY_CHECK --config ./scripts/pyproject.toml