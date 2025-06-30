#!/usr/bin/env python3
"""Script to fix critical linting errors in frontend_swea.py"""

import re

def fix_frontend_swea():
    """Fix critical linting errors in frontend_swea.py"""
    
    # Read the file
    with open('baes/swea_agents/frontend_swea.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix f-strings missing placeholders (F541)
    # Replace f"..." with "..." when no {} is present
    content = re.sub(r'f"([^"]*)"', lambda m: f'"{m.group(1)}"' if '{' not in m.group(1) else m.group(0), content)
    
    # Remove unused variable display_columns
    content = re.sub(r'display_columns = \[.*?\]\s*\n\s*# columns_str was unused and is removed', '', content, flags=re.DOTALL)
    
    # Remove trailing whitespace (W291)
    content = re.sub(r'[ \t]+$', '', content, flags=re.MULTILINE)
    
    # Remove blank lines with whitespace (W293)
    content = re.sub(r'^\s+$', '', content, flags=re.MULTILINE)
    
    # Write back
    with open('baes/swea_agents/frontend_swea.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Fixed critical linting errors in frontend_swea.py")

if __name__ == "__main__":
    fix_frontend_swea() 