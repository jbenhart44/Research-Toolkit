# /commit Smoke Test — Logical Grouping

**Purpose**: Verify `/commit` groups a mixed set of changes into logically-separate commits (the command's core claim) rather than concatenating them into one.

**Version**: v1.1 (2026-04-17)

---

## Fixture Setup

Create a test repo and populate with 6 uncommitted files that naturally fall into 3 groups:

```bash
TEST_REPO=$(mktemp -d)
cd "$TEST_REPO"
git init -q
git config user.email "test@example.com"
git config user.name "Test"
git commit --allow-empty -q -m "initial"

mkdir -p src tests docs
echo "def add(a, b): return a + b" > src/math.py
echo "def multiply(a, b): return a * b" > src/math_ext.py
echo "def test_add(): assert 1 == 1" > tests/test_math.py
echo "def test_multiply(): assert 2 == 2" > tests/test_math_ext.py
echo "# Math Module" > docs/math.md
echo "# Changelog" > CHANGELOG.md

git add -A && git status --short
```

Expected: 6 untracked files across 3 logical groups.

---

## The Test

Invoke `/commit` in Claude Code. Expected: **3 separate commits**, one per logical group:

1. `feat(src): add math and math_ext modules` — files: src/math.py, src/math_ext.py
2. `test(tests): add math module tests` — files: tests/test_math.py, tests/test_math_ext.py
3. `docs: add module README and changelog` — files: docs/math.md, CHANGELOG.md

**Success criteria**:
- Exactly 3 commits made (not 1, not 6)
- Each commit's files fall within a single logical group
- Commit messages follow Conventional Commits format (feat/fix/docs/test/chore)

**Failure modes**:
- **1 commit containing all 6 files**: concatenation bug (regression)
- **6 commits each with 1 file**: over-fragmentation (regression)
- **Cross-group commits**: grouping logic broken
- **Wrong Conventional Commits prefix**: message-type selection broken

---

## Automated Verification

```bash
cd "$TEST_REPO"
git log --oneline HEAD~5..HEAD
COMMITS=$(git rev-list --count HEAD)
[ "$COMMITS" -eq 4 ] && echo "PASS: 3 new commits + 1 initial" || echo "FAIL: expected 4, got $COMMITS"

# Verify no cross-group commits
for i in 1 2 3; do
  FILES=$(git show --name-only --pretty=format: HEAD~$((3-i)) | grep -v '^$')
  echo "Commit $i files: $FILES"
done
```

Each commit's files should stay within one of `src/`, `tests/`, `docs/`+`CHANGELOG.md`.

---

## Known Variance

Exact commit messages will vary (natural language generation). What matters structurally:
1. 3 groups, no cross-contamination
2. Conventional Commits prefix matches the group type
3. Message summarizes the group's intent

Slight wording variation is acceptable; structural failure (wrong count, wrong files per commit) is not.

---

## Cleanup

```bash
rm -rf "$TEST_REPO"
```

---

## When to Run

- After any edit to `shared/commands/commit.md` Step 2 "Grouping Logic" or Step 4 "Commit Messages"
- Before cutting a v1.x release
- If a user reports "commits are lumped" or "commits are over-split"
