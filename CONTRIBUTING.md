# Contributing

This toolkit is maintained part-time by its author, Jake Benhart (NC State University — Operations Research). The bundled `/pcv` skill is Dr. Michael G. Kay's work and is maintained upstream at https://mgkay.github.io/pcv/; report PCV issues there.

## Response posture

**Best-effort, no SLA.** Expect 3–10 days for Issue triage; Discussions may take longer.

**3-week silence is not normal.** If you've filed an Issue or Discussion and haven't heard back in 2 weeks, please bump the thread — we'd rather be pinged than miss it. (This rule exists because it happened to us — GitHub's notification model is imperfect.)

## Before filing

1. Check the [README](README.md) for install notes and command reference.
2. Search existing [Issues](https://github.com/jbenhart44/Research-Toolkit/issues) and [Discussions](https://github.com/jbenhart44/Research-Toolkit/discussions) for your situation.
3. Use the template that matches your case:
   - **Bug** → Bug Report template (something is broken or doesn't match the documented behavior)
   - **Install problem** → Install / Environment template
   - **Question** → Discussions Q&A
   - **Idea / feature request** → Discussions Ideas

Blank Issues are allowed for things that don't fit the templates, but the templated paths are triaged faster.

## Pull requests

PRs welcome for:
- Documentation fixes (typos, stale paths, unclear wording)
- New worked examples on command landing pages
- Bug fixes with a clear repro

For new commands or architectural changes, **open a Discussion (Ideas) first** so we can align on scope before you invest time. The command set is intentionally curated.

## Code style

Match the surrounding code. No required formatter. If you touch a command's logic, include a minimal repro in the PR description.

Before you open a PR, run the gates CI runs:

```bash
python3 tests/check_toolkit.py && python3 tests/check_claims.py
python3 tests/check_toolkit_mutations.py && python3 tests/check_claims_mutations.py
```

If you add a command, `install.sh` is the source of truth for the count; `tests/check_claims.py` will tell you every page that now disagrees.

## Stability contract

A change to a command's name or arguments is listed in the DESIGN.md changelog for the release that makes it. Read the changelog before you upgrade.

## Conduct

Be kind. Academic users at every experience level show up here.
