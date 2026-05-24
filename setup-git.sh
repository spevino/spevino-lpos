#!/bin/bash
set -e
cd /home/team/shared
git config --global user.email "spevino@lpos.com"
git config --global user.name "Spevino LP-OS"
git config --global --add safe.directory /home/team/shared
git branch -m main 2>/dev/null || true

# Create .gitignore
cat > .gitignore << 'GITIGNORE'
__pycache__/
*.pyc
.env
.venv/
venv/
node_modules/
.next/
*.db
spevino.db
.DS_Store
*.egg-info/
dist/
build/
.gitkeep
GITIGNORE

# Add and commit
git add -A
git commit -m "Initial commit: Spevino Loss Prevention OS" 2>&1 || echo "COMMIT_ALREADY_EXISTS"

# Create GitHub repo and push
gh repo create spevino-lpos --public --description "Spevino Loss Prevention Operating System - AI-powered surveillance for retail loss prevention" --source=. --remote=origin --push 2>&1 || gh repo set-default spevino-lpos 2>&1; git push -u origin main 2>&1

echo "ALL_DONE"