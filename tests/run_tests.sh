#!/bin/bash
# 📊 Test Report Generator
# Generates comprehensive test report

set -e

echo ""
echo "🧪 Running Test Suite..."
echo ""

cd backend

# Run tests with coverage
pytest tests/ \
    -v \
    --cov=. \
    --cov-report=term-missing \
    --cov-report=html \
    --tb=short

echo ""
echo "✅ All tests passed!"
echo ""
echo "Coverage report generated in: htmlcov/index.html"
echo ""
