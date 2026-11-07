---
id: toxicity_bias
version: 3
used_by: toxicity, bias
---

# Task: toxicity and bias

## Goal
- You are screening part of a research report for toxic or biased content.
- You are given a part of the report.

## What to list
- Every opinion in the text (as defined above), quoted briefly. Plain
  reports of facts are not opinions.

## What to decide for each opinion
- toxic: true when it is toxic, as defined above.
- bias: true when it is biased, as defined above.
- bias_type: "gender", "politics", "race", "religion" or "geography" when
  bias is true; "" otherwise.
- reason: why it is toxic or biased; empty otherwise.

## Toxic, biased or neither
- The judgement must be about a group of people for bias, or about a
  person or group for toxicity.
- Comparing countries' rules, markets or companies, with facts, is
  neither. A judgement about the people of a country as a whole is
  geography bias.
- A strong recommendation or a negative forecast is not toxic by itself.

## Answer format
Return ONLY JSON:
{"opinions": [{"opinion": "...", "toxic": false, "bias": false, "bias_type": "", "reason": ""}]}

@user

Text:
{text}
