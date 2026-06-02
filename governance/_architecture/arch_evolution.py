#!/usr/bin/env python3
import subprocess
import json
from datetime import datetime
from collections import defaultdict

OUT_FILE = "/tmp/ORGANVM_ARCHITECTURE_EVOLUTION.txt"

def get_commits_for_repo(owner, repo):
    """Get commit history for a repo using GitHub API"""
    try:
        # Fetch commits with file changes
        result = subprocess.run(
            ['gh', 'api', f'repos/{owner}/{repo}/commits', '--paginate', '-q', '.[] | {sha: .sha, date: .commit.committer.date, message: .commit.message, author: .commit.author.name}'],
            capture_output=True, text=True, timeout=30
        )
        
        commits = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    commits.append(json.loads(line))
                except:
                    pass
        return commits
    except:
        return []

def get_tree_at_commit(owner, repo, sha):
    """Get directory tree at a specific commit"""
    try:
        result = subprocess.run(
            ['gh', 'api', f'repos/{owner}/{repo}/git/trees/{sha}?recursive=1'],
            capture_output=True, text=True, timeout=30
        )
        data = json.loads(result.stdout)
        dirs = set()
        for item in data.get('tree', []):
            if item['type'] == 'tree' and not item['path'].startswith('.'):
                dirs.add(item['path'])
        return sorted(dirs)
    except:
        return []

# Repository manifest
ORG_REPOS = {
    'meta-organvm': ['meta-organvm--superproject'],
    'organvm-i-theoria': ['organvm-i-theoria--superproject', 'organvm-corpvs-testamentvm', 'atomic-substrata'],
    'organvm-ii-poiesis': ['organvm-ii-poiesis--superproject', 'organvm-ii-poiesis/metasystem-master', 'object-lessons'],
    'organvm-iii-ergon': ['organvm-iii-ergon--superproject', 'content-engine--asset-amplifier', 'sign-signal--voice-synth'],
    'organvm-iv-taxis': ['organvm-iv-taxis--superproject'],
}

with open(OUT_FILE, 'w') as out:
    # Header
    out.write("╔═══════════════════════════════════════════════════════════════════════════════╗\n")
    out.write("║        ORGANVM ENTERPRISE: COMPLETE ARCHITECTURAL EVOLUTION HISTORY           ║\n")
    out.write("║                         Git Architecture Timeline                             ║\n")
    out.write(f"║                     Generated: {datetime.utcnow().isoformat()}Z                  ║\n")
    out.write("╚═══════════════════════════════════════════════════════════════════════════════╝\n\n")
    
    total_repos = 0
    processed_repos = 0
    all_events = []
    
    for org, repos in sorted(ORG_REPOS.items()):
        out.write("═══════════════════════════════════════════════════════════════════════════════\n")
        out.write(f"📦 ORGANIZATION: {org}\n")
        out.write("═══════════════════════════════════════════════════════════════════════════════\n\n")
        
        for repo in repos:
            total_repos += 1
            
            # Handle nested org/repo format
            if '/' in repo:
                repo_owner, repo_name = repo.split('/')
            else:
                repo_owner, repo_name = org, repo
            
            print(f"  ⏳ Fetching: {repo_owner}/{repo_name}...", flush=True)
            
            commits = get_commits_for_repo(repo_owner, repo_name)
            
            if not commits:
                out.write(f"\n┌─ REPOSITORY: {repo_owner}/{repo_name}\n")
                out.write("│  (No commits found or access denied)\n│\n\n")
                continue
            
            processed_repos += 1
            
            out.write(f"\n┌─ REPOSITORY: {repo_owner}/{repo_name}\n")
            out.write(f"│  Commits: {len(commits)}\n")
            
            # Get first and last dates
            if commits:
                first_date = commits[-1].get('date', '?')[:10]
                last_date = commits[0].get('date', '?')[:10]
                out.write(f"│  Range: {first_date} → {last_date}\n")
            
            out.write("│\n")
            out.write("│  COMMIT HISTORY (recent first):\n")
            
            # Show recent commits with message
            for i, commit in enumerate(commits[:30]):
                date = commit.get('date', '?')[:10]
                sha = commit.get('sha', '?')[:7]
                msg = commit.get('message', '').split('\n')[0][:60]
                author = commit.get('author', '?')
                
                out.write(f"│    [{date}] {sha} {msg}\n")
                
                # Store for timeline
                all_events.append({
                    'date': date,
                    'org': org,
                    'repo': repo_name,
                    'msg': msg,
                    'author': author
                })
            
            # Get final tree structure
            if commits:
                sha = commits[0].get('sha')
                dirs = get_tree_at_commit(repo_owner, repo_name, sha)
                
                out.write("│\n")
                out.write("│  FINAL ARCHITECTURE (HEAD):\n")
                
                for d in dirs[:20]:
                    out.write(f"│    ├── {d}/\n")
                
                if len(dirs) > 20:
                    out.write(f"│    ... ({len(dirs) - 20} more directories)\n")
            
            out.write("│\n")
    
    # Timeline summary
    out.write("\n\n")
    out.write("═══════════════════════════════════════════════════════════════════════════════\n")
    out.write("📊 ARCHITECTURAL EVOLUTION TIMELINE\n")
    out.write("═══════════════════════════════════════════════════════════════════════════════\n\n")
    
    # Sort by date
    all_events.sort(key=lambda x: x['date'], reverse=True)
    
    current_date = None
    for event in all_events[:100]:  # Last 100 events
        if event['date'] != current_date:
            current_date = event['date']
            out.write(f"\n📅 {current_date}\n")
        
        out.write(f"   • {event['org']}/{event['repo']}: {event['msg']}\n")
    
    # Summary
    out.write("\n\n")
    out.write("═══════════════════════════════════════════════════════════════════════════════\n")
    out.write("📋 SUMMARY\n")
    out.write("═══════════════════════════════════════════════════════════════════════════════\n\n")
    out.write(f"Total Organizations: {len(ORG_REPOS)}\n")
    out.write(f"Total Repos Targeted: {total_repos}\n")
    out.write(f"Repos with Data: {processed_repos}\n")
    out.write(f"Total Commit Events: {len(all_events)}\n")
    out.write(f"\nGenerated: {datetime.utcnow().isoformat()}Z\n")

print(f"\n✓ Architecture history written to: {OUT_FILE}")
result = subprocess.run(['wc', '-l', OUT_FILE], capture_output=True, text=True)
print(result.stdout.strip())

