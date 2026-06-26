# GPT-Researcher Evaluations

This directory contains evaluation tools and frameworks for assessing the performance of GPT-Researcher across different research tasks.

## Evaluation Overview

Three complementary evaluation systems, each answering a different question:

| System | Question | Requires ground truth? |
| --- | --- | --- |
| `simple_evals/` | Is the answer factually correct? | Yes (OpenAI SimpleQA dataset) |
| `quality_eval/` | Is the report well-sourced and complete? | No — works on any query |
| `hallucination_eval/` | Does the report fabricate content? | No — compares against scraped sources |

**Quick start:**

```bash
# Factual accuracy (needs ground-truth answers)
python -m evals.simple_evals.run_eval --num_examples 10

# Report quality (works on any query, zero-cost metrics only)
python -m evals.quality_eval.run_eval --num_examples 10 --no-subtopic --no-hallucination --no-unsupported-claim

# Hallucination detection
python -m evals.hallucination_eval.run_eval -n 5
```

## Simple Evaluations (`simple_evals/`)

The `simple_evals` directory contains a straightforward evaluation framework adapted from [OpenAI's simple-evals system](https://github.com/openai/simple-evals), specifically designed to measure short-form factuality in large language models. Our implementation is based on OpenAI's [SimpleQA evaluation methodology](https://github.com/openai/simple-evals/blob/main/simpleqa_eval.py), following their zero-shot, chain-of-thought approach while adapting it for GPT-Researcher's specific use case.

### Components

- `simpleqa_eval.py`: Core evaluation logic for grading research responses
- `run_eval.py`: Script to execute evaluations against GPT-Researcher
- `requirements.txt`: Dependencies required for running evaluations

### Test Dataset

The `problems/` directory contains the evaluation dataset:

- `Simple QA Test Set.csv`: A comprehensive collection of factual questions and their correct answers, mirrored from OpenAI's original test set. This dataset serves as the ground truth for evaluating GPT-Researcher's ability to find and report accurate information. The file is maintained locally to ensure consistent evaluation benchmarks and prevent any potential upstream changes from affecting our testing methodology.

### Evaluation Logs

The `logs/` directory contains evaluation run histories preserved in version control.

Two formats are kept side-by-side:

| Format | Example filename | Purpose |
| --- | --- | --- |
| Plain text (legacy) | `SimpleQA Eval 100 Problems 2-22-25.txt` | Human-readable terminal output |
| Structured JSON | `eval_2025-02-22_10-32-11_n100.jsonl` | Machine-readable, suitable for trend analysis |

Each JSON log file contains one record with three sections: `run_metadata`, `aggregate_metrics`, and per-query `results`. See [`example_output.json`](simple_evals/example_output.json) for the full schema.

**Note:** Unlike typical log directories, this folder and its contents are intentionally tracked in git to maintain a historical record of evaluation runs.

### Features

- Measures factual accuracy of research responses
- Uses GPT-4 as a grading model (configurable)
  ```python
  # In run_eval.py, you can customize the grader model:
  grader_model = ChatOpenAI(
      temperature=0,                           # Lower temperature for more consistent grading
      model_name="gpt-4-turbo",               # Can be changed to other OpenAI models
      openai_api_key=os.getenv("OPENAI_API_KEY")
  )
  ```
- Grades responses on a three-point scale:
  - `CORRECT`: Answer fully contains important information without contradictions
  - `INCORRECT`: Answer contains factual contradictions
  - `NOT_ATTEMPTED`: Answer neither confirms nor contradicts the target

**Note on Grader Configuration:** While the default grader uses GPT-4-turbo, you can modify the model and its parameters to use different OpenAI models or adjust the temperature for different grading behaviors. This is independent of the researcher's configuration, allowing you to optimize for cost or performance as needed.

### Metrics Tracked

- Accuracy rate and F1 score
- Cost — total and per-query average
- Latency — average, p50 (median), and p95 per query
- Success/failure counts and answer attempt rates
- Source coverage per query

### Running Evaluations

1. Install dependencies:
```bash
cd evals/simple_evals
pip install -r requirements.txt
```

2. Set up environment variables in `.env` file:
```bash
# Use the root .env file
OPENAI_API_KEY=your_openai_key_here
TAVILY_API_KEY=your_tavily_key_here
LANGCHAIN_API_KEY=your_langchain_key_here
```

3. Run evaluation:
```bash
python run_eval.py --num_examples <number>
```

The `num_examples` parameter determines how many random test queries to evaluate (default: 1).

#### Customizing Researcher Behavior

The evaluation uses GPTResearcher with default settings, but you can modify `run_eval.py` to customize the researcher's behavior:

```python
researcher = GPTResearcher(
    query=query,
    report_type=ReportType.ResearchReport.value,  # Type of report to generate
    report_format="markdown",                      # Output format
    report_source=ReportSource.Web.value,         # Source of research
    tone=Tone.Objective,                          # Writing tone
    verbose=True                                  # Enable detailed logging
)
```

These parameters can be adjusted to evaluate different research configurations or output formats. For a complete list of configuration options, see the [configuration documentation](https://docs.gptr.dev/docs/gpt-researcher/gptr/config).

**Note on Configuration Independence:** The evaluation system is designed to be independent of the researcher's configuration. This means you can use different LLMs and settings for evaluation versus research. For example:
- Evaluation could use GPT-4-turbo for grading while the researcher uses Claude 3.5 Sonnet for research
- Different retrievers, embeddings, or report formats can be used
- Token limits and other parameters can be customized separately

This separation allows for unbiased evaluation across different researcher configurations. However, please note that this feature is currently experimental and needs further testing.

### Output

Each run produces two outputs:

#### Console summary

```text
=== Evaluation Summary ===
Total queries tested: 100
Successful queries: 100
Failed queries: 0

=== AGGREGATE METRICS ===
Debug counts:
Total successful: 100
CORRECT: 92
INCORRECT: 7
NOT_ATTEMPTED: 1
{
  "correct_rate": 0.92,
  "incorrect_rate": 0.07,
  "not_attempted_rate": 0.01,
  "answer_rate": 0.99,
  "accuracy": 0.9292929292929293,
  "f1": 0.9246231155778895
}
========================
Accuracy: 0.929
F1 Score: 0.925

Total cost: $9.6000
Average cost per query: $0.0960
Latency — avg: 48.3s  p50: 45.1s  p95: 89.2s

Structured log saved → evals/simple_evals/logs/eval_2025-02-22_10-32-11_n100.jsonl
```

**Structured JSON log** (`logs/eval_YYYY-MM-DD_HH-MM-SS_n{N}.jsonl`)

See [`example_output.json`](simple_evals/example_output.json) for the full schema. Key fields:

```
run_metadata        → timestamp, git_commit, grader_model, researcher_model
aggregate_metrics   → accuracy, f1, cost, avg/p50/p95 latency, success/fail counts
results             → per-query list with grade, score, latency, cost, sources
```

## Quality Evaluation (`quality_eval/`)

Measures the structural and content quality of research reports without requiring ground-truth answers. All metrics run on any open-ended query.

All metric logic lives in `metrics.py`. The runner is `run_eval.py`.

### Metrics

| Metric | Description | LLM calls | Cost |
| --- | --- | --- | --- |
| **Citation Faithfulness** | Are sources listed in the report's `## References` actually cited in the body? (catches decorative refs) | 0 | $0 |
| **Source Diversity** | Domain variety via ratio + Shannon entropy | 0 | $0 |
| **Source Authority** | Heuristic score per domain (.gov=1.0 → .com=0.5); unknown domains optionally LLM-scored | 0–1 | $0–$0.01 |
| **Subtopic Coverage** | LLM-judged coverage of expected subtopics (adaptive count) | 2 | ~$0.02/query |
| **Hallucination** | Binary faithfulness check — report vs. scraped sources | 1 | ~$0.01/query |
| **Unsupported Claim Rate** | Claim-level credibility: supported (1.0) / inferred (0.3–0.9) / unsupported (0.0) | 2 | ~$0.02/query |

**Citation Faithfulness** measures whether sources the report *lists* in its `## References` are *actually cited* in the body (a low score flags decorative references). It deliberately does not reward raw coverage — reading many sources and citing only the useful ones is good practice, like a real researcher.

**Unsupported Claim Rate** distinguishes between:

- `supported` — claim directly found in source text (score 1.0)
- `inferred` — reasonable synthesis from multiple sources; never applied to data claims (score 0.3–0.9)
- `unsupported` — no traceable basis in sources (score 0.0)

### Metric Grouping & Tooling

The metrics group into three families: **Source Quality** (diversity, authority), **Writing Behavior** (citation faithfulness, subtopic coverage), and **Hallucination** (hallucination check, unsupported claim) — i.e. *is the input good*, *how was it written*, *is it correct*.

Two tools complement `run_eval.py` (shared metric logic lives in `metrics.py`):

- **`benchmark.py`** — runs multiple researcher configurations (single- vs. multi-agent × model) over a fixed topic set and prints a side-by-side table. `--compare LOG_A LOG_B` diffs two past runs; `--summary-only` re-prints from saved logs.
- **`perturbation.py`** — a behavioral test that deliberately degrades a report (remove inline citations, swap sources to low-authority, corrupt claims) and checks each metric responds monotonically. This validates metric *reliability* (directional sensitivity), which is separate from whether a metric captures *quality*.

### Running

```bash
# Run all 6 metrics (most expensive, ~$0.06/query)
python -m evals.quality_eval.run_eval --num_examples 5

# Zero-cost only (citation ratio, diversity, authority)
python -m evals.quality_eval.run_eval --num_examples 10 --no-subtopic --no-hallucination --no-unsupported-claim

# Skip individual LLM metrics selectively
python -m evals.quality_eval.run_eval --num_examples 10 --no-subtopic
python -m evals.quality_eval.run_eval --num_examples 10 --no-hallucination
python -m evals.quality_eval.run_eval --num_examples 10 --no-unsupported-claim
```

Logs are saved to `evals/quality_eval/logs/quality_eval_YYYY-MM-DD_HH-MM-SS_n{N}.jsonl`.

### Example Output

```text
Quality eval: 5 queries  subtopic=off  hallucination=off  unsupported_claim=on

>> Query: What legal frameworks govern cross-border data transfers?
   citation_faithful:       0.95  (1 listed-only)
   diversity_ratio:         1.00  entropy=4.32
   authority_score:         0.62
   avg_claim_score:         0.79  (unsupported=0.11  inferred=0.22  n=9)
   latency=37.2s  cost=$0.13

=== QUALITY EVAL SUMMARY ===
  avg_citation_faithfulness: 0.94
  avg_diversity_ratio: 0.796
  avg_domain_entropy: 3.525
  avg_authority_score: 0.597
  avg_claim_score: 0.428
  avg_unsupported_claim_rate: 0.535
  avg_inferred_claim_rate: 0.148
  avg_latency_seconds: 33.6
  avg_cost: 0.116
```

### Dependencies

```bash
pip install langchain-openai python-dotenv

# Hallucination metric only:
pip install judges
```

Environment variables required: `OPENAI_API_KEY`, `TAVILY_API_KEY`.

---

## Report Generator (`report_generator/`)

Runs GPT-Researcher on one or more queries and saves each report as a timestamped Markdown file — useful for manual review and quality spot-checks.

```bash
# Single query
python -m evals.report_generator.run --query "What caused the 2008 financial crisis?"

# Batch from JSONL file (limit to 3)
python -m evals.report_generator.run --file evals/report_generator/queries.jsonl --limit 3
```

Reports are saved to `evals/report_generator/outputs/` (git-ignored).

---

## Hallucination Evaluation (`hallucination_eval/`)

The `hallucination_eval` directory contains tools for evaluating GPT-Researcher's outputs for hallucination. This evaluation system compares the generated research reports against their source materials to detect non-factual or hallucinated content, ensuring the reliability and accuracy of the research outputs.

### Components

- `run_eval.py`: Script to execute evaluations against GPT-Researcher
- `evaluate.py`: Core evaluation logic for detecting hallucinations
- `inputs/`: Directory containing test queries
  - `search_queries.jsonl`: Collection of research queries for evaluation
- `results/`: Directory containing evaluation results
  - `evaluation_records.jsonl`: Detailed per-query evaluation records
  - `aggregate_results.json`: Summary metrics across all evaluations

### Features

- Evaluates research reports against source materials
- Provides detailed reasoning for hallucination detection

### Running Evaluations

1. Install dependencies:
```bash
cd evals/hallucination_eval
pip install -r requirements.txt
```

2. Set up environment variables in `.env` file:
```bash
# Use the root .env file
OPENAI_API_KEY=your_openai_key_here
TAVILY_API_KEY=your_tavily_key_here
```

3. Run evaluation:
```bash
python run_eval.py -n <number_of_queries>
```

The `-n` parameter determines how many queries to evaluate from the test set (default: 1).

### Sample Result

```json
{
  "total_queries": 1,
  "successful_queries": 1,
  "total_responses": 1,
  "total_evaluated": 1,
  "total_hallucinated": 0,
  "hallucination_rate": 0.0,
  "results": [
    {
      "input": "What are the latest developments in quantum computing?",
      "output": "Research report content...",
      "source": "Source material content...",
      "is_hallucination": false,
      "confidence_score": 0.95,
      "reasoning": "The summary accurately reflects the source material with proper citations..."
    }
  ]
}
```
