# /utils/list_imports.py

# IMPORTANT!!!:
# this is a snippet code, NOT part of the application code base. It is meant to be used only once 
# What´s this script used for? --> gives a clean list of imported top modules actually used by the code.

import ast, sys, pathlib

root = pathlib.Path('src')
modules = set()
for p in root.rglob('*.py'):
    try:
        tree = ast.parse(p.read_text(encoding='utf-8'), filename=str(p))
    except Exception:
        continue
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                modules.add(n.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split('.')[0])

for m in sorted(modules):
    print(m)
