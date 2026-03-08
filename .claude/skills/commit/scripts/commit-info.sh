#!/bin/bash
cd "$(dirname "$0")/../../.."

echo "=== Status ==="
git status --short

echo ""
echo "=== Recent Commits ==="
git log --oneline -5

echo ""
echo "=== Diff ==="
git diff HEAD
