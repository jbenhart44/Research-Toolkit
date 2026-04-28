# /commit — Intelligent Git Commit Workflow

You have 11 changed files across two workstreams and you don't want one giant mixed-purpose commit.

## When you need this

- Your working tree has changes spanning multiple logical units of work
- You want well-organized commit messages that explain what changed and why
- You're about to push and want a clean, readable history

## What it does — and what it won't

`/commit` analyzes your staged and unstaged changes, groups them into logical commits by topic, writes clear commit messages, and executes them in sequence. It shows you the proposed groupings and asks for confirmation before running — you stay in control.

**Note**: `/commit` does not automatically stage untracked files. You choose which files are in scope. It will show you `git diff --cached --name-only` before committing so you can verify nothing unexpected is included.

## Worked example

Maya finishes a session where she touched her DiD specification script, updated two reference files, and edited her methods chapter. She has 11 files in her working tree across two distinct workstreams.

```
/commit
```

`/commit` groups the changes into three logical commits: *(1) feat(scripts): add staggered DiD estimator — 3 R scripts; (2) docs(references): update parallel trends documentation — 2 reference files; (3) docs(chapter2): revise econometric methods section — 1 chapter file.* It presents the groupings, waits for her confirmation, then executes all three.

## Try it

```
/commit
```

> *If this session included writing any cited numerical values into a document, run `/audit` on that document now — before the session closes and the context of what you wrote is lost.*
