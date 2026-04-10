import os
import re

def check_html(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    blocks = re.findall(r'{%\s*block\s+(\w+)\s*%}', content)
    endblocks = re.findall(r'{%\s*endblock\s*%}', content)
    
    if len(blocks) != len(endblocks):
        print(f"ERROR: {filepath} has unbalanced blocks. Blocks: {len(blocks)}, Endblocks: {len(endblocks)}")
        # Try to find which one
        # This is a bit naive but helpful
        pass

    # Check for unclosed {{ }}
    if content.count('{{') != content.count('}}'):
        print(f"ERROR: {filepath} has unbalanced {{ }}")

def check_js(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if content.count('{') != content.count('}'):
        print(f"ERROR: {filepath} has unbalanced {{ }}")
    if content.count('(') != content.count(')'):
        print(f"ERROR: {filepath} has unbalanced ( )")

def main():
    for root, dirs, files in os.walk('.'):
        if 'venv' in root:
            continue
        for file in files:
            path = os.path.join(root, file)
            if file.endswith('.html'):
                check_html(path)
            elif file.endswith('.js'):
                check_js(path)

if __name__ == "__main__":
    main()
