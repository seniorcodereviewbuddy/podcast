Create a git commit for the current staged and unstaged changes.

## Steps

You are preparing a git commit for the podcast project. Follow these steps in order:

### Step 1: Gather commit info

Run the commit-info script to see the current diff:

```
bash .claude/skills/commit/scripts/commit-info.sh
```

### 2. Determine what to commit

From `git status`, identify all modified, new, and deleted files.

**DO NOT stage:**
- `.env` files or anything containing secrets
- Large binaries or generated files that shouldn't be tracked

Stage specific files rather than `git add -A` or `git add .`.

### 3. Write the commit message

Follow the project commit message style:

```
Short summary (imperative mood, under 50 chars)

Explain WHY this change was made. What problem does it solve?
What was the previous behavior and what is it now?
Wrap body at 72 characters.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

- Subject: imperative mood ("Add" not "Added"), under 50 chars
- Body: required for non-trivial changes — motivation, context, how it works
- Co-author line always included

### 4. Create the commit

Combine `git add` and `git commit` into a **single Bash call** so the user only has to approve one command:

```bash
git add <file1> <file2> && git commit -m "$(cat <<'EOF'
Subject line here

Body explaining why.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)" && git status
```

This stages, commits, and confirms in one shot. If the pre-commit hook fails, fix the issue and retry — do NOT use `--no-verify`.

### 5. Report result

Show the committed hash from the `git status` output above.

## Output Format

```
## Commit

**Files staged**: [list]
**Message**:
> [subject]
>
> [body]

✓ Committed as [short hash]
```
