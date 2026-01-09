---
name: commit-and-push
description: Complete git workflow with quality checks and versioning - runs ruff linting and tests, stages changes, auto-increments semantic version, generates commit messages, updates CHANGELOG.md, creates tagged commits, and pushes to remote after confirmation. Use when ready to commit and push changes.
invocations: ["commit-and-push", "cap"]
allowed-tools: ["Bash(git:*)", "Bash(uv:*)", "Read", "Edit", "Write", "Grep", "Glob", "AskUserQuestion"]
---

# Commit and Push Workflow

This skill automates the complete git workflow for this project with quality checks and proper safeguards.

## Workflow Steps

### 1. Review Current State

First, check the current git status to understand what will be committed:

```bash
git status
git diff --staged
git diff
```

### 2. Run Ruff Linting

**QUALITY GATE**: Run ruff to check code quality and formatting:

```bash
uv run ruff check .
```

If there are any errors:
- Show the errors to the user
- Attempt to auto-fix if possible: `uv run ruff check --fix .`
- If issues remain, STOP and inform the user that linting must pass before committing

### 3. Run Tests

**QUALITY GATE**: Run the test suite to ensure nothing is broken:

```bash
uv run pytest
```

If tests fail:
- Show the test failures to the user
- STOP and inform the user that all tests must pass before committing
- Do not proceed with commit until tests pass

### 4. Stage All Changes

After quality gates pass, stage all changes including untracked files:

```bash
git add .
```

### 5. Analyze Changes and Generate Commit Message

Review the staged changes to understand what was modified:

```bash
git diff --staged --stat
git diff --staged
```

Based on the changes, generate a commit message following the conventional commits format used in this project:
- `feat:` for new features
- `fix:` for bug fixes
- `refactor:` for code refactoring
- `docs:` for documentation changes
- `test:` for test additions or changes
- `chore:` for maintenance tasks

The commit message should:
- Have a clear, concise subject line (under 50 characters)
- Include a body explaining what and why (if needed)
- Follow the project's commit standards from [.claude/instructions.md](../../instructions.md)

### 6. Determine Version Bump

Read the `.version` file to get the current version:
- If `.version` doesn't exist, initialize it with `0.1.0`
- Parse the version as MAJOR.MINOR.PATCH (semantic versioning)

Based on the commit message type, determine the version bump:
- `feat:` → bump MINOR (e.g., 0.1.0 → 0.2.0)
- `fix:` → bump PATCH (e.g., 0.1.0 → 0.1.1)
- `feat!:`, `fix!:`, or contains `BREAKING CHANGE:` → bump MAJOR (e.g., 0.1.0 → 1.0.0)
- `refactor:`, `docs:`, `test:`, `chore:` → bump PATCH by default

Version bump rules:
- When bumping MAJOR, reset MINOR and PATCH to 0 (e.g., 0.5.3 → 1.0.0)
- When bumping MINOR, reset PATCH to 0 (e.g., 0.5.3 → 0.6.0)
- When bumping PATCH, only increment PATCH (e.g., 0.5.3 → 0.5.4)

Update the `.version` file with the new version and stage it:
```bash
echo "0.2.0" > .version
git add .version
```

### 7. Update CHANGELOG.md

Based on the commit message and changes, update [CHANGELOG.md](../../../CHANGELOG.md):

1. Read the current CHANGELOG.md
2. Determine the appropriate category (Added, Changed, Fixed, etc.)
3. Add entries under the `[Unreleased]` section
4. Move unreleased changes to a **version-based section** using the NEW version number (e.g., `[0.2.0]`)
5. Include the date as a reference: `## [0.2.0] - 2026-01-09`
6. Follow the format from [.claude/instructions.md](../../instructions.md)

The changelog should include:
- Clear descriptions of what changed
- Bullet points for each significant change
- References to relevant files or modules
- Proper categorization (Added, Changed, Removed, Fixed, etc.)
- Version number as the primary identifier (dates are secondary)

