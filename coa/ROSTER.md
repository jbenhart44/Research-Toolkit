# Council of Agents — Project Roster

<!-- This file customizes which council members are available and when they're offered.
     The Clerk reads this file at the start of every /coa session.
     If this file doesn't exist, the Clerk uses the built-in default roster. -->

## Custom Seats

<!-- List each persona file in coa/personas/ and when to offer it.
     Format: **[Seat Name]** (`coa/personas/filename.md`) — [trigger condition] -->

- **Committee Chair** (`coa/personas/committee_chair.md`) — offer whenever the question involves dissertation scope, contribution framing, chapter structure, or advisor strategy
- **Domain Expert** (`coa/personas/domain_expert.md`) — offer whenever the question involves methodology choices, literature positioning, or reviewer expectations in a specific field
- **Advisor** (`coa/personas/advisor.md`) — offer for career, timeline, or project prioritization questions
- **Industry Practitioner** (`coa/personas/industry_practitioner.md`) — offer whenever the question involves external validity, real-world deployment, or practitioner relevance

## Seating Rules

<!-- Override the default seating logic. Remove or comment out lines you don't want. -->

# Always seat these two (matches built-in default — keep unless you have a reason to change)
always: Skeptic, Practitioner

# For methodology questions, prefer Methodologist over Economist
# on-keyword "methodology OR identification OR regression OR identification strategy": swap Economist → Domain Expert

# For dissertation/scope questions, always offer Committee Chair
# on-keyword "dissertation OR chapter OR scope OR committee OR defense": offer Committee Chair

## Notes

<!-- Any context about this project that helps the Clerk seat the right council.
     Example: "This is a labor economics dissertation. Reviewer 2 concerns are almost
     always about external validity and data quality." -->

