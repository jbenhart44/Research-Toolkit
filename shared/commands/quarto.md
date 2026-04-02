---
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(ls:*), Bash(date:*), Bash(mkdir:*), Bash(cp:*), Bash(quarto:*), Bash(open:*), Bash(cmd.exe:*), Agent
description: Generate a ~20-slide Quarto RevealJS presentation from background documents. Reads source material, designs slide structure, writes .qmd + .css, renders, and opens for review.
---

# /quarto — Slide Deck Generator

> **When to use**: You need a presentation and have background documents (papers, notes, reports) to build from. Generates a complete Quarto RevealJS slide deck with CSS.

You are generating a Quarto RevealJS slide deck from background documents provided by the user. Your job is to read the source material, design a coherent ~20-slide narrative arc, write production-quality `.qmd` files (with a CSS override as needed), render them, and open in the browser for review.

---

## BEFORE YOU START

1. **Identify the argument**: Parse `$ARGUMENTS` for:
   - A task description (e.g., "create slides for my research proposal")
   - File paths to background documents
   - Any specific constraints (audience, slide count, emphasis areas, theme preference)

2. **If `$ARGUMENTS` is empty or unclear**, ask the user:
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

There are two built-in options, plus a "bring your own theme" path. Ask the user which they prefer if not specified in `$ARGUMENTS`.

#### Option A: Branded Institutional Theme (recommended for academic/professional work)

Use this when the user has a university or organizational brand theme. The user provides (or points to):
- An SCSS file (e.g., `theme/myorg.scss`)
- A footer HTML partial (optional)
- A logo image (optional)

```yaml
---
title: "[Title]"
subtitle: "[Subtitle if needed]"
author:
  - name: "[Author Name]"
    affiliation: "[Institution / Department]"
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

#### Option B: Moon Dark Theme (for informal or non-institutional work)

Dark background, light text, no branding. Good for personal projects, internal demos, or non-academic presentations.

```yaml
---
title: "[Title]"
subtitle: "[Subtitle if needed]"
author: "[Author Name]"
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
- **For any deck with >10 slides, generate a companion CSS override file.** Many Quarto themes use large default fonts that overflow at 1600x900 on slides with >6 content elements. Add `css: [name]-override.css` to the YAML header.
- **Standard overflow CSS** (copy into the companion `.css` file and adjust font sizes to taste):
  ```css
  .reveal .slides section { font-size: 0.72em; }
  .reveal .slides section.smaller { font-size: 0.65em; }
  .reveal .slides section table { font-size: 0.88em; }
  .reveal .slides section table td, .reveal .slides section table th { padding: 0.2em 0.4em; }
  .reveal .slides section li { margin-bottom: 0.1em; line-height: 1.25; }
  .reveal .slides section p { margin-top: 0.2em; margin-bottom: 0.2em; }
  .reveal .slides section h3 { margin-top: 0.2em; margin-bottom: 0.15em; }
  ```
- **Preview at the target resolution BEFORE finalizing** — if any text is clipped at the bottom or right edge, fix it immediately by: (1) verifying the CSS override is linked in YAML, (2) removing highlight boxes from overflowing slides (move to speaker notes), (3) splitting the slide
- **Dense slides must use two-column layouts** — if a slide has both a table AND bullet points, split them into columns
- **Never rely on scrolling** — RevealJS slides do not scroll by default; content that overflows is invisible

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
Or, if the theme provides a custom callout class, use that instead.

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

### 3c. Data Accuracy

**CRITICAL**:
- Every specific number on a slide face MUST be traceable to a source document
- If a claim cannot be verified, add a speaker note: `- TODO: verify [claim] against [source]`
- Do NOT round or average numbers without showing your work in speaker notes
- Do NOT propagate numbers from conversation context without checking the source

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

---

### 3e. Source Document Registry

**REQUIRED**: After writing the slides, create a `[name]_sources.md` companion file next to the `.qmd`. This file maps every slide to the source documents it draws from, so future editors know exactly where each claim originates.

Format:
```markdown
# Source Document Registry — [Deck Title]

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

This registry serves four purposes:
1. **Audit trail** — any reviewer can trace a slide claim back to its source
2. **Update trigger** — if a source document changes, the registry shows which slides need updating
3. **Reuse** — future `/quarto` invocations on similar topics can start from this registry
4. **Compression accountability** — documents what was left out and why, enabling informed review

---

## STEP 4: DETERMINE OUTPUT LOCATION

Place the files in the most logical location:
- If the source material is in a specific project folder, put slides there
- If it's cross-project, put in a shared or top-level folder
- Name: `[descriptive_name]_slides.qmd` and `[descriptive_name]_slides.css`

Ask if uncertain:
> "I'll save the slides to `[path]/[name]_slides.qmd`. OK, or different location?"

---

## STEP 5: RENDER AND OPEN

```bash
cd "[directory]" && quarto render [filename].qmd
```

Then open in browser. On macOS:
```bash
open "[path to .html]"
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

- [ ] All figures PNG (not PDF)
- [ ] No table wider than 3 descriptive columns
- [ ] All table headers ≤15 chars, cells ≤30 chars
- [ ] Math visible on slide background (check contrast)
- [ ] Speaker notes on all substantive slides
- [ ] `incremental: false` in YAML
- [ ] Every number on slide face traceable to source document
- [ ] No Mermaid text overflow (3 lines max per node)
- [ ] **No text falling off the page** — preview every slide at the target resolution and verify nothing is clipped at bottom or right. This is the #1 rendering failure.
- [ ] **Overflow CSS present AND linked** — companion CSS file exists with reduced font size, AND the YAML header includes `css: [name]-override.css`. If either is missing, slides WILL overflow on dense content.
- [ ] **Self-contained if sharing** — `embed-resources: true` + `self-contained: true` in YAML for standalone HTML files
- [ ] **No empty slides** — after rendering, verify no slide is blank. Common cause: orphaned `{.notes}` block or `:::` div between two `---` separators after removing content during theme conversion. Check slide 2 especially (title slide removal artifact).

Report any issues found and offer to fix them.

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
Warn: "The content maps to [N] slides. Decks over 25 slides lose audience attention. Want me to: (a) trim to 20 by moving details to speaker notes, (b) split into two decks, or (c) keep all [N]?"

### If converting an existing deck from one theme to another

Theme conversion is a common operation. Follow this checklist to avoid rendering artifacts:

**YAML header conversion**:
1. Swap `theme:` to the new value
2. Update dimensions if switching between 1600x900 and 1920x1080
3. Ensure `navigation-mode: linear`, `controls: true`, `controls-layout: edges`, `self-contained: true` are present

**Title slide conversion** (CRITICAL — this is where the empty-slide bug lives):
- If the old deck used a **manual title slide** (custom `##` with styled `:::` blocks) and the new theme uses an **auto-generated title slide** from YAML metadata:
  - Delete the ENTIRE manual title slide including its `---` separator and any orphaned speaker notes. A `{.notes}` block sitting between two `---` separators creates an empty slide.
  - **Validation**: After conversion, count slides in the rendered output. Slide 2 should have visible content, not be blank.

**Content slide conversion**:
- Remove or replace any theme-specific background-color attributes
- Convert theme-specific CSS classes (e.g., `.result-headline`, `.two-col`) to the target theme's equivalents or Quarto native patterns
- Update Mermaid diagram themes if switching between light and dark backgrounds
- Update any hardcoded color values for the new background

$ARGUMENTS
