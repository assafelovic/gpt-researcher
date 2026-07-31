# Recruiting corpus — Nursing Mastery content inventory

The researcher's map of our own recruiting surface: what exists on
www.nursingmastery.com, what each page is for, and where the gaps are.
Research runs with the **Recruiting** scope read this folder, and the
Audience tab renders it for the team.

## What lives here

- `content-inventory.md` — generated inventory of nursingmastery.com pages
  (URL, title, description, section). Rebuild with:

  ```bash
  FIRECRAWL_API_KEY=... python scripts/build_recruiting_inventory.py
  ```

  The weekly audience-sweep GitHub Action refreshes it automatically.

- Strategy notes, positioning docs, and competitor teardowns — drop any
  markdown file here and commit; it becomes research context on deploy.

## The questions this corpus exists to answer

- "Which of our pages should rank for X?"
- "Where are our content gaps vs. the best recruiting content on earth?"
- "Does anything we published contradict what nurses actually say?"
  (cross-checked against `../audience/`)
