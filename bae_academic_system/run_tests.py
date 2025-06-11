#!/usr/bin/env python3
"""
Test Runner for BAE (Business Autonomous Entities) Test Suite

This script provides convenient ways to run different categories of tests
for the BAE system proof of concept validation.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd):
    """Run a command and return the result"""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Run BAE system tests")
    parser.add_argument(
        "test_type", 
        choices=["all", "unit", "integration", "scenario", "scenario1", "performance", "quick"],
        help="Type of tests to run"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Verbose output"
    )
    parser.add_argument(
        "--coverage", 
        action="store_true", 
        help="Run with coverage report"
    )
    parser.add_argument(
        "--parallel", "-j", 
        type=int, 
        help="Number of parallel workers"
    )
    
    args = parser.parse_args()
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add verbosity
    if args.verbose:
        cmd.append("-v")
    
    # Add coverage
    if args.coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term"])
    
    # Add parallel processing
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])
    
    # Select test paths based on test type
    if args.test_type == "all":
        cmd.append("tests/")
    elif args.test_type == "unit":
        cmd.extend(["-m", "unit", "tests/unit/"])
    elif args.test_type == "integration":
        cmd.extend(["-m", "integration", "tests/integration/"])
    elif args.test_type == "scenario":
        cmd.extend(["-m", "scenario", "tests/scenarios/"])
    elif args.test_type == "scenario1":
        cmd.append("tests/scenarios/test_scenario1.py")
    elif args.test_type == "performance":
        cmd.extend(["-m", "performance"])
    elif args.test_type == "quick":
        cmd.extend(["-m", "not slow", "tests/unit/"])
    
    print(f"🧪 Running BAE {args.test_type} tests...")
    print("=" * 60)
    
    return_code = run_command(cmd)
    
    if return_code == 0:
        print("=" * 60)
        print(f"✅ All {args.test_type} tests passed!")
    else:
        print("=" * 60)
        print(f"❌ Some {args.test_type} tests failed!")
        
    return return_code


if __name__ == "__main__":
    sys.exit(main()) 