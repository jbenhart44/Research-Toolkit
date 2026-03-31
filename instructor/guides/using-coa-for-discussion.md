# Using CoA for Research Discussion

## What CoA Does

Council of Agents (CoA) spawns a panel of specialists — each with a distinct professional perspective — to independently analyze a research question. A Chair agent then synthesizes their analyses into a convergence/divergence report.

## Why Use It in a Course

- **Surfaces perspectives students haven't considered.** A question like "Should we use simulation or optimization?" gets analyzed by a Skeptic, an Economist, a Practitioner, and a Methodologist — each seeing different tradeoffs.
- **Models academic discourse.** The convergence/divergence format mirrors how review panels work: where experts agree is high-confidence; where they diverge is where the real research questions live.
- **Great for seminar-style discussion prep.** Run `/coa` on a paper's central claim before class, and you have a structured multi-perspective analysis ready for discussion.

## Example: Research Question Analysis

### Before a Seminar

You're discussing a paper on dynamic pricing in ride-hailing. Run:

```
/coa "Is surge pricing welfare-improving or welfare-reducing for drivers?
Consider short-term vs. long-term effects, heterogeneous driver populations,
and platform market power."
```

CoA will produce a report with:
- **Skeptic**: Challenges the framing ("welfare for whom? which drivers?")
- **Economist**: Analyzes through surplus and efficiency lenses
- **Practitioner**: Grounds in operational reality ("drivers don't see the surge formula")
- **Convergence/Divergence**: Where the panel agrees and where genuine disagreement exists

Use the divergence points as discussion prompts for class.

### For Student Projects

Students working on research proposals can run `/coa` on their research question:

```
/coa "Is my proposed method (agent-based simulation) the right approach
for studying driver learning behavior, compared to econometric panel methods?"
```

The council's response helps students see their methodological choice from multiple angles before committing.

## Tips for Instructors

- **Use `--quick` for focused questions.** A 3-seat quick panel is faster and cheaper than the full council. Good for single-issue questions.
- **The divergence IS the lesson.** When council members disagree, that's where students learn the most. Don't treat it as a failure — it's the protocol working correctly.
- **CoA is a discussion tool, not an answer machine.** It surfaces perspectives; the student still decides.
