#!/usr/bin/env python3
"""
BAE Non-Interactive CLI - For Automated Testing/Benchmarking
Purpose: Execute single BAE requests without interactive prompts
Returns: JSON output for programmatic consumption
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bae_chat import BAEConversationalCLI


def main():
    parser = argparse.ArgumentParser(description="Execute BAE requests non-interactively")
    parser.add_argument("--request", required=True, help="Natural language request to execute")
    parser.add_argument(
        "--start-servers", action="store_true", help="Start FastAPI and Streamlit servers"
    )
    parser.add_argument("--output-json", action="store_true", help="Output result as JSON")
    parser.add_argument(
        "--context-store",
        default="database/context_store.json",
        help="Path to context store JSON file",
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Suppress progress messages (only output final result)"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Configure logging
    if args.debug:
        os.environ["BAE_DEBUG"] = "1"
        logging.basicConfig(level=logging.DEBUG)
    elif args.quiet:
        logging.basicConfig(level=logging.ERROR)
    else:
        logging.basicConfig(level=logging.INFO)

    # Suppress httpx logs unless in debug mode
    httpx_logger = logging.getLogger("httpx")
    httpx_logger.setLevel(logging.DEBUG if args.debug else logging.WARNING)

    try:
        # Ensure context store directory exists
        context_store_path = Path(args.context_store)
        context_store_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize CLI with custom context store path
        cli = BAEConversationalCLI(context_store_path=str(context_store_path))

        # Check if servers should be started
        if args.start_servers:
            server_status = cli.check_servers_running()
            if not server_status["both_running"]:
                if not args.quiet:
                    print("🚀 Starting servers...")
                # Start servers will happen during first request processing

        # Process the request
        if not args.quiet:
            print(f"📝 Processing request: {args.request}")

        # Execute request through kernel
        result = cli.kernel.process_natural_language_request(
            request=args.request, start_servers=args.start_servers
        )

        # Update CLI state
        if result.get("success"):
            # Update entity list if new entities were added
            if "entities" in result:
                cli.current_system_state["entities"] = result["entities"]

            if args.start_servers and result.get("servers_started"):
                cli.current_system_state["servers_running"] = True

        # Output result
        if args.output_json:
            output = {
                "success": result.get("success", False),
                "result": result,
                "system_state": {
                    "entities": cli.current_system_state.get("entities", []),
                    "servers_running": cli.current_system_state.get("servers_running", False),
                },
            }
            print(json.dumps(output, indent=2))
        else:
            if result.get("success"):
                print(f"✅ Request completed successfully")
                if "message" in result:
                    print(f"📄 {result['message']}")
            else:
                print(f"❌ Request failed: {result.get('error', 'Unknown error')}")
                sys.exit(1)

        sys.exit(0 if result.get("success") else 1)

    except Exception as e:
        error_output = {"success": False, "error": str(e), "error_type": type(e).__name__}

        if args.output_json:
            print(json.dumps(error_output, indent=2))
        else:
            print(f"❌ Error: {e}")

        sys.exit(1)


if __name__ == "__main__":
    main()
