#!/usr/bin/env python3
"""
Fix Python 3.10+ syntax to be compatible with Python 3.9
Replaces 'X | None' with 'Optional[X]' and 'list[X]' with 'List[X]'
"""
import re
import os
from pathlib import Path

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Check if file already has typing imports
    has_optional = 'from typing import' in content and 'Optional' in content
    has_list = 'from typing import' in content and 'List' in content
    has_iterable = 'from typing import' in content and 'Iterable' in content
    
    # Replace pipe union syntax with Optional
    # Matches patterns like: str | None, int | None, dict | None, float | None
    content = re.sub(r'(\w+)\s*\|\s*None', r'Optional[\1]', content)
    
    # Replace list[X] with List[X]
    content = re.sub(r'\blist\[', 'List[', content)
    
    # Replace Iterable[X] | None with Optional[Iterable[X]]
    content = re.sub(r'Iterable\[([^\]]+)\]\s*\|\s*None', r'Optional[Iterable[\1]]', content)
    
    if content != original:
        # Add necessary imports at the top
        imports_to_add = []
        if 'Optional[' in content and not has_optional:
            imports_to_add.append('Optional')
        if 'List[' in content and not has_list:
            imports_to_add.append('List')
        
        if imports_to_add:
            # Find existing typing import
            typing_import_match = re.search(r'^from typing import (.+)$', content, re.MULTILINE)
            if typing_import_match:
                existing_imports = typing_import_match.group(1)
                new_imports = existing_imports + ', ' + ', '.join(imports_to_add)
                content = content.replace(
                    f'from typing import {existing_imports}',
                    f'from typing import {new_imports}'
                )
            else:
                # Add new import at the beginning
                lines = content.split('\n')
                insert_pos = 0
                for i, line in enumerate(lines):
                    if line.startswith('import ') or line.startswith('from '):
                        insert_pos = i + 1
                    elif line.strip() and not line.startswith('#'):
                        break
                
                lines.insert(insert_pos, f'from typing import {", ".join(imports_to_add)}')
                content = '\n'.join(lines)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    return False

def main():
    app_dir = Path('app')
    fixed_count = 0
    
    for py_file in app_dir.glob('*.py'):
        if fix_file(py_file):
            print(f'Fixed: {py_file}')
            fixed_count += 1
    
    print(f'\nTotal files fixed: {fixed_count}')

if __name__ == '__main__':
    main()
