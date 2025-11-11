#!/bin/bash
# Clean all Python cache files

echo "Cleaning Python cache files..."

# Remove all .pyc files
find . -name "*.pyc" -delete
echo "✓ Removed .pyc files"

# Remove all __pycache__ directories
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
echo "✓ Removed __pycache__ directories"

# Remove .pytest_cache if it exists
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null
echo "✓ Removed .pytest_cache directories"

echo ""
echo "Cache cleaned! Please restart the application."