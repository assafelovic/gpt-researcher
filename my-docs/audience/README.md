# Audience corpus — the voice of nurses

This folder is the researcher's ground truth for what nurses and nursing
students actually say. Every research run with the **Audience** or
**Recruiting** scope reads these files (they load through the hybrid
`DOC_PATH` document loader), and the Audience tab in the Brain UI renders
them for the team.

## What lives here

- `quote-bank.md` — verbatim quotes with receipts (link, upvotes, date).
- `pain-points.md` — recurring pains ranked by how often and how loudly they
  come up.
- `brief-YYYY-MM.md` — distilled monthly audience briefs. The weekly sweep
  GitHub Action proposes these as pull requests; a human merges.

## Rules for anything added here

1. **Verbatim beats paraphrase.** Keep the audience's exact words; put your
   interpretation in a separate line, clearly labeled.
2. **Receipts required.** Every quote carries a source link and an
   engagement signal (upvotes, replies) so we can rank by feet-voting.
3. **Freshness matters.** Date every entry. The researcher is instructed to
   prefer recent voice over stale voice.

## How to add your own notes

Drop any markdown file in this folder and commit (or ask any agent to).
It becomes searchable research context on the next deploy — no other wiring
needed.
