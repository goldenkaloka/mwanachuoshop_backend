#!/bin/bash

# Test runner script
set -e

echo "🧪 Running test suite..."

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest is not installed. Installing development dependencies..."
    pip install -r requirements-dev.txt
fi

# Run tests with coverage
echo "🔍 Running tests with coverage..."
pytest --cov=. --cov-report=html --cov-report=term-missing --cov-fail-under=80

# Generate coverage report
echo "📊 Coverage report generated in htmlcov/index.html"

# Run specific test categories if needed
if [ "$1" = "unit" ]; then
    echo "🧪 Running unit tests only..."
    pytest -m "unit" --cov=. --cov-report=term-missing
elif [ "$1" = "integration" ]; then
    echo "🧪 Running integration tests only..."
    pytest -m "integration" --cov=. --cov-report=term-missing
elif [ "$1" = "fast" ]; then
    echo "🧪 Running fast tests only..."
    pytest -m "not slow" --cov=. --cov-report=term-missing
else
    echo "🧪 All tests completed successfully!"
fi

echo "✅ Test suite completed!" 