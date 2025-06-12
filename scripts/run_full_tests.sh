#!/bin/bash

# Full test suite runner for pre-push hook
# Ensures complete validation before pushing to remote repository

set -e  # Exit on any error

echo "🚀 Running complete BAE test suite..."
echo "====================================="

echo "📊 Test Summary:"
echo "  • Unit Tests (required)"
echo "  • Core Tests (required)"
echo "  • Integration Tests (required)"
echo "  • End-to-end Tests (if applicable)"
echo ""

# Run complete test suite
echo "🧪 Executing full test suite..."
python run_tests.py all

echo ""
echo "✅ All tests completed successfully!"
echo "📈 BAE framework is ready for deployment!"
echo "🎯 Semantic coherence and domain entity autonomy validated!"
