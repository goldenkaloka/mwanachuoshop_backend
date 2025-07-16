#!/bin/bash

# Code formatting and linting script
set -e

echo "🔧 Formatting and linting code..."

# Check if required tools are installed
if ! command -v black &> /dev/null; then
    echo "❌ Black is not installed. Installing development dependencies..."
    pip install -r requirements-dev.txt
fi

if ! command -v flake8 &> /dev/null; then
    echo "❌ Flake8 is not installed. Installing development dependencies..."
    pip install -r requirements-dev.txt
fi

if ! command -v isort &> /dev/null; then
    echo "❌ isort is not installed. Installing development dependencies..."
    pip install -r requirements-dev.txt
fi

# Format code with black
echo "🎨 Formatting code with Black..."
black .

# Sort imports with isort
echo "📦 Sorting imports with isort..."
isort .

# Lint code with flake8
echo "🔍 Linting code with flake8..."
flake8 .

# Security check with bandit
echo "🔒 Running security checks with bandit..."
bandit -r . -f json -o bandit-report.json || true

echo "✅ Code formatting and linting complete!"
echo "📊 Security report saved to bandit-report.json" 