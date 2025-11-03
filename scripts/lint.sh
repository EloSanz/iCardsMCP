#!/bin/bash
# Quality assurance script for Python code
# Run with: ./scripts/lint.sh

set -e

echo "🔍 Running Python Code Quality Checks..."
echo "========================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to run command and check exit code
run_check() {
    local name="$1"
    local command="$2"

    echo -e "${BLUE}▶ Running ${name}...${NC}"
    if eval "$command"; then
        echo -e "${GREEN}✓ ${name} passed${NC}"
        echo
        return 0
    else
        echo -e "${RED}✗ ${name} failed${NC}"
        echo
        return 1
    fi
}

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo -e "${GREEN}✓ Virtual environment detected: $VIRTUAL_ENV${NC}"
else
    echo -e "${YELLOW}⚠ No virtual environment detected${NC}"
fi

echo

# 1. Ruff (fastest, most comprehensive)
run_check "Ruff (lint + format)" "uv run ruff check . --fix"
run_check "Ruff format" "uv run ruff format ."

# 2. MyPy (type checking)
run_check "MyPy (type checking)" "uv run mypy ."

# 3. Bandit (security)
run_check "Bandit (security)" "uv run bandit -r . -c pyproject.toml"

# 4. Tests
run_check "Tests" "uv run pytest --cov=app --cov-report=term-missing"

# 5. Import sorting (should be handled by ruff, but double-check)
run_check "Import sorting" "uv run isort --check-only --diff ."

echo -e "${GREEN}🎉 All quality checks completed!${NC}"
echo
echo "📊 Summary of tools used:"
echo "  • Ruff: Ultra-fast linter + formatter (replaces flake8, isort, black)"
echo "  • MyPy: Static type checker"
echo "  • Bandit: Security vulnerability scanner"
echo "  • Pytest: Test runner with coverage"
echo "  • Isort: Import sorter (backup)"
echo
echo "💡 Pro tip: Run 'pre-commit install' to enable automatic checks on git commit"
