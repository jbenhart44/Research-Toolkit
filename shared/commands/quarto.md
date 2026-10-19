---
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(ls:*), Bash(date:*), Bash(mkdir:*), Bash(cp:*), Bash(quarto:*), Bash(python3:*), Bash(open:*), Bash(xdg-open:*), Bash(cmd.exe:*), Agent
description: Generate a ~20-slide Quarto RevealJS presentation from background documents. Reads source material, designs slide structure, writes .qmd + .css, renders, checks the rendered page and screenshots it, and opens for review. Can also condense an existing deck to a target slide count.
---

# /quarto — Slide Deck Generator

> **When to use**: You need a presentation and have background documents (papers, notes, reports) to build from. Generates a complete Quarto RevealJS slide deck with CSS. To shorten an existing deck instead, use `/quarto --condense <deck.qmd> <slide-count> "<bucket-spec>"` (see the last section).

You are generating a Quarto RevealJS slide deck from background documents provided by the user. Your job is to read the source material, design a coherent ~20-slide narrative arc, write production-quality `.qmd` files (with a CSS override as needed), render them, check the rendered page, and open it in the browser for review.

A clean `quarto render` exit code does not mean the page is correct. Several common defects render with exit 0 (see STEP 6b), so this command checks the rendered HTML and looks at screenshots before calling a deck done.

---

## STEP 0: CHECK THAT QUARTO IS INSTALLED

Run this before anything else:

```bash
quarto --version
```

- **It prints a version number** (for example `1.5.57`): continue to "Before you start".
- **It fails** (`command not found`, or no output): **STOP.** Do not read sources or write slides, because the deck cannot render. Tell the user:

  > "Quarto is not installed, so I cannot render slides. Install it, then run `/quarto` again.
  >
  > - **All platforms:** download the installer from https://quarto.org/docs/get-started/
  > - **macOS (Homebrew):** `brew install --cask quarto`
  > - **Windows:** `winget install Posit.Quarto`
  > - **Linux / WSL (Debian or Ubuntu):** download the `.deb` file from the page above, then `sudo dpkg -i quarto-*.deb`
  >
  > After you install it, open a new terminal and run `quarto --version` to confirm it works."

  Give only the line for the user's platform if you know it, and keep the download page link in every case.

Do not install Quarto yourself. The installers need administrator rights on many machines, and the user must choose the install method.

---

## BEFORE YOU START

1. **Read project configuration.** If `~/.claude/toolkit-config.md` exists, read these keys:
   - `author_name` — the `author:` name in the YAML header.
   - `author_affiliation` — the affiliation under the author name, and the institution in a branded footer.
   - `quarto_theme_dir` — the folder holding the user's branded RevealJS theme (an `.scss` file, and optionally a footer HTML partial and a logo image). Used only by Option A in Step 3a.
   - `slides_folder` — where to save a deck that belongs to no single project folder (Step 4).

   Ask only for keys this deck actually needs. If the file or a needed key is missing, ask the user once, use the answer for this deck, and offer to save it to `~/.claude/toolkit-config.md`. Do not write to that file without a yes. If the user declines, use placeholders (`[Author Name]`, `[Institution / Department]`) and tell them which lines to fill in.

2. **Identify the argument**: Parse `$ARGUMENTS` for:
   - A task description (e.g., "create slides for my research proposal")
   - File paths to background documents
   - Any specific constraints (audience, slide count, emphasis areas, theme preference)
   - `--condense` — if present, skip to **Mode: Condense Existing Deck** at the end of this file.

3. **If `$ARGUMENTS` is empty or unclear**, ask the user:
   > "I need two things to build your slides:
   > 1. **Background documents** — which files should I read? (papers, reports, plans, notes)
   > 2. **Audience and purpose** — who is this for and what's the key message?
   >
   > Example: `/quarto conference talk for PhD committee, read paper.qmd and results/sweep_summary.md`"

   **STOP and wait for the user's response.** Do not proceed without source material.

---

## STEP 1: READ SOURCE MATERIAL

Read all files the user specified (or that are clearly relevant from context). For each file, extract:
- **Key claims** — with supporting data (numbers, percentages, findings)
- **Narrative arc** — what story does this material tell?
- **Figures/tables** — what data visualizations exist or should be created?
- **Citations** — note any claims that need source verification

**Budget**: Read up to 10 source files. If more are provided, ask the user to prioritize.

---

## STEP 2: DESIGN THE SLIDE STRUCTURE

Design a ~20-slide outline (±5 slides depending on content density). Follow this template structure:

| Section | Slides | Purpose |
|---------|--------|---------|
| **Opening** | 1-2 | Title + motivation/problem statement |
| **Background** | 2-3 | Context, prior work, what's known |
| **Method/Approach** | 3-5 | What was done and how |
| **Results** | 5-8 | Data, findings, comparisons |
| **Discussion** | 2-3 | Implications, limitations, what it means |
| **Conclusion** | 1-2 | Summary + next steps/recommendations |

**Present the outline to the user** before writing any slides:

> "Here's my proposed slide structure ([N] slides):
>
> 1. Title
> 2. [Slide title] — [1-line description]
> 3. ...
>
> Adjust? Or say 'proceed' to build."

**STOP and wait for approval.** The user may want to reorder, add, or remove slides.

**Pre-authorized build.** If the invocation already specifies the deliverable's shape (slide count + topic + audience) and reads as "build it" rather than "help me plan it", show the outline and proceed in the same turn, stating: "Proceeding per your spec; say stop to adjust the outline first." Still show the outline, and still render and open for review. Keep the hard STOP for invocations where the structure is genuinely open.

**Exception — Theme conversions**: When the user asks to convert an existing deck to a different theme, skip Steps 1-2. Go directly to Step 3 (theme selection) and follow the theme conversion checklist in the EDGE CASES section.

---

## STEP 2b: DETAIL PRESERVATION CHECKLIST

Before finalizing the slide outline, check for four compression failure patterns:

### Pattern 1: Table Drops
Scan source material for any table with 4+ rows of structured data (comparison tables, version histories, metric breakdowns, classification schemes). Each such table SHOULD map to its own slide unless it has fewer than 3 meaningful columns. If a table is being summarized as bullets, flag it: "Source has a [N]-row table at [location] — should this be its own slide?"