### 8. Stage CHANGELOG.md

After updating the changelog:

```bash
git add CHANGELOG.md
```

### 9. Create the Commit

Create the commit with the generated message:

```bash
git commit -m "$(cat <<'EOF'
[commit message here]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

### 10. Create Annotated Git Tag

After creating the commit, tag it with the new version:

```bash
git tag -a "v0.2.0" -m "Release version 0.2.0"
```

The tag message should be: "Release version X.Y.Z"

### 11. Show What Will Be Pushed

Before pushing, show the user what commits will be pushed:

```bash
git log origin/$(git rev-parse --abbrev-ref HEAD)..HEAD --oneline
```

Or if the branch doesn't have an upstream yet:

```bash
git log --oneline -5
```

Also show the new version tag:
```bash
git describe --tags --abbrev=0
```

### 12. Confirm Before Pushing

**CRITICAL GUARDRAIL**: Always ask the user for explicit confirmation before pushing:

Use the AskUserQuestion tool to ask:
- Question: "Ready to push these commits to remote?"
- Options:
  - "Yes, push now" (description: "Push the commits and tags to the remote repository")
  - "No, cancel" (description: "Do not push, stop here")

### 13. Push to Remote (Only After Confirmation)

If the user confirms, push commits AND tags to remote:

```bash
git push origin $(git rev-parse --abbrev-ref HEAD) --follow-tags
```

The `--follow-tags` flag ensures annotated tags are pushed along with the commit.

If the branch doesn't have an upstream yet, set it:

```bash
git push -u origin $(git rev-parse --abbrev-ref HEAD) --follow-tags
```

If the user declines, stop and inform them that the commits and tags are ready locally but not pushed.

## Usage

Invoke this skill when you're ready to commit and push your changes:

```
/commit-and-push
```

Or use the shorter alias:

```
/cap
```

## Important Notes

- **Quality gates are enforced**: Ruff linting and tests MUST pass before committing
- **Automatic versioning**: The `.version` file is auto-incremented based on commit type
  - `feat:` → minor bump (0.1.0 → 0.2.0)
  - `fix:` → patch bump (0.1.0 → 0.1.1)
  - `feat!:` or `BREAKING CHANGE:` → major bump (0.1.0 → 1.0.0)
- **Git tags**: Each commit is tagged with an annotated version tag (e.g., `v0.2.0`)
- This skill will stage ALL changes (including untracked files) after quality checks pass
- The CHANGELOG.md will be automatically updated based on your changes
- You will always be asked for confirmation before pushing to remote
- Tags are pushed with commits using `--follow-tags`
- Commit messages follow conventional commits format
- The skill respects the project's commit and changelog standards from [.claude/instructions.md](../../instructions.md)

## Example Flow

1. User invokes `/commit-and-push`
2. I run ruff linting (with auto-fix if needed)
3. I run pytest to ensure tests pass
4. If quality gates fail, I STOP and report the issues
5. If quality gates pass, I stage all changes
6. I analyze the diff and generate a commit message
7. I determine version bump based on commit type and update `.version` file
8. I update CHANGELOG.md with today's date
9. I create the commit
10. I create an annotated git tag with the new version (e.g., `v0.2.0`)
11. I show you what will be pushed (commits and tags)
12. **I ask: "Ready to push these commits to remote?"**
13. Only after you confirm "Yes, push now", I push commits and tags to remote
14. I confirm the push was successful

## Safety & Quality Features

- **Ruff linting must pass** before committing
- **All tests must pass** before committing
- **Semantic versioning**: Automatic version management via `.version` file
- **Git tagging**: Each release is properly tagged with annotated tags
- Always shows git status first
- Shows full diff before committing
- Updates changelog systematically
- Shows what will be pushed (commits and tags)
- **Requires explicit confirmation before push**
- Never pushes without user approval
- Tags are pushed with commits for complete version tracking
