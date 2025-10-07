#!/bin/bash

# Install git hooks for the WellRead project

set -e

HOOKS_DIR=".git/hooks"
SOURCE_HOOKS_DIR="hooks"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not a git repository. Please run this script from the project root."
    exit 1
fi

# Create hooks directory if it doesn't exist
mkdir -p "$HOOKS_DIR"

# Install pre-commit hook
if [ -f "$SOURCE_HOOKS_DIR/pre-commit" ]; then
    cp "$SOURCE_HOOKS_DIR/pre-commit" "$HOOKS_DIR/pre-commit"
    chmod +x "$HOOKS_DIR/pre-commit"
    echo "✅ Pre-commit hook installed successfully"
    echo "   This hook prevents committing lines containing 'NOCOMMIT'"
else
    echo "❌ Error: hooks/pre-commit not found"
    exit 1
fi

echo ""
echo "🎉 All hooks installed!"
