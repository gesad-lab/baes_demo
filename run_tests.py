#!/usr/bin/env python3
"""
Test Runner for BAE (Business Autonomous Entities) Test Suite

This script provides convenient ways to run different categories of tests
for the BAE system proof of concept validation.

Progress Visibility Options:
- Default: Shows test names and basic progress
- --verbose (-v): Shows real-time output with test print statements
- --progress (-p): Explicit progress mode (same as default)
- --quiet (-q): Minimal output for CI/automation

Examples:
  python run_tests.py all --verbose          # See all test progress in detail
  python run_tests.py unit --progress        # See unit test names as they run
  python run_tests.py integration --quiet    # Minimal output for automation
"""

import argparse
import os
import shutil
import signal
import socket
import subprocess  # nosec B404
import sys
import time
from pathlib import Path

# Import centralized configuration
from config import Config

# Use centralized port configuration
REALWORLD_FASTAPI_PORT = Config.REALWORLD_FASTAPI_PORT
REALWORLD_STREAMLIT_PORT = Config.REALWORLD_STREAMLIT_PORT


def is_port_in_use(port):
    """Check if a port is currently in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def kill_process_on_port(port):
    """Kill process using the specified port."""
    try:
        # Use lsof to find process using the port
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"], capture_output=True, text=True, timeout=10
        )

        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split("\n")
            for pid in pids:
                if pid.strip():
                    try:
                        print(f"🔪 Killing process {pid} on port {port}")
                        os.kill(int(pid), signal.SIGTERM)
                        time.sleep(1)  # Give process time to terminate gracefully

                        # Check if process still exists, force kill if needed
                        try:
                            os.kill(int(pid), 0)  # Check if process exists
                            print(f"🔪 Force killing process {pid}")
                            os.kill(int(pid), signal.SIGKILL)
                        except ProcessLookupError:
                            pass  # Process already terminated

                    except (ValueError, ProcessLookupError, PermissionError) as e:
                        print(f"⚠️ Could not kill process {pid}: {e}")

    except (subprocess.TimeoutExpired, FileNotFoundError):
        # lsof not available or timeout, try alternative approach
        try:
            # Try netstat approach (more portable)
            result = subprocess.run(
                ["netstat", "-tlnp"], capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                lines = result.stdout.split("\n")
                for line in lines:
                    if f":{port} " in line and "LISTEN" in line:
                        # Extract PID from netstat output
                        parts = line.split()
                        if len(parts) > 6 and "/" in parts[6]:
                            pid = parts[6].split("/")[0]
                            try:
                                print(f"🔪 Killing process {pid} on port {port} (netstat)")
                                os.kill(int(pid), signal.SIGTERM)
                                time.sleep(1)
                            except (ValueError, ProcessLookupError, PermissionError) as e:
                                print(f"⚠️ Could not kill process {pid}: {e}")

        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(f"⚠️ Could not find process management tools to kill process on port {port}")


def cleanup_test_environment():
    """
    Clean up environment before running any tests:
    1. Kill existing servers on fixed ports
    2. Clean up .temp directory
    3. Handle permission issues gracefully
    """
    print("🧹 Cleaning up test environment...")

    # Step 1: Kill existing servers
    ports_to_clean = [REALWORLD_FASTAPI_PORT, REALWORLD_STREAMLIT_PORT]

    for port in ports_to_clean:
        if is_port_in_use(port):
            print(f"🔍 Found server running on port {port}")
            kill_process_on_port(port)

            # Verify port is now free
            time.sleep(2)
            if is_port_in_use(port):
                print(f"❌ Failed to free port {port}. Aborting test run.")
                print(f"💡 Try manually killing processes on port {port}:")
                print(f"   lsof -ti :{port} | xargs kill -9")
                sys.exit(1)
            else:
                print(f"✅ Port {port} is now free")
        else:
            print(f"✅ Port {port} is already free")

    # Step 2: Clean up .temp directory
    temp_dir = Path(__file__).parent / "tests" / ".temp"

    if temp_dir.exists():
        try:
            print(f"🗑️ Removing .temp directory: {temp_dir}")
            shutil.rmtree(temp_dir)
            print("✅ .temp directory cleaned successfully")
        except PermissionError as e:
            print(f"❌ Permission denied cleaning .temp directory: {e}")
            print("💡 Try running with appropriate permissions or manually remove:")
            print(f"   rm -rf {temp_dir}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error cleaning .temp directory: {e}")
            sys.exit(1)
    else:
        print("✅ .temp directory doesn't exist (already clean)")

    # Step 3: Recreate .temp directory
    try:
        temp_dir.mkdir(parents=True, exist_ok=True)
        print("✅ Created fresh .temp directory")
    except PermissionError as e:
        print(f"❌ Permission denied creating .temp directory: {e}")
        sys.exit(1)

    print("🎉 Test environment cleanup completed successfully!")
    print()


def run_command(cmd, verbose=False):
    """Run a command with real-time output for better visibility."""
    print(f"🚀 Running: {' '.join(cmd)}")
    print("=" * 80)

    if verbose:
        # For verbose mode, show real-time output
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,  # Line buffered
            )

            # Print output in real-time
            while True:
                output = process.stdout.readline()
                if output == "" and process.poll() is not None:
                    break
                if output:
                    print(output.strip())

            return_code = process.poll()

        except KeyboardInterrupt:
            print("\n⚠️ Test execution interrupted by user")
            process.terminate()
            return 1

    else:
        # For non-verbose mode, still capture but show some progress
        result = subprocess.run(cmd, capture_output=True, text=True)  # nosec B603

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        return_code = result.returncode

    print("=" * 80)
    return return_code


def main():
    parser = argparse.ArgumentParser(description="Run BAE system tests")
    parser.add_argument(
        "test_type",
        choices=[
            "all",
            "unit",
            "integration",
            "performance",
            "quick",
            "online",
            "e2e",
            "selenium",
            "realworld",
            "scenario1",
        ],
        help="Type of tests to run",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output with real-time progress"
    )
    parser.add_argument(
        "--progress",
        "-p",
        action="store_true",
        help="Show test progress and names (default behavior)",
    )
    parser.add_argument("--coverage", action="store_true", help="Run with coverage report")
    parser.add_argument("--parallel", "-j", type=int, help="Number of parallel workers")
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Minimal output (overrides verbose/progress)"
    )

    args = parser.parse_args()

    # Clean up environment BEFORE running any tests
    # This ensures clean state for all test runs, preventing conflicts
    cleanup_test_environment()

    # Base pytest command
    cmd = ["python", "-m", "pytest"]

    # Determine where the tests live (relative to this script)
    THIS_DIR = Path(__file__).resolve().parent
    TESTS_ROOT = THIS_DIR / "tests"

    # Handle verbosity and progress reporting
    if args.quiet:
        cmd.extend(["-q"])  # Quiet mode
    elif args.verbose:
        cmd.extend(["-v", "-s", "--tb=long"])  # -s shows print statements from tests
    elif args.progress or not args.quiet:
        cmd.extend(["-v", "--tb=short"])  # Default: show test names with short traceback

    # Add real-time progress reporting and colors
    cmd.extend(["--color=yes", "--durations=5"])  # Show 5 slowest tests

    # Add coverage
    if args.coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term"])

    # Add parallel processing
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])

    # Select test paths based on test type
    test_descriptions = {
        "all": "Running all tests (unit + integration)",
        "unit": "Running unit tests only",
        "integration": "Running integration tests only",
        "performance": "Running performance tests only",
        "online": "Running online integration tests (requires API keys)",
        "quick": "Running quick unit tests (excluding slow tests)",
        "e2e": "Running end-to-end tests",
        "selenium": "Running Selenium browser tests",
        "realworld": "Running real-world tests (excluding Selenium)",
        "scenario1": "Running Scenario 1 real-world test",
    }

    print(f"📋 Test Plan: {test_descriptions.get(args.test_type, 'Unknown test type')}")
    print()

    if args.test_type == "all":
        cmd.append(str(TESTS_ROOT))
    elif args.test_type == "unit":
        cmd.extend(["-m", "unit", str(TESTS_ROOT / "unit")])
    elif args.test_type == "integration":
        cmd.extend(["-m", "integration", str(TESTS_ROOT / "integration")])
    elif args.test_type == "performance":
        cmd.extend(["-m", "performance"])
    elif args.test_type == "online":
        # Ensure env variable is set for live tests
        os.environ["RUN_ONLINE"] = "1"
        cmd.extend(["-m", "integration_online", str(TESTS_ROOT / "integration")])
        print("🌐 Online mode enabled - will make real API calls")
    elif args.test_type == "quick":
        cmd.extend(["-m", "not slow", str(TESTS_ROOT / "unit")])
    elif args.test_type == "e2e":
        cmd.extend(["-m", "e2e", str(TESTS_ROOT / "integration")])
    elif args.test_type == "selenium":
        cmd.extend(["-m", "selenium", str(TESTS_ROOT / "integration")])
    elif args.test_type == "realworld":
        cmd.extend(["-m", "e2e and not selenium", str(TESTS_ROOT / "integration")])
    elif args.test_type == "scenario1":
        cmd.extend(["-k", "TestScenario1RealWorld", str(TESTS_ROOT / "integration")])

    print(f"🧪 Running BAE {args.test_type} tests...")

    # Show mode information
    if args.quiet:
        print("🔇 Quiet mode - minimal output")
    elif args.verbose:
        print("📝 Verbose mode - showing real-time test progress and print statements")
    else:
        print("📊 Progress mode - showing test names and progress (use --verbose for more detail)")

    # Show additional options
    if args.coverage:
        print("📈 Coverage reporting enabled")
    if args.parallel:
        print(f"⚡ Parallel execution with {args.parallel} workers")

    print("=" * 60)

    return_code = run_command(cmd, verbose=args.verbose)

    if return_code == 0:
        print("=" * 60)
        print(f"✅ All {args.test_type} tests passed!")

        # For tests that generate artifacts, remind user about inspection
        realworld_test_types = ["realworld", "scenario1", "e2e", "selenium", "all"]
        if args.test_type in realworld_test_types:
            print()
            print("🔍 INSPECTION AVAILABLE:")
            print("   • Generated files: tests/.temp/")
            print(f"   • FastAPI server: http://localhost:{REALWORLD_FASTAPI_PORT} (if running)")
            print(f"   • Streamlit UI: http://localhost:{REALWORLD_STREAMLIT_PORT} (if running)")
            print("   • Servers will remain running until next test cycle")
            print()
    else:
        print("=" * 60)
        print(f"❌ Some {args.test_type} tests failed!")

    return return_code


if __name__ == "__main__":
    sys.exit(main())
