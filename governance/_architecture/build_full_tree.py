#!/usr/bin/env python3
import subprocess
import json
from collections import defaultdict

def get_org_repos(org):
    """Get all repos in an org"""
    try:
        result = subprocess.run(
            ['gh', 'api', f'orgs/{org}/repos', '--paginate'],
            capture_output=True, text=True, timeout=30
        )
        repos = json.loads(result.stdout)
        return [r['name'] for r in repos]
    except:
        return []

def get_tree_recursive(owner, repo):
    """Get recursive tree from GitHub"""
    try:
        result = subprocess.run(
            ['gh', 'api', f'repos/{owner}/{repo}/git/trees/HEAD?recursive=1'],
            capture_output=True, text=True, timeout=30
        )
        data = json.loads(result.stdout)
        paths = [item['path'] for item in data.get('tree', []) if item['type'] == 'tree']
        return sorted([p for p in paths if not '/.git' in p and not p.startswith('.')])
    except:
        return []

def build_tree_lines(paths, prefix=''):
    """Convert flat paths to tree structure"""
    if not paths:
        return []
    
    # Build hierarchy
    tree = {}
    for path in paths:
        parts = path.split('/')
        current = tree
        for part in parts:
            if part not in current:
                current[part] = {}
            current = current[part]
    
    lines = []
    def print_tree(d, prefix='', is_last=True):
        items = sorted(d.items())
        for i, (name, subtree) in enumerate(items):
            is_last_item = (i == len(items) - 1)
            
            if prefix == '':
                connector = ''
                newprefix = ''
            else:
                connector = '└── ' if is_last_item else '├── '
                newprefix = prefix + ('    ' if is_last_item else '│   ')
            
            lines.append(f'{prefix}{connector}{name}/')
            
            if subtree:
                print_tree(subtree, newprefix, is_last_item)
    
    print_tree(tree)
    return lines

# Get all organizations
result = subprocess.run(
    ['gh', 'api', 'graphql', '-f', 'query={enterprise(slug:"meta-organvm"){organizations(first:100){nodes{login}}}}'],
    capture_output=True, text=True
)
orgs_data = json.loads(result.stdout)
orgs = sorted([o['login'] for o in orgs_data['data']['enterprise']['organizations']['nodes']])

print("╔═══════════════════════════════════════════════════════════════════════════════╗")
print("║     COMPLETE ORGANVM ENTERPRISE FOLDER HIERARCHY (2026-05-18)                 ║")
print("╚═══════════════════════════════════════════════════════════════════════════════╝")
print()
print(f"📊 ENTERPRISE: meta-organvm (8 Organizations, {sum(len(get_org_repos(o)) for o in orgs)} Repositories)")
print()

for org in orgs:
    repos = get_org_repos(org)
    if not repos:
        continue
    
    print(f"{'═' * 85}")
    print(f"📦 ORGANIZATION: {org}")
    print(f"{'═' * 85}")
    
    for repo in sorted(repos):
        print(f"\n  📁 {org}/{repo}")
        print(f"  {'─' * 75}")
        
        paths = get_tree_recursive(org, repo)
        
        if paths:
            tree_lines = build_tree_lines(paths)
            for line in tree_lines[:60]:  # Limit output per repo
                print(f"    {line}")
            if len(tree_lines) > 60:
                print(f"    ... ({len(tree_lines) - 60} more directories)")
        else:
            print(f"    (no directories)")
    
    print()