### Pattern 2: Concept Merging
If two source sections describe DIFFERENT mechanisms, models, or findings that happen to be adjacent in the document, they get SEPARATE slides. Test: "Could a reviewer ask a clarifying question about one without the other?" If yes, they are separate slides.

### Pattern 3: Missing Synthesis/Evolution Slides
If the source material describes a build-up across versions, phases, or iterations, there MUST be at least one slide showing the progression as a whole. The narrative of *how we got here* is often the most important slide for a technical audience. Check: "Does the source describe an iterative improvement process? If so, is there a slide showing the full arc?"

### Pattern 4: Highlight Box Overload
If a slide already has a table or >4 bullets, adding a highlight box WILL overflow at 1600x900. Limit to 1 highlight box per slide maximum. If the slide needs both data AND a callout, move the callout to speaker notes. Flag it: "This slide has [table/N bullets] + highlight box — move highlight to notes?"

When in doubt, err toward MORE slides (split) rather than fewer (merge). The 25-slide warning exists to catch bloat, not to encourage compression of substantive content.

---

## STEP 3: WRITE THE SLIDES

### 3a. Theme Selection

There are two built-in options, plus a "bring your own theme" path. Ask the user which they prefer if not specified in `$ARGUMENTS`. A default that works:

- **Branded (Option A)** for work presented under an institution or organization: thesis and committee talks, proposals, conference and department talks, coursework, advisor meetings.
- **Moon (Option B)** for informal work: personal projects, internal demos, notes.
- When in doubt and `quarto_theme_dir` is set, use the branded theme.

#### Option A: Branded Institutional Theme (recommended for academic/professional work)

Use this when the user has a university or organizational brand theme. Take it from `quarto_theme_dir` (ask for it if the key is missing; see "Before you start"), or from a path the user gives. It holds:
- An SCSS file (e.g., `myorg.scss`)
- A footer HTML partial (optional)
- A logo image (optional)

**Copy the theme files into a `theme/` subfolder next to the `.qmd`** rather than pointing at the shared folder, so the deck renders on its own and a later theme change does not alter old decks. If the footer partial holds a list that maps slides to section names, update that list for this deck's headings (Step 6c checks it). If there is no logo, omit the `logo:` line.

```yaml
---
title: "[Title]"
subtitle: "[Subtitle if needed]"
author:
  - name: "[author_name]"
    affiliation: "[author_affiliation]"
  # add one entry per co-author the user names (advisor, collaborators)
date: "[YYYY-MM-DD]"
format:
  revealjs:
    theme: [default, theme/myorg.scss]
    slide-number: true
    logo: theme/images/logo.png
    footer: "[Short title] | [Institution]"
    include-in-header: theme/slide-footer.html
    incremental: false
    transition: slide
    progress: true
    width: 1600
    height: 900
    margin: 0.04
    center: false
    embed-resources: true
    self-contained: true
    navigation-mode: linear
    controls: true
    controls-layout: edges
---
```

