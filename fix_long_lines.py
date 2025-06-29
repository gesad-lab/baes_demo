#!/usr/bin/env python3
"""
Script to fix long lines in Python files by breaking them at appropriate points.
"""

from pathlib import Path


def fix_long_lines_in_file(file_path: Path, max_length: int = 120):
    """Fix long lines in a Python file."""
    print(f"Processing {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    fixed_lines = []

    for line in lines:
        if len(line) <= max_length:
            fixed_lines.append(line)
            continue

        # Skip comments and docstrings
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
            fixed_lines.append(line)
            continue

        # Try to break at logical points
        if 'f"' in line or "f'" in line:
            # Handle f-strings carefully
            fixed_lines.append(line)
            continue

        if "(" in line and ")" in line:
            # Try to break at parentheses
            if line.count("(") == line.count(")"):
                # Simple case - break after opening parenthesis
                parts = line.split("(", 1)
                if len(parts) == 2:
                    indent = len(line) - len(line.lstrip())
                    fixed_lines.append(parts[0] + "(")
                    fixed_lines.append(" " * (indent + 4) + parts[1])
                    continue

        if "," in line:
            # Try to break at commas
            parts = line.split(",")
            if len(parts) > 1:
                indent = len(line) - len(line.lstrip())
                fixed_lines.append(parts[0] + ",")
                for part in parts[1:-1]:
                    fixed_lines.append(" " * (indent + 4) + part + ",")
                fixed_lines.append(" " * (indent + 4) + parts[-1])
                continue

        # If we can't break it logically, just keep it
        fixed_lines.append(line)

    # Write back
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(fixed_lines))


def main():
    """Main function."""
    # baes_dir = Path("baes")  # Removed unused variable

    # Files with the most long lines
    priority_files = [
        "baes/swea_agents/backend_swea.py",
        "baes/swea_agents/techlead_swea.py",
        "baes/swea_agents/test_swea.py",
        "baes/swea_agents/frontend_swea.py",
        "baes/swea_agents/database_swea.py",
        "baes/core/enhanced_runtime_kernel.py",
        "baes/domain_entities/base_bae.py",
        "baes/llm/openai_client.py",
    ]

    for file_path in priority_files:
        if Path(file_path).exists():
            fix_long_lines_in_file(Path(file_path))


if __name__ == "__main__":
    main()
