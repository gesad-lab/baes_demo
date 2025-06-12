# 🧪 BAE Testing Automation Guide

## 🎯 OVERVIEW

The BAE project implements a **two-tier testing strategy**:
1. **⚡ Pre-commit**: Fast unit tests + code quality checks
2. **🚀 Pre-push**: Complete test suite including integration tests

## 🔧 SETUP

### Install Hooks
```bash
# Install pre-commit framework
pre-commit install

# Install pre-push hooks
pre-commit install --hook-type pre-push
```

## 📋 TESTING STAGES

### 🔹 PRE-COMMIT (Unit Tests)
**Triggers:** Before each `git commit`
**Duration:** ~5 seconds
**Command:** `python run_tests.py unit`
**Tests:** Unit tests (99 tests) + code quality checks

### 🔹 PRE-PUSH (Full Test Suite)
**Triggers:** Before each `git push`
**Duration:** ~5 minutes
**Command:** `python run_tests.py all`
**Tests:** Complete suite (126 tests) including integration

## 🛠️ MANUAL COMMANDS

```bash
# Run specific test categories
python run_tests.py unit      # Unit tests only
python run_tests.py core      # Core functionality
python run_tests.py all       # Complete suite

# Run pre-commit checks manually
pre-commit run --all-files

# Skip hooks (emergency only)
git commit --no-verify -m "Emergency commit"
git push --no-verify
```

## 📊 CURRENT STATUS
- ✅ Unit Tests: 99/99 passing
- ✅ Core Tests: 4/4 passing
- ✅ Integration Tests: 21/21 passing
- ✅ Total: 126/128 tests passing (2 skipped)

## 🎯 KEY BENEFITS

### Simplified Architecture
- **Single test runner**: `run_tests.py` handles all test categories
- **No redundant scripts**: Direct integration with pre-commit framework
- **Clear messaging**: Built-in output from the main test runner

### Domain Entity Validation
- **Semantic coherence**: BAE domain entity autonomy validated at every checkpoint
- **Business vocabulary preservation**: Ensures alignment between business concepts and technical artifacts
- **Runtime evolution testing**: Validates BAE adaptation capabilities

This ensures semantic coherence and domain entity autonomy validation at every checkpoint using a clean, unified testing interface.
