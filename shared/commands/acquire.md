---
allowed-tools: Bash(python3:*), Read, Write, Glob, Agent
description: Download a paper (or a manifest of papers), prove it is the right document, extract its text, and grep-check every claimed figure against it before anything cites it.
---

# /acquire — get the source on file, then check what it says

> **When to use**: before a document cites a paper you do not yet have on disk, or when a list of papers (perhaps
> suggested by a language model) has to be fetched and checked in one go. `/readable` extracts files you already have;
> `/acquire` downloads them first and refuses the ones that are not what they claim to be.

Every step below is one command of `acquire.py`, which `install.sh` puts in `~/.claude/toolkit/scripts/`. Each step
has a self-test and a mutation check (`scripts/acquire_mutations.py`), so a refusal here has been made to happen on
purpose, not only described.

```bash
A="$HOME/.claude/toolkit/scripts/acquire.py"
```

## Usage

```
/acquire <url> <target_path> [claimed:"<string>" ...]
/acquire manifest:<path_to_manifest.md>
```

Examples:
- `/acquire https://example.org/paper.pdf "papers/Author_2024.pdf" claimed:"22%"`
- `/acquire manifest:papers/to_acquire.md`

## Steps (one URL)

**0. Is the DOI the paper you think it is?** Run this when the URL or DOI came from a language model, a search
snippet, or anything other than the publisher's page or the paper itself:

```bash
python3 "$A" doi 10.xxxx/yyyy --expect "Author et al. (2023)"
```

Exit 1 is a MISMATCH: the claimed first author is not on CrossRef's record, so the DOI points at a different paper.
**Stop, correct the source of the DOI, and do not download.** A model can supply a DOI that is real, well formed and in
the right journal, and still belongs to someone else's paper; this check catches that before any time is spent. A year
off by one passes with a note, because online and print years often differ. Exit 4 means CrossRef could not be asked,
which is not a match.

**0b. Does an open copy exist at all?** For a journal article, ask before hunting:

```bash
python3 "$A" oa "Title of the paper"
```

Exit 0: an open copy is recorded. Exit 1: none is, so stop searching and go to the fallback ladder below. One call
answers what an hour of searching otherwise does not. Two things it will not tell you: an HTTP 400 is a malformed query,
not a negative result (the script retries a long title cut at its colon, which often surfaces a preprint the long query
hid); and an open copy is not the same as a retrievable one, since some open-access hosts refuse every automated
request. Exit 4 (no results, or no answer) says nothing about whether an open copy exists.

**1. Download, and refuse anything that is not the PDF.**

```bash
python3 "$A" fetch "<url>" "<target_path>"            # add --user-agent "Your Name you@example.org" where a host requires it
```

| Exit | Meaning | Next |
|---|---|---|
| 0 | a `%PDF` file is saved (a warning under 50 KB means: open it and confirm it is the paper) | step 2 |
| 1 | the host sent HTML (a bot check or a paywall page); nothing is saved | the known bot-blocked sources below |
| 2 | the target exists; an acquisition never overwrites | pick another name, or use the file already there |
| 3 | neither PDF nor HTML; kept for inspection | identify it before extracting |
| 4 | the download failed | retry later, or the fallback ladder |

**2. Extract, automatically, in the same run.** Extraction is part of every acquisition, never a separate question:

```bash
python3 "$A" extract "<target_path>"
```

It tries `pypdf`, then PyMuPDF, writes `<name>.txt` beside the PDF (`paper.pdf` becomes `paper.txt`, never
`paper.pdf.txt`) with a `=== PAGE N ===` header for every page, and gives a page with no text a typed
`[MATERIAL GAP: ...]` marker rather than leaving it out. Then the **density gate**: under 200 characters per page is
**SPARSE**. A text page yields thousands; a scanned page yields only its running header, about 70. A non-empty `.txt`
is not proof of an extraction, so SPARSE and EMPTY write no `.txt` at all and exit 3, with every page rendered as a
PNG and the folder named.

