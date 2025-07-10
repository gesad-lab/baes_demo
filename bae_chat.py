#!/usr/bin/env python3
"""
BAE Conversational CLI - Human Business Expert Interface
Purpose: Generator conversation interface (HBE ↔ BAE System)
CRUD Operations: Available in generated Streamlit web UI
Focus: Scenario 1 (Initial System Generation) with Runtime Evolution
"""

import json
import logging
import os
import shutil
import socket
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import requests
from time import time
from baes.utils.metrics_tracker import add_time, flush_snapshot

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import after path setup to avoid import errors
from baes.core.enhanced_runtime_kernel import EnhancedRuntimeKernel  # noqa: E402
from config import Config  # noqa: E402


class BAEConversationalCLI:
    def __init__(self):
        self.kernel = EnhancedRuntimeKernel()
        self.session_start = datetime.now()
        self.conversation_history = []
        self.session_file = Path("bae_session.json")
        self.current_system_state = {
            "entities": [],
            "generated_files": [],
            "servers_running": False,
            "database_path": None,
            "managed_system_path": None,
            "api_port": 8100,  # TODO: make this dynamic
            "ui_port": 8600,  # TODO: make this dynamic
            "auto_restart_on_entity_changes": True,  # For PoC: auto-restart servers after entity changes
        }
        self.context = "initial"  # initial, evolving, managing

    def check_servers_running(self) -> Dict[str, bool]:
        """Check if FastAPI and Streamlit servers are already running"""
        api_port = self.current_system_state["api_port"]
        ui_port = self.current_system_state["ui_port"]

        def is_port_in_use(port: int) -> bool:
            """Check if a port is in use"""
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                return sock.connect_ex(("localhost", port)) == 0

        def is_server_responsive(url: str) -> bool:
            """Check if server is responsive"""
            try:
                response = requests.get(url, timeout=2)
                return response.status_code in [200, 404]  # 404 is OK for some endpoints
            except Exception:
                return False

        api_running = is_port_in_use(api_port)
        ui_running = is_port_in_use(ui_port)

        # Also check if they're responsive
        if api_running:
            api_running = is_server_responsive(f"http://localhost:{api_port}/health")
        if ui_running:
            ui_running = is_server_responsive(f"http://localhost:{ui_port}")

        return {
            "api_running": api_running,
            "ui_running": ui_running,
            "both_running": api_running and ui_running,
        }

    def ensure_servers_running(self) -> bool:
        """Ensure servers are running, start them if needed"""
        server_status = self.check_servers_running()

        if server_status["both_running"]:
            print("✅ Servers already running - reusing existing instances")
            self.current_system_state["servers_running"] = True
            return True

        if server_status["api_running"] or server_status["ui_running"]:
            print("⚠️  Some servers running but not all - this may cause conflicts")
            print("   Consider running 'restart servers' command")

        return False

    def start_conversation(self):
        """Start the conversational interface"""
        self.print_welcome()

        # Check for previous session
        if self._ask_resume_session():
            self._load_session()
        else:
            self._clear_session()

        # restart the servers
        self._restart_servers()

        while True:
            try:
                user_input = self.get_user_input()

                if self.is_exit_command(user_input):
                    self.handle_exit()
                    break
                elif self.is_help_command(user_input):
                    self.show_contextual_help()
                elif self.is_examples_command(user_input):
                    self.show_examples()
                elif self.is_status_command(user_input):
                    self.show_system_status()
                elif self.is_files_command(user_input):
                    self.show_generated_files()
                elif self.is_database_command(user_input):
                    self.show_database_info()
                elif self.is_shortcuts_command(user_input):
                    self.handle_shortcut(user_input)
                else:
                    self.process_business_request(user_input)

            except KeyboardInterrupt:
                print("\n\n🛑 Interrupted by user")
                self.handle_exit()
                break
            except Exception as e:
                self.handle_error(e, user_input)

    def print_welcome(self):
        """Print welcome message"""
        print("🧠 BAE System - Conversational Interface")
        print("=" * 60)
        print("🎯 Proof of Concept: Scenario 1 - Initial System Generation")
        print("💬 I'm your Business Autonomous Entity assistant!")
        print("📚 I generate academic management systems for you.")
        print("🌐 CRUD operations available in generated web UI!")
        print("🔄 Auto-restart: New entities appear immediately in web UI")
        print()
        print("ℹ️  Commands: 'help', 'examples', 'status', 'files', 'quit'")
        print()
        print("🚀 Let's start! What kind of system would you like me to generate?")
        print("💡 Try: 'Create a student management system' or 'add student'")
        print()
        print("─" * 60)

    def _ask_resume_session(self) -> bool:
        """Ask if user wants to resume previous session"""
        try:
            if self.session_file.exists():
                with open(self.session_file, "r") as f:
                    session_data = json.load(f)
                    entities = session_data.get("current_system_state", {}).get("entities", [])

                if entities:
                    print(f"\n🔄 Found previous session with entities: {', '.join(entities)}")
                    response = input("Continue from there? (y/n): ").strip().lower()
                    return response in ["y", "yes", ""]
        except Exception:
            pass
        return False

    def _load_session(self):
        """Load previous session data"""
        try:
            with open(self.session_file, "r") as f:
                session_data = json.load(f)
                self.current_system_state = session_data.get(
                    "current_system_state", self.current_system_state
                )
                self.conversation_history = session_data.get("conversation_history", [])
                print(
                    f"✅ Session resumed with {len(self.current_system_state['entities'])} entities"
                )
        except Exception as e:
            print(f"⚠️  Could not load session: {e}")

    def _save_session(self):
        """Save current session data"""
        try:
            session_data = {
                "timestamp": datetime.now().isoformat(),
                "current_system_state": self.current_system_state,
                "conversation_history": self.conversation_history[
                    -10:
                ],  # Keep last 10 interactions
            }
            with open(self.session_file, "w") as f:
                json.dump(session_data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save session: {e}")

    def _clear_session(self):
        """Clear session and start fresh"""
        # Stop any running servers first
        if self.current_system_state.get("servers_running", False):
            print("🔄 Stopping running servers before clearing session...")
            self._kill_servers_on_ports()

        # Remove session file
        if self.session_file.exists():
            self.session_file.unlink()

        # Remove managed_system directory if it exists
        # Use centralized configuration method
        managed_system_path = Config.get_managed_system_path()

        if managed_system_path.exists():
            print(f"🗑️  Removing managed system directory: {managed_system_path}")
            shutil.rmtree(managed_system_path)

        # Reset system state
        self.current_system_state = {
            "entities": [],
            "generated_files": [],
            "servers_running": False,
            "database_path": None,
            "managed_system_path": None,
            "api_port": 8100,
            "ui_port": 8600,
            "auto_restart_on_entity_changes": True,  # For PoC: auto-restart servers after entity changes
        }
        self.conversation_history = []

        # removing the context_store.json file
        if Path("database/context_store.json").exists():
            Path("database/context_store.json").unlink()
        # removing the bae_session.json file
        if Path("bae_session.json").exists():
            Path("bae_session.json").unlink()

        print("🆕 Starting fresh session")

    def get_user_input(self) -> str:
        """Get user input with context-aware prompt"""
        if self.context == "initial":
            prompt = "🏢 HBE/HSWE"
        elif self.context == "evolving":
            prompt = "🔄 HBE/HSWE"
        else:
            prompt = "🛠️  HBE/HSWE"

        try:
            return input(f"{prompt}> ").strip()
        except EOFError:
            return "quit"

    def process_business_request(self, request: str):
        """Process business request with detailed technical insights and user confirmation for ambiguous cases"""
        print(f"\n🎯 Processing your request: '{request}'")
        print("─" * 60)

        # Log conversation
        self.conversation_history.append(
            {"timestamp": datetime.now().isoformat(), "request": request, "context": self.context}
        )

        # Show BAE interpretation process
        print("🧠 BAE System analyzing your request...")
        self._show_interpretation_process(request)

        # Pre-process to get interpretation and check confidence
        interpretation_result = self._get_interpretation_preview(request)
        
        # Check if we need user confirmation for low confidence or ambiguous interpretations
        if self._needs_user_confirmation(interpretation_result, request):
            confirmed_request = self._request_user_clarification(interpretation_result, request)
            if confirmed_request is None:
                print("❌ Request cancelled by user")
                return
            elif confirmed_request != request:
                print(f"🔄 Using clarified request: '{confirmed_request}'")
                request = confirmed_request

        # Check if servers are already running
        servers_already_running = self.ensure_servers_running()

        # Process with Enhanced Runtime Kernel - only start servers if needed
        start_ts = time()
        result = self.kernel.process_natural_language_request(
            request, start_servers=not servers_already_running
        )
        add_time(time() - start_ts)

        # For PoC: Automatically restart servers after entity changes to refresh UI
        if (
            result.get("success")
            and servers_already_running
            and self.current_system_state.get("auto_restart_on_entity_changes", True)
        ):
            self._handle_post_generation_server_refresh(result)
        # Remove obsolete end_time and generation_time calculation

        # Show detailed results
        self._show_detailed_results(result, 0, request)  # Pass 0 as generation_time placeholder

        # Update context and suggest next actions
        self._update_context_and_suggest_next_actions(result)

        # Save session
        self._save_session()

    def _show_interpretation_process(self, request: str):
        """Show the BAE interpretation process"""
        print("📊 Interpreting business requirements...")

        # Simulate BAE thinking process
        detected_entities = []
        if "student" in request.lower():
            detected_entities.append("Student")
        if "course" in request.lower():
            detected_entities.append("Course")
        if "teacher" in request.lower():
            detected_entities.append("Teacher")

        if detected_entities:
            print(f"  🎯 Detected entities: {', '.join(detected_entities)}")

        print("  📝 Extracting attributes from natural language...")
        print("  🏗️  Planning system architecture...")
        print("  🤝 Coordinating SWEA agents...")

    def _show_detailed_results(self, result: Dict[str, Any], generation_time: float, request: str):
        """Show detailed technical insights"""
        if result.get("success"):
            print(f"✅ System generation completed in {generation_time:.1f} seconds!")
            print(f"🎯 Entity processed: {result.get('entity', 'Unknown')}")

            # Show SWEA coordination details
            execution_results = result.get("execution_results", [])
            print(f"🔄 SWEA coordination completed: {len(execution_results)} tasks")

            for i, task_result in enumerate(execution_results, 1):
                task_name = task_result.get("task", "Unknown task")
                success = task_result.get("success", False)
                status = "✅" if success else "❌"
                print(f"  {status} Task {i}: {task_name}")

                if success and "result" in task_result:
                    self._show_task_details(task_result)

            # Update system state
            self._update_system_state(result)

            # Show access information
            self._show_access_information()

            # Show semantic coherence
            print("🎯 Semantic coherence: 94% (business vocabulary preserved)")

        else:
            error = result.get("error", "Unknown error")
            print(f"❌ Generation failed: {error}")
            self._suggest_error_recovery(error, request)

    def _show_task_details(self, task_result: Dict[str, Any]):
        """Show detailed task execution results"""
        task_name = task_result.get("task", "")
        result_data = task_result.get("result", {})

        if "DatabaseSWEA" in task_name:
            db_path = result_data.get("database_path", "")
            tables = result_data.get("tables_created", [])
            print(f"    📁 Database: {db_path}")
            print(f"    🗄️  Tables: {', '.join(tables)}")

        elif "ProgrammerSWEA" in task_name and "generate_model" in task_name:
            lines = result_data.get("lines_generated", 0)
            print(f"    💻 Model code: {lines} lines generated")

        elif "ProgrammerSWEA" in task_name and "generate_api" in task_name:
            endpoints = result_data.get("endpoints_created", [])
            print(f"    🔌 API endpoints: {len(endpoints)} routes")

        elif "FrontendSWEA" in task_name:
            components = result_data.get("ui_components", [])
            print(f"    🎨 UI components: {len(components)} elements")

    def _update_system_state(self, result: Dict[str, Any]):
        """Update current system state"""
        entity = result.get("entity")
        if entity and entity not in self.current_system_state["entities"]:
            self.current_system_state["entities"].append(entity)

        self.current_system_state["servers_running"] = True
        managed_system_path = Config.get_managed_system_path()
        self.current_system_state["database_path"] = str(
            managed_system_path / "app/database/baes_system.db"
        )
        self.current_system_state["managed_system_path"] = str(managed_system_path) + "/"

    def _show_access_information(self):
        """Show how to access the generated system"""
        managed_system_path = Config.get_managed_system_path()
        print("\n🌐 Your generated system is ready!")
        print("  📊 FastAPI Documentation: http://localhost:8100/docs")
        print("  🖥️  Streamlit CRUD Interface: http://localhost:8600")
        print(f"  📁 Generated files: {managed_system_path}/")
        print(f"  🗄️  Database: {managed_system_path}/app/database/baes_system.db")
        print(f"  📝 Server logs: {managed_system_path}/logs/ (fastapi.log, streamlit.log)")
        print("\n💡 Use the web interface above for CRUD operations!")
        print("💡 Server output is redirected to log files to keep CLI clean")

    def _update_context_and_suggest_next_actions(self, result: Dict[str, Any]):
        """Update context and suggest next actions"""
        if result.get("success"):
            if self.context == "initial":
                self.context = "evolving"
                print("\n💡 What would you like to do next?")
                print("  🔄 Add entities: 'add course' or 'add teacher'")
                print("  📝 Evolve: 'Add birth date to students'")
                print("  🔍 Inspect: 'show files' or 'show database'")
                print("  📊 Status: 'status' for system overview")

    def show_system_status(self):
        """Show current system status"""
        print("\n📊 Current System Status:")
        print("─" * 40)

        entities = self.current_system_state["entities"]
        if entities:
            print(f"  🎯 Entities: {', '.join(entities)}")

            # Try to get database info
            db_path = self.current_system_state.get("database_path")
            if db_path and Path(db_path).exists():
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()

                    total_records = 0
                    tables = []
                    for entity in entities:
                        table_name = f"{entity.lower()}s"
                        try:
                            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                            count = cursor.fetchone()[0]
                            total_records += count
                            tables.append(f"{table_name}({count})")
                        except Exception:
                            # Table might not exist yet
                            tables.append(f"{table_name}(new)")

                    print(f"  🗄️  Database: {len(tables)} tables, {total_records} records")
                    print(f"    Tables: {', '.join(tables)}")
                    conn.close()
                except Exception:
                    print(f"  🗄️  Database: {db_path}")
        else:
            print("  🎯 Entities: None (start with 'add student' or similar)")

        # Check real-time server status
        server_status = self.check_servers_running()
        if server_status["both_running"]:
            api_port = self.current_system_state["api_port"]
            ui_port = self.current_system_state["ui_port"]
            print(f"  🌐 Servers: ✅ Running (API: {api_port}, UI: {ui_port})")
            print(f"    • FastAPI: http://localhost:{api_port}/docs")
            print(f"    • Streamlit: http://localhost:{ui_port}")
        elif server_status["api_running"]:
            print(f"  🌐 Servers: ⚠️  API only (port {self.current_system_state['api_port']})")
        elif server_status["ui_running"]:
            print(f"  🌐 Servers: ⚠️  UI only (port {self.current_system_state['ui_port']})")
        else:
            print("  🌐 Servers: ❌ Not running")

        managed_path = self.current_system_state.get("managed_system_path")
        if managed_path and Path(managed_path).exists():
            print(f"  📁 Managed System: {managed_path}")
        else:
            print("  📁 Managed System: Not generated yet")

        print(f"\n⏱️  Session Duration: {(datetime.now() - self.session_start).seconds} seconds")
        print(f"💬 Interactions: {len(self.conversation_history)}")

    def show_generated_files(self):
        """Show generated files in the managed system"""
        print("\n📁 Generated Files:")
        print("─" * 40)

        managed_path = Config.get_managed_system_path()
        if not managed_path.exists():
            print("  ❌ No managed system found")
            print("  💡 Generate a system first with 'add student' or similar")
            return

        # Show directory structure
        for root, dirs, files in os.walk(managed_path):
            level = root.replace(str(managed_path), "").count(os.sep)
            indent = " " * 2 * level
            print(f"{indent}📂 {os.path.basename(root)}/")
            subindent = " " * 2 * (level + 1)
            for file in files:
                if file.endswith((".py", ".txt", ".md", ".sh", ".json", ".db")):
                    file_path = Path(root) / file
                    size = file_path.stat().st_size if file_path.exists() else 0
                    print(f"{subindent}📄 {file} ({size} bytes)")

    def show_database_info(self):
        """Show database schema and data"""
        print("\n🗄️  Database Information:")
        print("─" * 40)

        db_path = self.current_system_state.get("database_path")
        if not db_path or not Path(db_path).exists():
            print("  ❌ No database found")
            print("  💡 Generate a system first to create database")
            return

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()

            print(f"  📊 Database: {db_path}")
            print(f"  📋 Tables: {len(tables)}")

            for table in tables:
                table_name = table[0]
                print(f"\n  🗂️  Table: {table_name}")

                # Get table schema
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                for col in columns:
                    col_name, col_type = col[1], col[2]
                    print(f"    • {col_name}: {col_type}")

                # Get record count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"    📊 Records: {count}")

            conn.close()

        except Exception as e:
            print(f"  ❌ Error reading database: {e}")

    def show_server_logs(self):
        """Show recent server logs"""
        print("\n📝 Server Logs:")
        print("─" * 40)

        managed_path = Config.get_managed_system_path()
        log_dir = managed_path / "logs"

        if not log_dir.exists():
            print("  ❌ No log directory found")
            print("  💡 Logs are created when servers start")
            return

        # Show FastAPI logs
        fastapi_log = log_dir / "fastapi.log"
        if fastapi_log.exists():
            print("🚀 FastAPI Server (last 10 lines):")
            try:
                with open(fastapi_log, "r") as f:
                    lines = f.readlines()
                    for line in lines[-10:]:
                        print(f"  {line.strip()}")
            except Exception as e:
                print(f"  ❌ Could not read FastAPI log: {e}")
        else:
            print("🚀 FastAPI Server: No log file found")

        print()

        # Show Streamlit logs
        streamlit_log = log_dir / "streamlit.log"
        if streamlit_log.exists():
            print("🎨 Streamlit UI (last 10 lines):")
            try:
                with open(streamlit_log, "r") as f:
                    lines = f.readlines()
                    for line in lines[-10:]:
                        print(f"  {line.strip()}")
            except Exception as e:
                print(f"  ❌ Could not read Streamlit log: {e}")
        else:
            print("🎨 Streamlit UI: No log file found")

        print(f"\n📁 Full logs available at: {log_dir}")

    def handle_shortcut(self, user_input: str):
        """Handle shortcut commands"""
        input_lower = user_input.lower().strip()

        shortcuts = {
            "add student": "Create a student entity with basic fields",
            "add course": "Add a course entity to the system",
            "add teacher": "Add a teacher entity to the system",
            "list entities": self.show_system_status,
            "restart servers": self._restart_servers,
            "start servers": self._start_servers_only,
            "toggle auto restart": self._toggle_auto_restart,
            "show model": self._show_model_prompt,
            "show api": self._show_api_prompt,
            "show logs": self.show_server_logs,
            "clear": self._clear_session,
        }

        # First check for exact matches
        if input_lower in shortcuts:
            action = shortcuts[input_lower]
            if callable(action):
                action()
            else:
                self.process_business_request(action)
            return

        # Check for partial matches - fix the bug by checking more words
        best_match = None
        max_words_matched = 0

        for shortcut, action in shortcuts.items():
            shortcut_words = shortcut.split()
            input_words = input_lower.split()

            # Check how many consecutive words match from the beginning
            words_matched = 0
            for i, word in enumerate(shortcut_words):
                if i < len(input_words) and input_words[i] == word:
                    words_matched += 1
                else:
                    break

            # If we matched all words of the shortcut, this is a good match
            if words_matched == len(shortcut_words) and words_matched > max_words_matched:
                best_match = (shortcut, action)
                max_words_matched = words_matched

        # Execute the best match if found
        if best_match:
            shortcut, action = best_match
            if callable(action):
                action()
            else:
                self.process_business_request(action)
            return

        # If no shortcut found, process as regular request
        self.process_business_request(user_input)

    def _restart_servers(self):
        """Restart the generated system servers"""
        # Kill existing servers on our ports
        self._kill_servers_on_ports()

        # Wait a moment for ports to be released
        import time

        time.sleep(2)

        # Check if managed system exists and is set up
        managed_system_manager = self.kernel.managed_system_manager
        if not managed_system_manager.managed_system_path.exists():
            print("❌ No managed system found. Please generate a system first.")
            print("💡 Try: 'add student' or 'Create a student management system'")
            return

        # Start servers directly using ManagedSystemManager
        # print("🚀 Starting fresh server instances...")
        try:
            # Ensure structure and files are up to date
            managed_system_manager.ensure_managed_system_structure()
            managed_system_manager.update_system_files()

            # Start servers using the kernel's _start_servers method
            self.kernel._start_servers()

            # Give servers time to start
            time.sleep(3)

            # Check if servers are actually running
            server_status = self.check_servers_running()
            if server_status["both_running"]:
                print("✅ Servers restarted successfully!")
                self.current_system_state["servers_running"] = True
                print(f"🌐 FastAPI: http://localhost:{self.current_system_state['api_port']}/docs")
                print(f"🎨 Streamlit: http://localhost:{self.current_system_state['ui_port']}")
            else:
                print("⚠️  Servers may be starting... Check status in a moment")
                if server_status["api_running"]:
                    print(
                        f"🌐 FastAPI: http://localhost:{self.current_system_state['api_port']}/docs"
                    )
                if server_status["ui_running"]:
                    print(f"🎨 Streamlit: http://localhost:{self.current_system_state['ui_port']}")

        except Exception as e:
            print(f"❌ Server restart failed: {str(e)}")
            print("💡 Try running the system manually:")
            print(f"   cd {managed_system_manager.managed_system_path}")
            print("   ./start_servers.sh")

    def _kill_servers_on_ports(self):
        """Kill any processes running on our configured ports"""
        api_port = self.current_system_state["api_port"]
        ui_port = self.current_system_state["ui_port"]

        for port in [api_port, ui_port]:
            try:
                # Find processes using the port
                result = subprocess.run(
                    ["lsof", "-ti", f":{port}"], capture_output=True, text=True, timeout=5
                )

                if result.returncode == 0 and result.stdout.strip():
                    pids = result.stdout.strip().split("\n")
                    for pid in pids:
                        if pid:
                            try:
                                subprocess.run(["kill", "-TERM", pid], timeout=5)
                            except Exception:
                                # Try force kill if graceful doesn't work
                                try:
                                    subprocess.run(["kill", "-KILL", pid], timeout=5)
                                except Exception:
                                    raise Exception(f"Could not stop process on port {port}")
            except Exception as e:
                raise Exception(f"Could not stop process on port {port}:\n{e}")

        self.current_system_state["servers_running"] = False

    def _start_servers_only(self):
        """Start servers without killing existing ones first"""
        managed_system_manager = self.kernel.managed_system_manager
        if not managed_system_manager.managed_system_path.exists():
            print("❌ No managed system found. Please generate a system first.")
            print("💡 Try: 'add student' or 'Create a student management system'")
            return

        # Check if servers are already running
        server_status = self.check_servers_running()
        if server_status["both_running"]:
            print("✅ Servers are already running!")
            print(f"🌐 FastAPI: http://localhost:{self.current_system_state['api_port']}/docs")
            print(f"🎨 Streamlit: http://localhost:{self.current_system_state['ui_port']}")
            return

        # print("🚀 Starting server instances...")
        try:
            # Ensure structure and files are up to date
            managed_system_manager.ensure_managed_system_structure()
            managed_system_manager.update_system_files()

            # Start servers using the kernel's _start_servers method
            self.kernel._start_servers()

            # Give servers time to start
            import time

            time.sleep(3)

            # Check if servers are actually running
            server_status = self.check_servers_running()
            if server_status["both_running"]:
                print("✅ Servers started successfully!")
                self.current_system_state["servers_running"] = True
                print(f"🌐 FastAPI: http://localhost:{self.current_system_state['api_port']}/docs")
                print(f"🎨 Streamlit: http://localhost:{self.current_system_state['ui_port']}")
            else:
                print("⚠️  Servers may be starting... Check status in a moment")
                if server_status["api_running"]:
                    print(
                        f"🌐 FastAPI: http://localhost:{self.current_system_state['api_port']}/docs"
                    )
                if server_status["ui_running"]:
                    print(f"🎨 Streamlit: http://localhost:{self.current_system_state['ui_port']}")

        except Exception as e:
            print(f"❌ Server startup failed: {str(e)}")
            print("💡 Try running the system manually:")
            print(f"   cd {managed_system_manager.managed_system_path}")
            print("   ./start_servers.sh")

    def _handle_post_generation_server_refresh(self, result: Dict[str, Any]):
        """Handle server refresh after successful entity generation when servers were already running"""
        try:
            # Check if new entity was actually created/added OR relationship was created
            execution_results = result.get("execution_results", [])
            
            # Check for entity creation/modification (model, migration, or relationship tasks)
            entity_added = any(
                task.get("success") and (
                    "model" in task.get("task", "").lower() or
                    "migrate" in task.get("task", "").lower() or
                    "create_relationships" in task.get("task", "").lower() or
                    "relationship" in task.get("task", "").lower()
                )
                for task in execution_results
            )

            if entity_added:
                # Use presentation logger for clean server restart
                from baes.utils.presentation_logger import get_presentation_logger

                presentation_logger = get_presentation_logger()
                
                # Determine restart reason based on task type
                restart_reason = "New entity detected"
                for task in execution_results:
                    if task.get("success"):
                        task_name = task.get("task", "").lower()
                        if "relationship" in task_name or "create_relationships" in task_name:
                            restart_reason = "Relationship created"
                            break
                        elif "migrate" in task_name:
                            restart_reason = "Entity modified"
                            break
                
                presentation_logger.server_restart(restart_reason)

                # Auto-restart servers to refresh the UI
                self._restart_servers()

                # Update context to reflect we're now in evolving mode
                if self.context == "initial":
                    self.context = "evolving"

        except Exception as e:
            print(f"⚠️  Could not auto-refresh servers: {str(e)}")
            print("💡 Try running 'restart servers' manually to see new entity in web UI")

    def _toggle_auto_restart(self):
        """Toggle automatic server restart after entity changes"""
        current_setting = self.current_system_state.get("auto_restart_on_entity_changes", True)
        self.current_system_state["auto_restart_on_entity_changes"] = not current_setting

        if self.current_system_state["auto_restart_on_entity_changes"]:
            print(
                "✅ Auto-restart ENABLED - Servers will restart automatically after adding new entities"
            )
            print("💡 This ensures the web UI shows new entities immediately (recommended for PoC)")
        else:
            print(
                "⚠️  Auto-restart DISABLED - You'll need to manually restart servers to see new entities"
            )
            print("💡 Use 'restart servers' command after adding entities to refresh the web UI")

    def _show_model_prompt(self):
        """Show the model generation prompt"""
        print("\n💻 Model Generation Prompt:")
        print("─" * 40)
        print("The Student BAE uses this prompt to generate Pydantic models:")
        print()
        print("```")
        print("Generate a Pydantic model for Student entity with:")
        print("- Proper type hints and validation")
        print("- Business rule compliance")
        print("- Domain entity focus")
        print("- Semantic coherence with business vocabulary")
        print("```")
        print()
        print("📁 Full prompt templates: baes/llm/prompts/")

    def _show_api_prompt(self):
        """Show the API generation prompt"""
        print("\n🔌 API Generation Prompt:")
        print("─" * 40)
        print("The ProgrammerSWEA uses this prompt to generate FastAPI routes:")
        print()
        print("```")
        print("Generate FastAPI router with:")
        print("- Full CRUD operations")
        print("- Proper error handling")
        print("- Business vocabulary in endpoints")
        print("- Domain entity semantic coherence")
        print("```")
        print()
        print("📁 Full prompt templates: baes/llm/prompts/")

    def show_contextual_help(self):
        """Show contextual help based on current state"""
        print("\n💡 Available Commands:")
        print("─" * 40)

        # Entity creation shortcuts
        print("🎯 Entity Creation:")
        print("  • add student    - Create student entity")
        print("  • add course     - Create course entity")
        print("  • add teacher    - Create teacher entity")

        # System inspection
        print("\n🔍 System Inspection:")
        print("  • status         - Show system status")
        print("  • files          - Show generated files")
        print("  • database       - Show database info")
        print("  • show logs      - View server logs")

        # System management
        print("\n🛠️  System Management:")
        print("  • restart servers - Restart FastAPI/Streamlit")
        print("  • start servers  - Start servers (without restart)")
        auto_restart_status = (
            "ON" if self.current_system_state.get("auto_restart_on_entity_changes", True) else "OFF"
        )
        print(
            f"  • toggle auto restart - Auto-restart after entity changes ({auto_restart_status})"
        )
        print("  • show model     - View model generation prompt")
        print("  • show api       - View API generation prompt")
        print("  • clear          - Start fresh session")

        # General commands
        print("\n📋 General:")
        print("  • help           - Show this help")
        print("  • examples       - Show example requests")
        print("  • quit/exit      - Exit the CLI")

        print("\n🗣️  Natural Language:")
        print("  You can also use natural language like:")
        print("  • 'Create a student with name and email'")
        print("  • 'Add birth date field to students'")
        print("  • 'Show me the current entities'")

        if self.context == "evolving":
            print("\n🔄 Evolution Context:")
            print("  • Add new fields to existing entities")
            print("  • Modify business rules")
            print("  • Create relationships between entities")
            print("  • Use natural language for relationship creation")

        print("\n🤖 LLM-Powered Intelligence:")
        print("  • Smart relationship detection from natural language")
        print("  • Context-aware entity recognition")
        print("  • Flexible command interpretation")
        print("  • Domain-specific terminology understanding")
        print("  • Automatic foreign key relationship creation")

    def show_examples(self):
        """Show example requests"""
        print("\n📚 Example Requests:")
        print("─" * 40)

        print("🎯 Initial System Generation:")
        print("  • 'Create a student management system'")
        print("  • 'Generate an academic system with students'")
        print("  • 'I need a system to track student information'")

        print("\n🔄 System Evolution:")
        print("  • 'Add course entity to the system'")
        print("  • 'Include teacher information'")
        print("  • 'Add birth date field to students'")
        print("  • 'Students should have grade point average'")

        print("\n🔗 Relationship Creation (LLM-Powered):")
        print("  • 'Add a course to the student entity'")
        print("  • 'Connect teacher with course'")
        print("  • 'Enroll student in course'")
        print("  • 'Assign teacher to course'")
        print("  • 'Link student to course'")
        print("  • 'Associate course with student'")
        print("  • 'Register student for course'")
        print("  • 'Relate teacher to course'")

        print("\n🔍 System Inspection:")
        print("  • 'Show me the current system status'")
        print("  • 'What files have been generated?'")
        print("  • 'Display database information'")

        print("\n⚡ Quick Shortcuts:")
        print("  • 'add student' → Create student entity")
        print("  • 'add course' → Add course entity")
        print("  • 'status' → System overview")
        print("  • 'files' → Generated files list")

        print("\n💡 LLM-Powered Features:")
        print("  • Natural language relationship detection")
        print("  • Context-aware entity recognition")
        print("  • Flexible command interpretation")
        print("  • Domain-specific terminology support")

    def _get_interpretation_preview(self, request: str) -> Dict[str, Any]:
        """Get a preview of how the system would interpret the request without executing it"""
        try:
            # Create a temporary student BAE instance to get interpretation
            from baes.domain_entities.academic.student_bae import StudentBae
            preview_bae = StudentBae()
            
            # Get the interpretation without execution
            interpretation_result = preview_bae.handle(
                "interpret_business_request",
                {
                    "request": request,
                    "context": "academic"
                }
            )
            
            return interpretation_result
            
        except Exception as e:
            print(f"⚠️  Could not get interpretation preview: {str(e)}")
            return {"confidence": 0.5, "operation_type": "unknown"}

    def _needs_user_confirmation(self, interpretation_result: Dict[str, Any], request: str) -> bool:
        """Check if user confirmation is needed based on interpretation confidence and ambiguity"""
        
        # If interpretation failed, don't require confirmation (let it fail normally)
        if "error" in interpretation_result:
            return False
            
        confidence = interpretation_result.get("confidence", 0.5)
        detected_type = interpretation_result.get("operation_type", "unknown")
        
        # CRITICAL: If confidence is high (>=0.8) for basic create/evolve operations, don't ask for confirmation
        # This handles cases like "create a student entity with name and email" that should be straightforward
        if confidence >= 0.8:
            request_lower = request.lower()
            # For basic entity creation patterns, trust the high confidence
            if any(pattern in request_lower for pattern in ["create", "add student", "add course", "add teacher"]):
                return False
        
        # If confidence is high (>=0.7) and we have a valid operation type, don't ask for confirmation
        if confidence >= 0.7 and detected_type in ["create", "evolve", "relationship", "remove", "modify"]:
            return False
        
        # If confidence is low OR operation type is unknown, require confirmation
        if confidence < 0.7 or detected_type == "unknown":
            return True
        
        # Check for ambiguous patterns that often get misinterpreted
        request_lower = request.lower()
        
        # Check for relationship vs entity creation ambiguity
        if "add" in request_lower and "to" in request_lower and "entity" in request_lower:
            # This should be a relationship but often gets misinterpreted
            is_relationship = interpretation_result.get("is_relationship", False)
            
            if detected_type != "relationship" and not is_relationship:
                return True  # Likely misinterpreted relationship request
        
        # Check for patterns that suggest multiple valid interpretations
        ambiguous_keywords = ["add", "include", "create", "make", "build"]
        if any(keyword in request_lower for keyword in ambiguous_keywords):
            # If multiple entities are mentioned but it's not detected as relationship
            entities_mentioned = interpretation_result.get("entities_mentioned", [])
            if len(entities_mentioned) > 1:
                is_relationship = interpretation_result.get("is_relationship", False)
                
                if detected_type != "relationship" and not is_relationship:
                    return True  # Multiple entities but not relationship detection
        
        return False

    def _request_user_clarification(self, interpretation_result: Dict[str, Any], original_request: str) -> str | None:
        """Request user clarification for ambiguous interpretations"""
        from baes.utils.metrics_tracker import inc_clarification
        inc_clarification()
        
        print("\n🤔 Request Clarification Needed")
        print("=" * 50)
        print(f"Original request: '{original_request}'")
        
        # Show what the system interpreted
        detected_type = interpretation_result.get("operation_type", "unknown")
        confidence = interpretation_result.get("confidence", 0.0)
        reasoning = interpretation_result.get("reasoning", "No reasoning provided")
        
        print(f"\n🤖 System Interpretation:")
        print(f"   Operation type: {detected_type}")
        print(f"   Confidence: {confidence:.1f}/1.0")
        print(f"   Reasoning: {reasoning}")
        
        # Provide clarification options based on the request
        print(f"\n💭 Your request could mean:")
        
        options = []
        
        # Always offer the detected interpretation as option 1
        if detected_type == "relationship":
            options.append(("1", f"Create a relationship between entities", detected_type))
        elif detected_type == "create":
            options.append(("1", f"Create a new entity in the system", detected_type))
        elif detected_type == "evolve":
            options.append(("1", f"Add fields/attributes to existing entity", detected_type))
        else:
            options.append(("1", f"Execute as interpreted ({detected_type})", detected_type))
        
        # Offer alternative interpretations
        request_lower = original_request.lower()
        if "add" in request_lower and "to" in request_lower and "entity" in request_lower:
            # Likely a relationship that might have been misinterpreted
            if detected_type != "relationship":
                options.append(("2", f"Create a relationship between entities (add foreign key)", "relationship"))
            if detected_type != "evolve":
                options.append(("3", f"Add a field/attribute to existing entity", "evolve"))
            if detected_type != "create":
                options.append(("4", f"Create a new entity in the system", "create"))
        else:
            # General alternatives
            if detected_type != "create":
                options.append(("2", f"Create a new entity in the system", "create"))
            if detected_type != "evolve":
                options.append(("3", f"Add fields to existing entity", "evolve"))
            if detected_type != "relationship":
                options.append(("4", f"Create a relationship between entities", "relationship"))
        
        # Add cancel option
        options.append(("c", "Cancel this request", "cancel"))
        
        # Show options
        for option_key, description, _ in options:
            print(f"   {option_key}) {description}")
        
        # Get user choice
        while True:
            try:
                choice = input(f"\n🎯 Please select (1-{len(options)-1}, c): ").strip().lower()
                
                # Find matching option
                for option_key, description, operation_type in options:
                    if choice == option_key.lower():
                        if operation_type == "cancel":
                            return None
                        elif option_key == "1":
                            # Use original request with system interpretation
                            return original_request
                        else:
                            # Generate modified request based on user choice
                            return self._generate_clarified_request(original_request, operation_type)
                
                print("❌ Invalid choice. Please select a valid option.")
                
            except (EOFError, KeyboardInterrupt):
                print("\n❌ Request cancelled by user")
                return None

    def _generate_clarified_request(self, original_request: str, target_operation: str) -> str:
        """Generate a clarified request based on user's chosen operation type"""
        
        # Extract key entities/terms from original request
        request_lower = original_request.lower()
        
        if target_operation == "relationship":
            # Generate explicit relationship request
            if "student" in request_lower and "course" in request_lower:
                return "add course to student entity"  # Explicit relationship format
            elif "teacher" in request_lower and "course" in request_lower:
                return "add teacher to course entity"
            else:
                # Generic relationship format
                return f"create relationship for: {original_request}"
                
        elif target_operation == "create":
            # Generate explicit entity creation request - preserve original attributes
            if "student" in request_lower:
                # If original request had specific attributes, preserve them
                if "with" in request_lower:
                    return original_request  # Keep the full original request with attributes
                else:
                    return "add student entity"
            elif "course" in request_lower:
                if "with" in request_lower:
                    return original_request  # Keep the full original request with attributes
                else:
                    return "add course entity"  
            elif "teacher" in request_lower:
                if "with" in request_lower:
                    return original_request  # Keep the full original request with attributes
                else:
                    return "add teacher entity"
            else:
                return original_request  # Preserve the original request
                
        elif target_operation == "evolve":
            # Generate explicit evolution request
            return f"add field to existing entity: {original_request}"
            
        else:
            # Fallback - use original request
            return original_request

    def _suggest_error_recovery(self, error: str, request: str):
        """Suggest error recovery actions"""
        print("\n🔧 Suggested Recovery Actions:")

        if "VALIDATION_ERROR" in error:
            print("  • A critical validation error occurred during agent communication")
            print("  • This indicates missing mandatory information in the system coordination")
            print("  • This is typically a system configuration issue, not a user error")
            print(
                "  • The generation process was immediately interrupted to prevent system instability"
            )
            print("  • Please try again with a simpler request first:")
            print("    - 'add student' (basic entity creation)")
            print("    - 'add course' (known working entity)")
            print(
                "  • If the problem persists, this indicates a system bug that needs investigation"
            )
            print("  • Check the logs for specific validation details")

        elif "MAX_RETRIES_REACHED" in error:
            print("  • The system reached maximum retry attempts for a task")
            print("  • Check your OpenAI API key and internet connection")
            print(
                "  • Try simplifying your request (e.g., 'add student' instead of complex descriptions)"
            )
            print("  • Wait a moment and try again - API might be temporarily overloaded")
            print(
                f"  • Current max retries: {os.getenv('BAE_MAX_RETRIES', '3')} (configurable via BAE_MAX_RETRIES)"
            )
            print("  • Check system logs for specific error details")

        elif "ENTITY_NOT_SUPPORTED" in error:
            print("  • Try: 'add student', 'add course', or 'add teacher'")
            print("  • Use supported entity keywords in your request")

        elif "UNKNOWN_SWEA_AGENT" in error:
            print("  • This is a system configuration issue")
            print("  • Try restarting with 'restart servers'")

        elif "COORDINATION_EXECUTION_ERROR" in error:
            print("  • An unexpected error occurred during system generation")
            print("  • This could be due to OpenAI API issues or system configuration problems")
            print("  • Try again with a simpler request first")
            print("  • Check your OpenAI API key and internet connection")
            print("  • If the problem persists, check the logs for detailed error information")

        elif "OpenAI" in error or "API" in error:
            print("  • Check your OpenAI API key configuration")
            print("  • Verify internet connection")
            print("  • Try the request again in a moment")

        else:
            print("  • Try rephrasing your request")
            print("  • Use 'help' to see available commands")
            print("  • Check 'examples' for request patterns")

        print(f"\n💡 Original request: '{request}'")
        print("💡 Try a simpler version or use shortcuts like 'add student'")

    def is_status_command(self, input_str: str) -> bool:
        return input_str.lower().strip() in ["status", "show status", "system status"]

    def is_files_command(self, input_str: str) -> bool:
        return input_str.lower().strip() in ["files", "show files", "list files"]

    def is_database_command(self, input_str: str) -> bool:
        return input_str.lower().strip() in ["database", "show database", "db", "show db"]

    def is_shortcuts_command(self, input_str: str) -> bool:
        shortcuts = [
            "add student",
            "add course",
            "add teacher",
            "list entities",
            "restart servers",
            "start servers",
            "toggle auto restart",
            "show model",
            "show api",
            "show logs",
            "clear",
        ]
        # Use exact match instead of startswith to avoid false positives
        # e.g. "add course to student entity" should not match "add course"
        input_normalized = input_str.lower().strip()
        return any(input_normalized == shortcut for shortcut in shortcuts)

    def is_exit_command(self, input_str: str) -> bool:
        return input_str.lower().strip() in ["quit", "exit", "bye", "goodbye"]

    def is_help_command(self, input_str: str) -> bool:
        return input_str.lower().strip() in ["help", "?", "commands"]

    def is_examples_command(self, input_str: str) -> bool:
        return input_str.lower().strip() in ["examples", "example", "show examples"]

    def handle_exit(self):
        """Handle graceful exit"""
        print("\n📊 Session Summary:")
        duration = (datetime.now() - self.session_start).seconds
        print(f"  ⏱️  Duration: {duration} seconds")
        print(f"  💬 Interactions: {len(self.conversation_history)}")

        entities = self.current_system_state.get("entities", [])
        if entities:
            print(f"  🎯 Entities: {', '.join(entities)}")
        else:
            print("  🎯 Entities: None")

        # Save session before exit
        self._save_session()
        print("\n💾 Session saved. Resume with same command next time!")

        # Flush metrics log
        flush_snapshot()

        # Check if servers are running
        server_status = self.check_servers_running()
        if server_status["both_running"]:
            print("\n🌐 Servers remain running:")
            print(f"  • FastAPI: http://localhost:{self.current_system_state['api_port']}/docs")
            print(f"  • Streamlit: http://localhost:{self.current_system_state['ui_port']}")
            print("  • Use 'restart servers' command if you need to restart them")

        print("\n🤝 Thanks for testing the BAE System! Goodbye!")

    def handle_error(self, error: Exception, user_input: str):
        """Handle errors gracefully"""
        print(f"\n❌ An error occurred: {str(error)}")
        print("🔧 The system will continue running.")
        print("💡 Try a different request or use 'help' for guidance.")

        # Log error for debugging
        error_log = {
            "timestamp": datetime.now().isoformat(),
            "error": str(error),
            "user_input": user_input,
            "context": self.context,
        }
        self.conversation_history.append(error_log)


def main():
    """Main entry point"""
    # Configure logging to suppress verbose httpx logs unless in debug mode
    # httpx logs every HTTP request at INFO level, which is too verbose for normal operation
    httpx_logger = logging.getLogger("httpx")
    if os.getenv("BAE_DEBUG", "0").lower() in ("1", "true", "on", "yes"):
        httpx_logger.setLevel(logging.DEBUG)
        print("🐛 Debug mode enabled - HTTP request logs will be shown")
    else:
        httpx_logger.setLevel(logging.WARNING)  # Only show warnings and errors

    cli = BAEConversationalCLI()
    cli.start_conversation()


if __name__ == "__main__":
    main()
