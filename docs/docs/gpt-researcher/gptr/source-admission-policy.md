---
sidebar_label: Source Admission Policy
---

# Source Admission Policy

An optional LLM-based quality gate that evaluates scraped sources against a caller-provided admission policy before inclusion in research. Sources that violate the policy are rejected, improving the signal-to-noise ratio of the final report.

## How It Works

1. After scraping, each source's content is sent to a fast LLM for scoring
2. The LLM returns a violation score in `[0.0, 1.0]` — lower means cleaner
3. Sources with a score above the threshold are rejected
4. Accepted sources proceed to context management and report generation

The policy is entirely caller-defined. You control what counts as a violation by writing the admission prompt.

## Quick Start

```python
from gpt_researcher import GPTResearcher
import asyncio

async def main():
    researcher = GPTResearcher(
        query="latest developments in quantum computing",
        source_assessment_prompt=(
            "Accept only independent, primary sources with original data or analysis. "
            "Reject press releases, blogs, opinion pieces, and derivative content "
            "that merely repeats other sources."
        ),
        source_assessment_threshold=0.25,
    )

    await researcher.conduct_research()
    report = await researcher.write_report()
    print(report)

    # Inspect assessment results
    for a in researcher.get_source_assessments():
        status = "ACCEPTED" if a["accepted"] else "REJECTED"
        print(f"  [{status}] {a['url']} — score: {a['score']}, reason: {a['reason']}")

if __name__ == "__main__":
    asyncio.run(main())
```

When `source_assessment_prompt` is not set (the default), the feature is disabled and all scraped sources are accepted as before.

## Configuration

| Parameter | Default | Description |
|---|---|---|
| `source_assessment_prompt` | `None` (disabled) | Free-text policy the LLM evaluates each source against |
| `source_assessment_threshold` | `0.25` | Maximum violation score for acceptance. Set to `0.0` for strict rejection, `1.0` to accept all |
| `source_assessment_max_content_chars` | `12000` | Number of raw content characters sent to the LLM per source. Use `-1` for full content |
| `source_assessment_max_concurrency` | `4` | Maximum number of sources assessed in parallel |

The assessment uses the `FAST_LLM` model configured on the researcher, so it runs quickly and at low cost.

### Writing Effective Policies

A good admission policy is specific about what to accept and reject:

```python
# Strict — only primary research
policy = (
    "Accept peer-reviewed papers, official documentation, and original data sources. "
    "Reject news articles, blogs, forums, Wikipedia, and any secondary summaries."
)

# Domain-specific
policy = (
    "Accept sources from established financial institutions, regulatory filings, "
    "and recognized financial news outlets. Reject personal blogs, social media posts, "
    "and unverified market commentary."
)
```

### Fact-Checking Claims

The most powerful use case is **fact-checking**: verifying a claim by excluding the claimant and all derivative sources from the research scope. This forces the researcher to find independent corroboration — or lack thereof.

For example, to verify a Gartner prediction you want zero Gartner content in the results:

```python
researcher = GPTResearcher(
    query="AI agent market size 2030 prediction accuracy",
    source_assessment_prompt=(
        "You are verifying an independent claim. Accept only sources that are "
        "completely independent of Gartner. Reject any Gartner publications, "
        "Gartner citations, Gartner press releases, articles quoting Gartner analysts, "
        "and any derivative content that references or relies on Gartner research. "
        "Only accept original data from other analysts, company filings, market reports "
        "from other firms, and independent empirical studies."
    ),
    source_assessment_threshold=0.2,
)
```

This pattern generalizes to any claim verification:

```python
# Verify a company's sustainability claims
policy = (
    "Accept only third-party audits, regulatory filings, NGO reports, and independent "
    "journalistic investigations. Reject all content published by Acme Corp, Acme Corp "
    "press releases, Acme-sponsored research, trade publications funded by Acme, and "
    "any article that primarily cites Acme as its source."
)
```

The key principle: **name the entity to exclude explicitly**, then block its publications, citations, sponsored content, and derivatives. Set a low threshold (`0.1`–`0.3`) to ensure strict enforcement.

## Accessing Assessment Results

After research completes, inspect the assessment records:

```python
# All assessments (accepted + rejected)
assessments = researcher.get_source_assessments()

# Only rejected sources
rejected = researcher.get_rejected_sources()
```

Each assessment record contains:

```python
{
    "url": "https://example.com/article",
    "title": "Article Title",
    "accepted": True,           # Boolean decision
    "score": 0.1,               # Violation score [0.0, 1.0]
    "reason": "Independent data analysis.",
    "matched_policy": "primary_sources",
}
```

## Behavior Details

- **Scraped sources**: Assessed after scraping in `BrowserManager.browse_urls()`
- **Pre-fetched content**: Retriever results that already contain full text (e.g., PubMed, arXiv) are assessed before merging with scraped content
- **LLM failures**: If the LLM call fails or returns malformed output, the source is rejected with a descriptive error reason
- **Score coercion**: Scores outside `[0.0, 1.0]` or non-numeric values cause rejection — the `accepted` flag from the LLM response is ignored; only the numeric score matters

## Performance Considerations

- Each assessment incurs one fast LLM call. For a typical research run with 15–30 sources, expect modest additional cost
- Concurrency is capped at `source_assessment_max_concurrency` to avoid overwhelming the LLM provider
- Content is truncated to `source_assessment_max_content_chars` to keep token usage predictable

## Limitations

- Adds latency proportional to the number of scraped sources
- Requires a functioning LLM provider; assessment cannot run offline
- Policy quality depends on how clearly you articulate acceptance criteria