<!-- spawn: role=transcriber model=config:model_transcriber floor=haiku site=acquire#transcriber -->
**When extract exits 3 (SPARSE or EMPTY), transcribe the pages in the same run.** Start the transcriber with the
Agent tool (the `transcriber` row of `references/model-roles.md`). For its model, pass `model` = the value of
`model_transcriber` in `~/.claude/toolkit-config.md` if it is `haiku` or `sonnet`; otherwise pass `haiku` and print one
line. The floor is `model: "haiku"`. On `haiku` (smaller plans), start **two** transcribers in one message, writing
`<renders>/reader_1.txt` and `<renders>/reader_2.txt`; on `sonnet`, start one, writing `<renders>/reader_1.txt`. Each
reads every rendered PNG with the Read tool and writes a `=== PAGE N ===` header per page, tables as markdown tables,
figures as `[FIGURE: brief description]`, and a `[MATERIAL GAP: <one-line reason>]` line for any page it cannot read,
never a best guess. Then check before installing anything:

```bash
python3 "$HOME/.claude/toolkit/scripts/check_transcription.py" --pdf "<target_path>" --transcript <renders>/reader_1.txt [--second <renders>/reader_2.txt]
```

With two readers it refuses unless both agree on every number, page by page, because a misread digit is a number the
other reader does not have. Exit 0: copy `reader_1.txt` to `<name>.txt` beside the PDF with a first line
`[TRANSCRIBED from page images by <model> on <date>; check_transcription.py passed]`, then run `extract` again: it reads
the new `.txt`, applies the density gate, and exits 0 only if the transcription passes. Exit 1: install nothing, report
the failing checks, and offer to rerun on `sonnet`. Never change the model on your own.

<!-- BEGIN MODEL FAILURE -->
**MODEL FAILURE — when an agent cannot run on the model it requested.**
1. **A session or weekly limit** ("You've hit your session limit"). These limits are shared across all models, so another model does not help. Stop starting agents, quote the error and its reset time, and offer two choices: wait, or stop. Do not retry.
2. **An Opus limit, or a model the account cannot use, on the Chair's `opus` request** ("You've hit your Opus limit"; "There's an issue with the selected model"). Retry the Chair once on `sonnet`. Write `fallback_from: opus` and the error text into the run report, and name the model that ran in the printed model line.
3. **Any other error, or any other role.** Stop that role, quote the error, and offer the choices: retry as written, run that role on the session's model, or stop. Never change a role's model on your own; rule 2 is the only exception.
4. Do not rely on a fallback-model setting for this: Claude Code never switches models on an authentication, billing or rate-limit error.
<!-- END MODEL FAILURE -->

`/acquire` starts no Chair, so rule 2 never applies here.

A `.html` or `.docx` target is saved as it is; extract it with `/readable`.

**3. Check each claimed figure against the text.**

```bash
python3 "$A" verify "<target_path_without_.pdf>.txt" "22%" "14.41"
```

Each claim is matched ignoring case, line breaks and words hyphenated across a line, and reported as
`FOUND "<claim>" p.<N>` with its context, or `NOT FOUND`. A NOT FOUND in a source with unreadable pages names those
pages, because the figure may be on one of them; otherwise it is a possible hallucination to log before anything cites
it. A SPARSE source is refused (exit 3): its headers would find or miss strings at random.

**4. The verification matrix.** After every URL, print one row per claim. The extract column is the trust verdict:

```
| Paper | Downloaded | Extract status | Claimed figure | Grep result |
|---|---|---|---|---|
| Author (Year) | OK 1.2MB | OK (1850/pg) | "22%" | FOUND "22%" p.14: "...response rate of 22%..." |
| Author2 (Year) | OK 0.8MB | OK (640/pg) | "23.4%" | NOT FOUND "23.4%"; a possible hallucination |
| Author3 (Year) | OK 0.4MB | SPARSE needs transcription | (blocked) | (not run) |
```

**5. The VERDICT line, always:** `VERDICT: N/N acquired | M SPARSE/EMPTY (need transcription) | K grep NOT-FOUND | B blocked`.
Any SPARSE, EMPTY, NOT FOUND or blocked row means the run is not clean: name the rows to fix before anything cites them.

## Manifest mode

```bash
python3 "$A" manifest "<manifest.md>"
```

The manifest is a markdown table. Column names are matched by the words in them:

