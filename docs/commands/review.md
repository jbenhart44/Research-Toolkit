# /review — Three-Lens Document Review

Your advisor just sent you a 40-page working paper and said "this is relevant to your chapter — read it carefully."

## When you need this

- Someone handed you a paper, memo, or long document and you need more than a summary
- You want to know what's actually wrong with an argument, not just what it says
- You received advisor feedback and want to extract every implication before your next meeting

## What it does — and what it won't

`/review` reads your document through three parallel expert perspectives — a Skeptic who challenges the methodology, a Practitioner who extracts what's directly usable, and an Editor who evaluates how well the argument is made. A Chair synthesis then produces key takeaways, relevance to your project, and three concrete implications. Output is typically 800–1200 words across all lenses plus synthesis.

**Note**: `/review` is for understanding a document's argument and implications — not for citation verification. For checking that numbers match their sources, use `/audit`.

## Worked example

Dario's advisor sent him a 40-page working paper on monopsony in labor markets with a note: "relevant to your third chapter." He has three days before their next meeting.

```
/review "advisor_docs/dube2025_monopsony.txt" "how does this relate to my wage-setting chapter?"
```

The Skeptic finds that the wage-markdown estimates assume competitive hiring in secondary markets — fragile if Dario's panel includes municipal workers. The Practitioner identifies two regression specifications directly adaptable to his dataset. The Editor notes the abstract undersells the main contribution, which is actually the decomposition in Section 4. The Chair synthesis gives Dario three concrete next steps, including one equation substitution he can implement this week.

## Try it

```
/review paper.txt
/review paper.txt "does this method generalize to my dataset?"
/review advisor_feedback.md
```

> *After reviewing: if the paper surfaces new citations you want to add to your own writing, run `/readable` on those PDFs, then `/audit` on your document after you've written the new section.*
