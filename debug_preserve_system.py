#!/usr/bin/env python3

import os
import sqlite3
import time
from pathlib import Path

from baes.core.enhanced_runtime_kernel import EnhancedRuntimeKernel


def generate_and_preserve_system():
    print("🔧 Generating system for inspection...")

    # Create debug temp directory
    debug_dir = Path("tests/.temp")
    debug_dir.mkdir(parents=True, exist_ok=True)

    # Create unique temp directory for this test
    temp_system_dir = debug_dir / f"scenario1_system_{os.getpid()}_{int(time.time())}"
    temp_system_dir.mkdir(parents=True)

    # Set managed system path to temp directory
    managed_system_path = temp_system_dir / "managed_system"
    os.environ["MANAGED_SYSTEM_PATH"] = str(managed_system_path)

    # Store original working directory
    original_cwd = os.getcwd()

    try:
        # Change to temp directory for file generation
        os.chdir(temp_system_dir)

        # Initialize kernel
        context_store_path = temp_system_dir / "context_store.json"
        kernel = EnhancedRuntimeKernel(context_store_path=str(context_store_path))

        # Process the business request
        business_request = (
            "Create a system to manage students with name, registration number, and course"
        )

        print(f"📝 Business Request: {business_request}")
        print(f"📁 System will be generated at: {managed_system_path}")

        # Generate the system
        start_time = time.time()
        result = kernel.process_natural_language_request(business_request)
        generation_time = time.time() - start_time

        print(f"✅ System generated in {generation_time:.2f} seconds")
        print(f"📊 Result: {result}")

        # Check what was generated
        if managed_system_path.exists():
            print(f"\n📂 Generated files:")
            for file_path in managed_system_path.rglob("*.py"):
                if "venv" not in str(file_path):
                    print(f"  - {file_path.relative_to(managed_system_path)}")

            # Check database
            db_path = managed_system_path / "app" / "database" / "academic.db"
            if db_path.exists():
                print(f"\n🗄️ Database schema:")
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(students);")
                columns = cursor.fetchall()
                for col in columns:
                    print(f"  - {col[1]} ({col[2]})")
                conn.close()
            else:
                print(f"\n❌ Database not found at: {db_path}")
        else:
            print(f"\n❌ Managed system not found at: {managed_system_path}")

        print(f"\n🔍 System preserved at: {temp_system_dir}")
        print("Files will remain for inspection until manually deleted.")

    finally:
        # Restore original working directory
        os.chdir(original_cwd)


if __name__ == "__main__":
    generate_and_preserve_system()
