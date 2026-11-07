---
id: topic_relevance
version: 7
used_by: topic_relevance
---

# Task: topic relevance

## Goal
- You are checking whether each paragraph of a research report serves the
  report's core question.
- You are given the core query and the report's numbered paragraphs.

## What to decide for each paragraph
- verdict:
  - "yes": it helps answer the question; background the question needs
    counts;
  - "no": it is off topic, or padding that says nothing about the question;
  - "idk": you cannot tell, such as a short transition.
- reason: a short reason for every "no"; empty otherwise.

## On topic or not
- Judge each paragraph against the core query, not against its section
  heading.
- A paragraph on one aspect of the question is "yes" even when it does not
  answer the whole question: valuations or financing terms in a report on
  M&A activity are on topic.
- A paragraph on a related subject is "yes" when the report uses it to
  answer the question (a comparison, a cause, a context).
- Generic statements that would fit any report ("this is a complex and
  evolving field") are padding: "no".
- The report's notes about itself (its method, its sources, its date, its
  scope, a table of contents or list of its section headings) are "idk": they
  neither answer nor leave the question.

## Answer format
Return ONLY JSON, one entry per paragraph, in order:
{"verdicts": [{"paragraph": 1, "verdict": "yes", "reason": ""}]}

@user

Core question:
{question}

Paragraphs:
{paragraphs}