| Paper | URL | Target path | Claimed figures | DOI source |
|---|---|---|---|---|
| Author et al. (2023) | https://example.org/a.pdf | papers/Author_2023.pdf | "14.41", "21.4%" | Direct from publisher |
| Second & Third (2015) | https://doi.org/10.xxxx/yyyy | papers/Second_2015.pdf | -- | Model-suggested (UNVERIFIED) |

**DOI source values**: `Direct from publisher` (from the publisher's page or the paper itself), `CrossRef-verified
<date>`, `User-supplied`, and anything containing `UNVERIFIED`, for a DOI a language model supplied. Trusted rows run
first; UNVERIFIED rows run after them with step 0 enforced, and a row that fails it is BLOCKED and never downloaded.
A target path that already exists is used as it is, not downloaded again. Paths are relative to the manifest's folder.
The script prints the matrix, the VERDICT line and a count of UNVERIFIED rows that passed, and saves all of it as
`<manifest>_verified_<date>.md` beside the manifest, never over an earlier report. Exit 0 only when every row is
acquired and every claim found.

## Hard rules

- **Never cite a figure until it is FOUND on disk.** The matrix is an intermediate artifact, not a citation source.
- **A wrong document is not extracted.** HTML for a PDF, a MISMATCH on the DOI, or a PDF whose title is not the paper:
  log it as WRONG DOCUMENT and stop that row.
- **SPARSE is not acquired.** No grep, no citation, until a transcription passes the density gate.
- **A fetch summary is not the document.** A web fetch that answers a question with a small model returns a reading of
  the page, not the page. Save the file and extract it before quoting it.
- **A document is not ready to send while any work it cites is not on file** and checked against its text. "Four of
  five checked" is a useful report; "so it is ready" on top of it is not.

## The fallback ladder, when no open copy exists

Work down it and stop at the first rung that yields the file. Do not loop on a blocked source.

1. **Another product number for the same document.** Publishers number the same item differently (a case or a
   teaching note can carry one code from its publisher and another from a distributor, and a reprint can carry a third).
   A search on the wrong number finds nothing. Search every number you can find.
2. **Your library's proxy.** A link of the form `https://doi-org.<your-library-proxy>/<DOI>` needs the user's login,
   which the assistant does not have. Hand the user the DOI and say so.
3. **A course page that once hosted it, through the Wayback Machine.** The CDX API lists archived PDFs under a domain:
   `https://web.archive.org/cdx/search/cdx?url=<domain>/*&filter=mimetype:application/pdf&output=json`
4. **A co-author.** By far the cheapest route when one of them wrote it.
5. **Interlibrary loan**, for a short article where nothing else works.

**Rung 3 carries an obligation.** A copy a course page once hosted is often a review copy licensed to one named
person, and its footer says so. Read the footer of any PDF found this way and report the licence word for word.
Acquire it if it is the only way to check a claim, say plainly what it is, and tell the user to obtain a clean copy
before anything relies on it outside the project.

## Known bot-blocked sources

Observed during 2026. Hosts change their behaviour, so treat a row as a hint and re-probe rather than trusting it.

| Source | Behaviour | What to do |
|---|---|---|
| **SEC EDGAR** | refuses an undeclared automated client | `--user-agent "Your Name you@example.org"`: the SEC asks for a name and an email address |
| **ScienceDirect / Elsevier** | an HTML anti-bot page for every automated request, open-access papers included | a library proxy for paywalled papers; a browser download for open ones |
| **Case and teaching-note publishers** | metadata only, purchase required; numbers differ between publishers for one document | search every number; if a co-author wrote it, ask them first |
| **ResearchGate** | 403 without a login | use an institutional repository or the author's own page |
| **SSRN** | 403 to every automated client, on the abstract page and the download route | record the abstract id so nobody searches again, and hand the user a one-click list |
| **MDPI** | 403 or 409 on every route, on gold open-access papers too | one browser click. Do not read the 403 as a paywall: reporting an open paper as unavailable is the failure |

When a source is on this list, print the row's advice and do not retry blindly.

## Related

`/readable` (extraction for files already on disk) · `/audit` (checks a document's citations and numbers against the
`.txt` files this makes, and reports a figure on an unreadable page as GAP-IN-SOURCE, not NOT FOUND).

> **What next?** Once every row is FOUND, run `/audit` on the document that cites these papers.

$ARGUMENTS