If no branded SCSS is available, use `theme: default` (Quarto's clean white theme) as a stand-in and note which lines to swap when the theme file is provided.

**Use the theme's own classes.** Read the SCSS for the classes it defines and use them instead of the generic patterns in 3b. Common ones, if the theme has them:

| Element | Syntax | Typical rendering |
|---------|--------|-------------------|
| Section divider | `## Title {.section-divider}` | Full-slide colour band |
| Highlight box | `::: {.highlight-box}` | Card with a coloured left border |
| Stat block | `::: {.stat-block}` with `[value]{.stat-value}` + `[label]{.stat-label}` | Centred number card |
| Smaller text | `## Title {.smaller}` | Reduced font for dense content |

```
::: {.stat-block}
[87.5%]{.stat-value}
[Agreement rate]{.stat-label}

Supporting context text here
:::
```

Do not put a dark `background-color` attribute on slides of a light theme.

#### Option B: Moon Dark Theme (for informal or non-institutional work)

Dark background, light text, no branding. Good for personal projects, internal demos, or non-academic presentations.

```yaml
---
title: "[Title]"
subtitle: "[Subtitle if needed]"
author: "[author_name]"
institute: "[author_affiliation]"   # omit if not wanted
date: "[YYYY-MM-DD]"
format:
  revealjs:
    theme: moon
    slide-number: true
    incremental: false
    fig-align: center
    width: 1920
    height: 1080
    margin: 0.05
    transition: fade
    embed-resources: true
    self-contained: true
    navigation-mode: linear
    controls: true
    controls-layout: edges
    css: [filename].css
---
```

Uses `.result-headline`, `.two-col`, and dark callout boxes (see 3b and 3d).

#### Option C: Bring Your Own Theme

If the user provides a `.scss` or `.css` file (or a path to one), use it directly:

```yaml
format:
  revealjs:
    theme: [default, path/to/custom.scss]
    css: path/to/override.css
```

Ask: "I see you have `[theme file]`. Should I use this as the theme? And is there a CSS override file alongside it?"

**MANDATORY navigation settings** (include in ALL theme options — never omit):
- `embed-resources: true` + `self-contained: true` — standalone HTML that works offline
- `navigation-mode: linear` — LEFT/RIGHT arrow keys advance slides horizontally; without this, RevealJS uses 2D navigation that causes vertical scrolling instead of sliding
- `controls: true` + `controls-layout: edges` — clickable arrows on screen edges
- `incremental: false` — use `. . .` for manual pauses only on narrative slides

### 3b. Slide Content Rules

For EVERY slide, follow these rules:

**Text density**:
- Maximum ~8 content elements per slide (bullets, table rows, callout boxes)
- If a slide needs more, split it into two slides (e.g., "Results 1/2", "Results 2/2")
- Use `. . .` pauses between logical groups on narrative slides
- Alternative: wrap specific bullet lists in `::: {.incremental}` / `:::` to make just that list incremental while the rest of the slide appears at once
- No pauses on data-heavy slides — let tables/figures appear at once

**Overflow prevention** (CRITICAL — text falling off the page is the #1 rendering failure):
- **For any deck with >10 slides, generate a companion CSS override file.** Many Quarto themes use large default fonts that overflow at 1600x900 on slides with >6 content elements. Trimming content alone often cannot fix this; the root font has to come down. Add `css: [name]-override.css` to the YAML header.
- **Standard overflow CSS** (copy into the companion `.css` file and adjust font sizes to taste):
  ```css
  .reveal .slides section { font-size: 0.72em; }
  .reveal .slides section.smaller { font-size: 0.65em; }
  .reveal .slides section table { font-size: 0.88em; }
  .reveal .slides section table td, .reveal .slides section table th { padding: 0.2em 0.4em; }
  .reveal .slides section li { margin-bottom: 0.1em; line-height: 1.25; }
  .reveal .slides section p { margin-top: 0.2em; margin-bottom: 0.2em; }
  .reveal .slides section h3 { margin-top: 0.2em; margin-bottom: 0.15em; }
  /* if the theme defines callout or stat classes, shrink them too (use its class names): */
  .reveal .slides section .highlight-box { padding: 0.4em 0.6em; margin-top: 0.3em; font-size: 0.92em; }
  .reveal .slides section .stat-block { padding: 0.3em 0.5em; font-size: 0.92em; }
  ```
- **Check at the target resolution BEFORE finalizing** by screenshot (Step 5). If any text is clipped at the bottom or right edge, fix it immediately by: (1) verifying the CSS override is linked in YAML, (2) removing highlight boxes from overflowing slides (move to speaker notes), (3) splitting the slide
- **Dense slides must use two-column layouts** — if a slide has both a table AND bullet points, split them into columns
- **Never rely on scrolling** — RevealJS slides do not scroll by default; content that overflows is invisible
- **A highlight box costs about 3 bullets of vertical space.** Limit to 1 per slide. If the slide already has a table or >4 bullets, move the highlight box to speaker notes.

Overflow is caused by content volume, not by the theme. Moon at 1920x1080 overflows the same way a branded theme does at 1600x900. These apply to every theme:
- **A bottom callout under a two-column block is the most common casualty.** A result headline + a two-column list (4 items per side) + a callout at the bottom will push the callout off the page. Fix that shape when you write it: either trim every bullet to one line AND mark the slide `{.smaller}`, or split the slide (content on one, callout or table on the next). Splitting is the more reliable fix; `{.smaller}` alone is often not enough for a 4+4 two-column slide plus a callout.
- **Apply `{.smaller}` to every data-dense slide by default** (any slide with a table, a two-column block, or >5 bullets), not only after one overflows. Over-applying it costs little; iterating slide by slide while the user reports "still off the page" costs a lot.
- **Reducing the deck `margin`** (e.g., 0.05 → 0.025) buys vertical room on every slide at once — a useful global lever when several slides are tight.
- **Map slide numbers exactly before editing.** When the user says "slide N is off the page", N counts the title slide as 1, so it is the (N−1)th `##` heading. List the headings in order (search the `.qmd` for lines starting with `## `) and count. Splitting or inserting a slide shifts every later number.

**Tables** (CRITICAL — this is the #1 source of rendering problems):

At 1600x900 with 4% margin (~1472px usable):
- **3 columns max** for descriptive text. Headers ≤15 chars, cells ≤25 chars.
- 4-column tables only with short numeric data.

At 1920x1080 with 5% margin (~1728px usable):
- **3 columns max** for descriptive text. Headers ≤15 chars, cells ≤30 chars.
- 4-column tables: abbreviate aggressively (~25 chars/column max).

Both resolutions:
- If a table needs long text, restructure as bullets or split into multiple slides
- **Test**: If any cell wraps to 2+ lines at presentation scale, restructure
- Do not bold text inside a header cell (see trap 4 in STEP 6b); a themed header is already emphatic.

**Result headlines**:

For light-background themes, use a bold introductory line:
```
**Key finding: [one sentence stating the slide's main claim.]**
```

For dark-background themes (Moon), use a styled callout:
```
::: {.result-headline}
[One sentence stating the slide's key finding or claim]
:::
```

**Callout boxes**:

Light-background (default/institutional):
```
::: {.callout-note}
**Key point here.** Supporting text.
:::
```
Or, if the theme provides a custom callout class (e.g., `.highlight-box`), use that instead.

Dark-background (Moon):
```
::: {style="background-color:#2d2d4e; padding:0.8em 1.2em; border-left: 4px solid #6666cc; margin-top:0.5em;"}
**Key point here.**
:::
```

**Two-column layouts** (use Quarto native columns — works across all themes):
```
:::: {.columns}
::: {.column width="50%"}
**Left column header**
- bullet 1
- bullet 2
:::
::: {.column width="50%"}
**Right column header**
- bullet 1
- bullet 2
:::
::::
```

On Moon, the `.two-col` class from the companion CSS (3d) also works:
```
:::: {.two-col .nonincremental}
::: {}
**Left column header**
- bullet 1
- bullet 2
:::
::: {}
**Right column header**
- bullet 1
- bullet 2
:::
::::
```

**Never put a `###` or `####` heading inside a `:::` div** (a column, a callout, any fenced div). It turns the slide into a vertical stack (trap 1 in STEP 6b). Use a bold line or a span with a class instead:
```
[The engagement]{.side-head}
```
```css
.reveal .slides section .side-head { display: block; font-weight: 700; margin-bottom: 0.2em; }
```

**Speaker notes** (REQUIRED on every substantive slide):
```
::: {.notes}
- 2-5 bullet points of context the presenter would say aloud
- Include details that didn't fit on the slide face
- Reference source documents for claims
:::
```

**Background color**:
- Light themes: No background-color needed (white by default). Use themed section divider classes if the theme provides them.
- Moon theme: Use `{background-color="#1a1a2e"}` on all content slides for consistent dark theme.

### 3b-2. Layout and Wording Defaults

Apply these unless the user asks otherwise. They are defaults, not house style; the user's request wins.

**Structure**
- **Headed bullet groups beat tables for prose.** A table is for a genuine matrix of short values. Sentences laid out in a grid read better as a bold label (`[Label]{.side-head}`) followed by short bullets.
- **No decorative kicker line above a slide title** (a small-caps "why it matters" line, for example) unless the user asks for one.
- **One lead line, then bullets indented under it.** Not a paragraph.
- **Text left, figure right** on a slide that has a real column of text and a figure.
- **If the text is only a few bullets, stack them UNDER the figure instead.** A narrow column holding three bullets is empty for most of its height. Stacked, the figure gets the full slide width and the text band underneath is two lines. Keep the band short: put the label span to the LEFT of the list rather than above it, and run the bullets in `column-count: 3` on the wrapper div. Both are CSS on one wrapper; the markup stays a span and a plain list.
- **Say which way the size actually went.** Stacking cannot make a taller-than-wide figure bigger full-screen, because anything under it costs height a side column did not. It can make the figure bigger in a windowed browser and slightly smaller full-screen. Report both numbers, not the flattering one.
- **A figure fills its slot.** If a figure leaves visible whitespace, fix the figure file, not the stylesheet: compute the slot's aspect (column width ÷ available height) and rebuild the figure to match it (trap 3 in STEP 6b). Enlarge the type in the same pass, in the figure and in the column; a bigger figure with the same type is just bigger whitespace inside its boxes. Estimate the column's fill before enlarging so you do not overshoot.

**Diagrams**
- **A band or group label names the place; the boxes are what is in it.** If one box in each row just names the row, remove it and promote its name to the band heading.
- **Box names only.** Explanatory subtext under every box belongs in the speaker notes or the text column.
- **Plain connecting lines, not arrowheads**, when a line means "belongs to" or "comes from". Reserve arrows for flow or sequence.
- **If colour encodes ownership or category, give the legend** on the slide or in the notes. When an item's category is unclear, state the assumption you made rather than guessing silently.
- **"Make it bigger" means make it legible**, which is usually an aspect-ratio problem (trap 3), not a request to scale the file.

**Words**
- **Every bullet starts with a capital letter.** Nothing in the Quarto toolchain reads bullet text, so a lowercase opener renders cleanly, passes every structural check, and is obvious once projected. Check it rather than relying on memory: search the `.qmd` for list items matching `^\s*([-*+]|[0-9]+\.)\s+[*_\[]*[a-z]`. Rules:
  - Judge the first character after leading markdown (`*`, `_`, `[`, spaces), not the first letter found anywhere. Otherwise `1983 was the year` fails on its `w`.
  - A non-letter opener is exempt. A bullet starting with a code span or a digit is already correct.
  - Speaker notes are exempt. They are the presenter's crib, not the page.
  - The fix upper-cases the first LETTER, not the first character, so `**read-only**` becomes `**Read-only**`.
- **The user's wording is the default.** Fix an outright typo; do not reword, tighten, or "improve" a phrase the user wrote. If a line does not fit its box, say so and offer to shrink the type or widen the box instead of rewriting the sentence.

### 3c. Data Accuracy

**CRITICAL**:
- Every specific number on a slide face MUST be traceable to a source document
- If a claim cannot be verified, add a speaker note: `- TODO: verify [claim] against [source]`
- Do NOT round or average numbers without showing your work in speaker notes
- Do NOT propagate numbers from conversation context without checking the source
- **MATERIAL GAP refusal token** (speaker-note-only guard). When `/audit` returns NOT FOUND or MISMATCH for a value that would otherwise appear on a slide, the `[MATERIAL GAP: ...]` marker goes ONLY in the speaker-note block (`::: {.notes}`), NEVER as a slide-face bullet. The slide-face content is either (a) dropped entirely or (b) replaced with a verified value from a different source. A visible `[MATERIAL GAP: ...]` line projected at a committee meeting, conference, or site visit is a credibility hit — louder than the underlying gap it documents. Speaker-note format:
  ```
  ::: {.notes}
  - [MATERIAL GAP: <claim> — needed from <source>, not found on disk]
  - Either obtain the source and re-render, or drop this slide.
  :::
  ```
  **If the slide does NOT already have a `::: {.notes}` block, create one** with the MATERIAL GAP marker as its first entry. Do NOT silently omit the marker because the speaker-note block is missing — the absence of a notes section is a stylistic default, not a directive to drop the gap-tracking artifact.

  Keep a count of the markers you leave. Step 5a checks that every marker sits in the notes and that the count matches.

### 3d. CSS Companion File

**For any theme with >10 slides**: Generate a companion CSS override file with the overflow prevention values from Step 3b and add `css: [name]-override.css` to the YAML header. This prevents the most common rendering failure (content clipping on dense slides).

**For Moon theme**: Also include these layout helper classes in the companion CSS:

```css
.reveal .slides section .result-headline {
  font-size: 0.85em;
  font-style: italic;
  color: #a0a0a0;
  margin-bottom: 0.5em;
}
.reveal .slides section .two-col {
  display: flex;
  gap: 2em;
  align-items: flex-start;
}
.reveal .slides section .two-col > div {
  flex: 1;
}
```

**Size figures in slide pixels, never `vh`** (trap 6 in STEP 6b). When you set a figure's `max-height`, write the budget it came from in a comment beside the rule.

---

### 3e. Source Document Registry

**REQUIRED**: After writing the slides, create a `[name]_sources.md` companion file next to the `.qmd`. This file maps every slide to the source documents it draws from, so future editors know exactly where each claim originates.

Format:
```markdown
# Source Document Registry — [Deck Title]

## Theme Files
| Resource | Location | Purpose |
|----------|----------|---------|
| [theme .scss] | [theme/ folder, copied from where] | Branding, classes |
| [footer partial / logo] | [path] | [what it does] |

## Content Sources
| Slide(s) | Source Document | Location | Key Data Pulled |
|----------|----------------|----------|-----------------|
| 1-2 (Title, Motivation) | [document name] | [path] | [what was used] |
| 3-5 (Background) | [document name] | [path] | [what was used] |
| ... | ... | ... | ... |

## Unverified Claims
| Slide | Claim | Status |
|-------|-------|--------|
| [N] | [claim text] | TODO: verify against [source] |

## Compression Decisions
| Source Content | Location | Decision | Reason |
|---------------|----------|----------|--------|
| [table/section name] | [source file] | DROPPED/MERGED/SUMMARIZED | [why] |
```

The Compression Decisions table documents intentional exclusions. If a reviewer asks about a missing topic, check there first.

This registry serves four purposes:
1. **Audit trail** — any reviewer can trace a slide claim back to its source
2. **Update trigger** — if a source document changes, the registry shows which slides need updating
3. **Reuse** — future `/quarto` invocations on similar topics can start from this registry
4. **Compression accountability** — documents what was left out and why, enabling informed review

---

## STEP 4: DETERMINE OUTPUT LOCATION

Place the files in the most logical location:
- If the source material is in a specific project folder, put slides there
- If it's cross-project, put them in `slides_folder` from the config (ask once if the key is missing, and offer to save it), or a shared top-level folder
- Name: `[descriptive_name]_slides.qmd` and `[descriptive_name]_slides.css`

Ask if uncertain:
> "I'll save the slides to `[path]/[name]_slides.qmd`. OK, or different location?"

---

## STEP 5: RENDER, CHECK, THEN LOOK AT IT

```bash
cd "[directory]" && quarto render [filename].qmd
```

`quarto render` exits 0 on a deck with a slide split into vertical sub-slides, an SVG that failed to parse and shows nothing, a table header that renders invisible, and text off the bottom of the page. None of those shows up in a read of the `.qmd`. So do 5a and 5b before opening the deck for the user.

### 5a. Structural checks on the rendered HTML

Run these on the rendered `.html`, not on the `.qmd`. The `.qmd` is what produced the page, not evidence about it. Each check can fail on its own:

1. **Nested sections.** reveal.js reads a `<section>` nested inside a slide as a vertical sub-slide. Any nested section is trap 1, except the stacks Pandoc builds on purpose when the deck uses `#` level-1 headings (a bare `<section>` wrapping `level1` and `level2` slides). A nested section does not change the top-level slide count, so it needs its own check.
2. **Slide count.** Slides = the title slide + one per `##` heading (+ one per `#` heading, if used). An extra slide with no heading is usually an orphaned `{.notes}` block or a stray `---`. If the user approved an outline, the content-slide count should equal its length.
3. **Images resolve.** Every `<img src>` that is not `data:` or `http(s):` exists on disk.
4. **SVGs parse.** Every SVG the `.qmd` references parses as XML, and so does every other SVG in the same folder (one edit pass can break a file the deck no longer points at). With `embed-resources: true` the HTML holds images as `data:` URIs, so check the SVG files on disk, not the HTML.
5. **No bold inside a `<th>`** (trap 4).
6. **Gap markers.** No `[MATERIAL GAP: ...]` marker on a slide face; the number in the speaker notes equals the number you deliberately left (3c).
7. **No empty slides.** Every slide carries text or a figure once its speaker notes are removed (slides with a background image are exempt).

One way to run all seven, standard library only (arguments: the rendered deck, the number of gap markers you left, and optionally the approved content-slide count):

```bash
python3 - "[filename].html" 0 [N] <<'EOF'
import re, sys, pathlib, urllib.parse, xml.dom.minidom
deck = pathlib.Path(sys.argv[1]).resolve()
gaps = int(sys.argv[2]) if len(sys.argv) > 2 else 0
expect = int(sys.argv[3]) if len(sys.argv) > 3 else None
qmd = deck.with_suffix(".qmd")
body = deck.read_text(errors="replace").split('<div class="slides">', 1)[-1]
body = re.sub(r"<script\b.*?</script>", "", body, flags=re.S)  # JS templates look like tags
NOTES = r'<aside\b[^>]*class="[^"]*\bnotes\b[^"]*"[^>]*>.*?</aside>'
fails = []

# 1-2. Slides. A '#' heading makes Pandoc wrap a bare <section> around level1 +
# level2 slides, by design. Any other nested <section> is a vertical sub-slide.
stack, slides, nested = [], [], []
for m in re.finditer(r"<section\b[^>]*>|</section\s*>", body):
    tag = m.group(0)
    if not tag.startswith("</"):
        ok = not stack or (stack[-1][0] == "<section>" and re.search(r"\blevel[12]\b", tag))
        if not ok:
            sid = re.search(r'id="([^"]*)"', tag)
            nested.append(sid.group(1) if sid else tag[:60])
        stack.append((tag, m.end(), ok))
    elif stack:
        tag0, start, ok = stack.pop()
        if ok and tag0 != "<section>":
            slides.append((tag0, body[start:m.start()]))
title = any("quarto-title-block" in t or 'id="title-slide"' in t for t, _ in slides)
content = len(re.findall(r"<h2\b", body)) + sum(bool(re.search(r"\blevel1\b", t)) for t, _ in slides)
if nested:
    fails.append(f"nested-sections: {nested} (a heading inside a ::: div became a vertical sub-slide)")
if len(slides) != content + title:
    fails.append(f"slide-count: {len(slides)} slides but {content} headings{' + title' if title else ''}")
if expect is not None and content != expect:
    fails.append(f"slide-count: {content} content slides, the outline has {expect}")

# 3-4. Images resolve; SVGs (referenced, and their siblings) parse.
for src in sorted(set(re.findall(r'<img\b[^>]*\bsrc="([^"]+)"', body))):
    if not src.startswith(("data:", "http:", "https:", "//")) and not (deck.parent / urllib.parse.unquote(src)).exists():
        fails.append(f"images-resolve: {src} is not on disk")
refs = set(re.findall(r'<img\b[^>]*\bsrc="([^"]+\.svg)"', body))
if qmd.exists():
    refs |= {r for r in re.findall(r'[^\s()\[\]"\'<>=]+\.svg\b', qmd.read_text(errors="replace")) if "://" not in r}
svgs = set()
for r in refs:
    p = (deck.parent / urllib.parse.unquote(r)).resolve()
    if p.exists():
        svgs.update(p.parent.glob("*.svg"))
    else:
        fails.append(f"images-resolve: {r} is referenced but not on disk")
for p in sorted(svgs):
    try:
        xml.dom.minidom.parse(str(p))
    except Exception as e:
        fails.append(f"svg-parses: {p.name} does not parse, so it renders as nothing ({e})")

# 5. Bold inside a table header cell.
bold = [re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r"<th\b[^>]*>(.*?)</th>", body, re.S)
        if re.search(r"<(strong|b)\b", c)]
if bold:
    fails.append(f"bold-in-th: {bold[:4]}")

# 6. Gap markers: speaker notes only, and exactly the number declared.
GAP = r"\[(?:MATERIAL )?GAP:[^\]]*\]"
on_face = re.findall(GAP, re.sub(NOTES, "", body, flags=re.S))
in_notes = re.findall(GAP, "".join(re.findall(NOTES, body, re.S)))
if on_face:
    fails.append(f"gap-markers: {len(on_face)} on a slide face; they belong in speaker notes")
if len(in_notes) != gaps:
    fails.append(f"gap-markers: {len(in_notes)} in speaker notes, {gaps} declared")

# 7. Empty slides (notes removed; background-image slides exempt).
for tag, inner in slides:
    if re.search(r"data-background-(image|video|iframe)", tag):
        continue
    inner = re.sub(NOTES, "", inner, flags=re.S)
    if not re.search(r"<(img|svg|video|iframe)\b", inner) and not re.sub(r"<[^>]+>|&#?\w+;|\s", "", inner):
        fails.append(f"empty-slides: {tag[:70]} has no text and no figure")

print(f"{len(slides)} slides ({content} content{' + title' if title else ''}), "
      f"{len(svgs)} SVG file(s) parsed, {len(in_notes)} gap marker(s) in notes")
print("\n".join("FAIL " + f for f in fails) or
      "Structural checks pass. Now screenshot the slides: this says the page is not broken, not that it is good.")
sys.exit(1 if fails else 0)
EOF
```

A pass means the page is not broken in these seven ways. It says nothing about whether a figure is big enough, whether a label overruns its box, or whether the words are right. **Screenshot the slides whatever it says.**

### 5b. Screenshot the slides

Quarto can install a headless browser in user space, with no sudo:

```bash
quarto install chrome-headless-shell --no-prompt
quarto tools        # the chrome-headless-shell row should say "Up to date"
```

Find the binary in Quarto's per-user data folder (macOS, then Linux):

```bash
B=$(find "$HOME/Library/Application Support/quarto" "$HOME/.local/share/quarto" \
      -type f -name chrome-headless-shell 2>/dev/null | head -1); echo "$B"
```

If `$B` is empty, ask the user where Quarto put it. Shoot one slide per invocation, at the deck's real `width` and `height`:

```bash
"$B" --headless --disable-gpu --no-sandbox --hide-scrollbars \
     --window-size=1600,900 --virtual-time-budget=7000 \
     --screenshot="/tmp/[name]_s10.png" "file://$PWD/[filename].html#/10"
```

Then **Read the PNG**. Looking is the step; producing the file is not.

- **`#/N` is the Nth `##` slide**, because the title slide is index 0. reveal's on-screen counter therefore reads `N+1`. Getting this wrong means reviewing the wrong slide and concluding the deck is fine.
- **Shoot each slide separately.** `?print-pdf` with `--print-to-pdf` can produce a single page instead of the whole deck.
- **Two screenshots with identical file sizes** usually mean both hash navigations failed and both landed on the title slide. Hash the files and check they differ before trusting a batch.
- For a quick read of a whole deck, tile the PNGs into a contact sheet (e.g., with Pillow) and look at that.
- If you resized a figure, also shoot at a smaller window (e.g., `--window-size=1244,700`) to see what a reviewer sees in a windowed browser.

**An SVG figure is cheaper to check on its own than a slide.** On macOS, `qlmanage -t -s 1400 -o <dir> figure.svg` renders it standalone; elsewhere, screenshot `file://.../figure.svg` with the same headless binary. That is enough to catch a collision, a clipped label or a parse failure.

**If the headless install genuinely fails**, fall back to structural fixes: mark every dense slide `{.smaller}`, split every two-column-plus-callout slide, and tell the user plainly that you fixed layout structurally because you could not screenshot it.

### 5c. Open in the browser

On macOS (add `#/N` to land on a slide):
```bash
open "[path to .html]"
open -a Safari "file://$PWD/[filename].html#/10"
```

On Windows (WSL):
```bash
cmd.exe /c start "" "[Windows path to .html]"
```

On Linux:
```bash
xdg-open "[path to .html]"
```

---

## STEP 6: REVIEW CHECKLIST

After rendering, run through this checklist:

- [ ] All figures PNG or SVG (not PDF)
- [ ] Every SVG parses as XML (Step 5a)
- [ ] No table wider than 3 descriptive columns
- [ ] All table headers ≤15 chars, cells ≤30 chars, and no bold inside header cells
- [ ] Math visible on slide background (check contrast; on dark themes avoid `\underbrace` with `\text{}`)
- [ ] Speaker notes on all substantive slides
- [ ] `incremental: false` in YAML
- [ ] Every number on slide face traceable to source document
- [ ] No `[MATERIAL GAP: ...]` marker on a slide face
- [ ] No Mermaid text overflow (3 lines max per node)
- [ ] **No text falling off the page** — screenshot every slide (Step 5b) and verify nothing is clipped at bottom or right. This is the #1 rendering failure. Only if the headless install fails, use the structural fallback in 5b and say so.
- [ ] **No slide has become a vertical stack** — the nested-sections and slide-count checks in Step 5a pass.
- [ ] **Overflow CSS present AND linked** — companion CSS file exists with reduced font size, AND the YAML header includes `css: [name]-override.css`. If either is missing, slides WILL overflow on dense content.
- [ ] **No `vh` in the stylesheet** — figure heights are in slide pixels (trap 6).
- [ ] **Every bullet starts with a capital letter** (3b-2).
- [ ] **Self-contained if sharing** — `embed-resources: true` + `self-contained: true` in YAML for standalone HTML files
- [ ] **No empty slides** — verify no slide is blank. Common cause: orphaned `{.notes}` block or `:::` div between two `---` separators after removing content during theme conversion. Check slide 2 especially (title slide removal artifact).

Report any issues found and offer to fix them.

---

## STEP 6b: SIX TRAPS THAT EXIT 0

Each of these produces a clean `quarto render` and a wrong page. Step 5a catches traps 1, 2 and 4. Traps 3, 5 and 6 need a screenshot, because they are about size and position, which no structural check sees.

### 1. A heading inside a `:::` div becomes a VERTICAL SUB-SLIDE

`####` or `###` inside `::: {.column}` or any fenced div makes Pandoc emit a nested `<section>`, and **reveal.js reads a nested `<section>` as a vertical sub-slide.** The parent stops being one slide: its intro paragraph and highlight box separate from the columns, and the presenter has to press **down** rather than **right** to reach them.

It is invisible in the source and nearly invisible on screen. The tell is arithmetic: reveal's counter reads higher than your heading count. Twenty `##` headings that report `24` slides means some slides became stacks.

**Fix: use a span with a class, styled `display: block`** (see 3b):

```markdown
[The engagement]{.side-head}     <!-- not: #### The engagement -->
```

This recurs easily, including right after it has been fixed. Let Step 5a catch it on every render rather than relying on memory.

### 2. `--` inside an XML comment voids the whole SVG

Two hyphens inside an XML comment are illegal. The file does not "mostly work": it fails to parse, and the figure renders as nothing or as an error. Writing an em dash as `--` in a hand-written SVG comment is the usual cause.

**Validate every SVG before rendering the deck** (Step 5a does this for all of them):
```bash
python3 -c "import xml.dom.minidom; xml.dom.minidom.parse('images/f.svg'); print('ok')"
```

### 3. A figure in a column is HEIGHT-constrained, so scaling the file does nothing

When the user says a figure is too small, the instinct is to enlarge the SVG. **An SVG scales uniformly, so changing its units changes nothing on screen.** If the figure is taller than its slot's aspect and sits in a column, height binds and the extra column width goes unused.

**Find the binding dimension first, then use the matching lever.** Compute the slot: `target aspect = column width ÷ available height`, and compare it with the file's `viewBox` aspect.

| File aspect vs slot | Binding | The lever |
|---|---|---|
| taller (smaller ratio) | height | widen and shorten the file: wider, shorter boxes, smaller gutters, so text fits fewer lines |
| wider (larger ratio) | **width** | **lengthen** the file: taller boxes, wider gutters, and every font up by the same factor |

Worked example: a slot 677px wide and 768px tall has target aspect 0.88. A 980×520 figure (aspect 1.69) can only be about 400px tall in it, and raising `max-height` does nothing because width already binds. Rebuilt at 980×834 (aspect 1.18) with taller boxes and every font about 30% larger, the same column renders it about 576px tall. No stylesheet change could have produced that.

In the height-bound case, the same idea runs the other way: boxes changed from 168×86 to 240×80 so each description fitted two lines instead of three, bands and gutters shrank, and the type grew into the room that bought. Aspect went 0.74 → 1.14 and the rendered text got roughly 40% larger at the same height.

- Removing a dead column from a `viewBox` enlarges everything else for free, because the same height now buys more scale.
- **The type must grow with the canvas.** Stretching a `viewBox` without touching the font sizes leaves the rendered text the same size and adds whitespace inside the figure.

### 4. Bold inside a table header cell can render invisible

`**Read-only in**` in a pipe-table header produces a `<strong>` whose colour can be nearly unreadable against a theme's coloured header bar, while the unbolded header beside it is fine. **Do not bold inside a `<th>`**; the header style is already emphatic.

### 5. Rotated SVG text clips off the viewBox

`transform="rotate(-90 x y)"` rotates about that point, and with `text-anchor: middle` the string extends both ways from it. Put the rotation centre at the MIDDLE of the run the label belongs to, not at its end, or half the label leaves the canvas. To check by hand: for each `<text>` that is not inside a transformed group, its `x`,`y` (or the `x y` of its `rotate(a x y)`) must lie inside the `viewBox`. That catches an anchor off the canvas, not a long label that starts on it and runs off; the screenshot catches that.

### 6. A `vh` figure height is measured against the WINDOW, not the slide

**Size a reveal figure in slide pixels. `vh` inside a reveal deck renders differently on every screen and exits 0 on all of them.**

reveal.js lays every slide out in a fixed pixel box (the YAML `width` × `height`, e.g. 1600×900) and then scales that whole box with a CSS transform to fit the window. `vh` is 1% of the browser viewport and is not inside that scaled coordinate system. So `max-height: 78vh` on a figure gives:

| Window height | What 78vh gives the figure | Of the 900px slide |
|---|---|---|
| 900px (full-screen) | 702px | 78% |
| 700px (windowed) | 546px | 61% |

The windowed case is what a reviewer sees when they open the file. This is the usual answer to "why is there so much whitespace" on a slide whose CSS looks generous.

Absolute px inside the slide box scale with everything else, so they behave the same on every screen. Budget them against the slide height: at 1600×900 with `margin: 0.04` the usable height is 828px; subtract the title (an `h2` with its rule and margins can take ~90px at a 30px root font) and what is left is the figure's. Write the budget in a comment beside the rule. The same applies to any `vh` in a reveal stylesheet, not only figures.

### Sizing text inside an SVG box, before you render

Roughly **0.5 × font-size per character** for lowercase Helvetica. A 168-wide box at 11.5px holds about 29 characters; a 240-wide box at 13.5px holds about 35. Compute the line break before you write the line, then rasterise and confirm.

---

## STEP 6c: PER-DECK CHECKS FOR A DECK THAT WILL BE REVISED (optional)

Step 5a is generic. For a deck that will go through many revisions, offer to add a small `check_deck.py` beside the `.qmd` for claims about THIS deck. It must read the rendered `.html`, not the `.qmd`. Assert at least:

1. The exact heading list, in order. This is the deck's structure, and it catches a reorder going wrong.
2. Any running footer or section map matches the real headings **in both directions**: every map entry matches a heading, and every heading is claimed by an entry. One direction alone misses a renamed slide.
3. Any per-slide classes the design depends on (column classes, section dividers).

Do not reimplement the Step 5a checks there; run Step 5a alongside it.

**Then prove it bites.** Copy the rendered HTML, mutate the copy, and watch the named check fail: swap two headings, delete a referenced figure, rename a heading without updating the footer map, drop a class. Let the script take the deck path as an argument so it can be pointed at the mutated copy. **Confirm each mutation actually changed the file before believing a result.** A replacement whose pattern matches nothing leaves the good file in place, and the check then passes for the wrong reason.

---

## STEP 7: OFFER QUALITY REVIEW

After the user has looked at the slides, offer:

> "The slides are rendered. Would you like me to:
> 1. **Run /pace** for a quality/accuracy audit (catches data errors, layout issues)
> 2. **Make specific edits** to individual slides
> 3. **We're done** — the deck is ready
>
> A /pace pass typically catches 5-10 issues per deck on first review."

---

## EDGE CASES

### If the user provides too little source material
Flag it: "I have [N] pages of source material. For a 20-slide deck, I typically need [estimate]. The slides may be thin on [specific sections]. Want to proceed or add more sources?"

### If the user wants a non-academic audience
Adjust: fewer tables, more callout boxes, shorter bullets, simpler language. Still follow all rendering rules.

### If figures need conversion from PDF to PNG
Use pymupdf:
```bash
python3 -c "import fitz; doc=fitz.open('fig.pdf'); doc[0].get_pixmap(matrix=fitz.Matrix(3,3)).save('fig.png')"
```

### If the deck exceeds ~25 slides
Warn: "The content maps to [N] slides. Decks over 25 slides lose audience attention. Want me to: (a) trim to 20 by moving details to speaker notes, (b) split into two decks, or (c) keep all [N]?" Option (b) on an existing deck is the condense mode below.

### If the user is editing an existing deck
- **Change only what the user named.** Do not touch other slides, other wording or other figures in the same pass. If the deck is under version control, diff the rendered text against the last commit and confirm every changed string is one the user asked for; judge the words a line gained, not whether an authorised word still appears in it.
- **The user's wording is the default** (3b-2).
- **Show the render after every change**, one change at a time, and name anything you noticed but did not change so the user can decide.

### If converting an existing deck from one theme to another

Theme conversion is a common operation. Follow this checklist to avoid rendering artifacts:

**YAML header conversion**:
1. Swap `theme:` to the new value (e.g., `theme: moon` ↔ `theme: [default, theme/myorg.scss]`)
2. Add or remove theme-specific keys: a branded theme usually wants `footer`, `include-in-header`, `logo`, `progress`, `center: false`
3. Update dimensions if switching between 1600x900 / `0.04` margin and 1920x1080 / `0.05` margin
4. Ensure `navigation-mode: linear`, `controls: true`, `controls-layout: edges`, `self-contained: true` are present

**Title slide conversion** (CRITICAL — this is where the empty-slide bug lives):
- If the old deck used a **manual title slide** (custom `##` with styled `:::` blocks) and the new theme uses an **auto-generated title slide** from YAML metadata (`title:`, `author:`, `date:`):
  - Delete the ENTIRE manual title slide including its `---` separator and any orphaned speaker notes. A `{.notes}` block sitting between two `---` separators creates an empty slide.
  - **Validation**: After conversion, run Step 5a. Slide 2 should have visible content, not be blank.

**Content slide conversion**:
- Remove or replace any theme-specific background-color attributes (going dark → light, remove every `{background-color="#1a1a2e"}`)
- Convert dark section-break slides to the target theme's divider class (e.g., `{.section-divider}`), if it has one
- Convert theme-specific CSS classes to the target theme's equivalents or Quarto native patterns: `.result-headline` → the theme's highlight class or a bold line; `.two-col` → `.columns` + `.column width="50%"`
- Update Mermaid diagram themes if switching between light and dark backgrounds (`'dark'` ↔ `'default'`) and restyle node colours
- Update any hardcoded color values for the new background (a light blue that reads on dark, e.g. `#4da6ff`, needs a darker shade such as `#1565c0` on white)

**Theme file setup** (converting to a branded theme):
- Create a `theme/` subfolder next to the `.qmd`
- Copy the theme's `.scss` from `quarto_theme_dir` (or the path the user gives)
- Copy the footer partial if the theme has one and update its section list for this deck
- Copy the logo if available; omit the `logo:` YAML line if not

---

## Mode: Condense Existing Deck

Invoked as `/quarto --condense <existing-deck.qmd> <target-slide-count> "<bucket-spec>"`.

**Use this mode when** the user has an existing deck and wants a shorter version organized by explicit scope buckets (e.g., compressing an 18-slide walkthrough to 10 slides with a "done / next / need" bucket spec). Skip Steps 1–3 (source reading, outline design, theme selection); the existing deck already has those fixed.

### Execution

1. **Read the existing deck** at the given path. Extract every `## Slide Title` heading and the content beneath each. Count the source deck's slides.
2. **Validate the bucket spec** — at most 4 buckets. More than 4 should not be a condensed deck; suggest splitting into two decks instead.
3. **Validate the target slide count** — it must satisfy `target ≥ (2 × bucket_count + 1)`: each bucket needs at least 2 slides, plus the title slide. If it is smaller, tell the user the floor and ask whether to raise the target.
4. **Map every existing slide to a bucket** OR mark it for cutting. Cuts must be explicit: list each cut slide with a one-sentence reason ("background framing — out of scope for this audience").
5. **Allocate the target count across buckets in proportion to the source material's depth, not equally.** A "done / next / need" spec on a deck with 12 done-slides and 4 next-slides should not split evenly; "done" has more documented material. Show the allocation explicitly: "Done: 5 slides, Next: 2 slides, Need: 2 slides."
6. **Present the cut list and bucket allocation to the user before writing anything.** Wait for approval. The user may override individual cuts (e.g., "keep the verification slide" — move it from Cut to a bucket).
7. **Produce the condensed deck** at `<existing-deck-stem>_<count>slide.qmd` (e.g., `project_walkthrough_10slide.qmd`). Reuse content verbatim where possible; do not rewrite content the source already has right. Keep the source's YAML header (theme, dimensions, CSS reference); update only `title:`, `subtitle:` (mention that it is condensed), and `date:`.
8. **Render the new deck** with `quarto render`, confirm the `.html` exists, and run Step 5a with the target content-slide count.

### Constraints

- **The theme does not change.** A Moon deck stays Moon, a branded deck stays branded.
- **The YAML CSS reference is kept.** If the source uses `css: <name>.css`, the condensed deck uses the same CSS file (no new CSS).
- **The title slide counts.** A "10-slide" target = 1 title + 9 content slides.
- **Cuts are shown before writing**, not after. The user reviews the cut list and can override BEFORE the file is created.
- **Speaker notes travel with their slide.** When a slide moves to the condensed deck, its `::: {.notes}` block comes with it. Update notes only where the surrounding context changed (e.g., "see slide 12" → "see slide 8").

### Output format for the cut/keep list

Show the user this table BEFORE producing the condensed deck:

```markdown
**Source deck**: <path> (<N> slides)
**Target**: <M> slides
**Buckets**: [bucket1, bucket2, ...]
**Allocation**: bucket1=<a>, bucket2=<b>, ... (sums to M-1; 1 reserved for title)

### Keep
| # | Slide title | Bucket | Why |
|---|---|---|---|
| 1 | <title> | bucket1 | <one-sentence reason> |
| ... | ... | ... | ... |

### Cut
| # | Slide title | Reason |
|---|---|---|
| <n> | <title> | <one-sentence reason> |
| ... | ... | ... |

Confirm to proceed, or override individual cuts (e.g., "keep slide 14, move to bucket2").
```

### Example invocation

`/quarto --condense slides/project_walkthrough.qmd 10 "done / next / need"`

Produces `slides/project_walkthrough_10slide.qmd`, for example with 5 done-slides + 2 next-slides + 2 need-slides + 1 title slide.

$ARGUMENTS
