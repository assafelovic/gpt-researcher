# GPT-Researcher Evaluations

This directory contains evaluation tools and frameworks for assessing the performance of GPT-Researcher across different research tasks.

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

The `logs/` directory contains detailed evaluation run histories that are preserved in version control:

- Format: `SimpleQA Eval {num_problems} Problems {date}.txt`
- Example: `SimpleQA Eval 100 Problems 2-22-25.txt`

These logs provide historical performance data and are crucial for:
- Tracking performance improvements over time
- Debugging evaluation issues
- Comparing results across different versions
- Maintaining transparency in our evaluation process

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

- Accuracy rate
- F1 score
- Cost per query
- Success/failure rates
- Answer attempt rates
- Source coverage

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

The evaluation provides detailed metrics including:
- Per-query results with sources and costs
- Aggregate metrics (accuracy, F1 score)
- Total and average costs
- Success/failure counts
- Detailed grading breakdowns

### Example Output
```
=== Evaluation Summary ===
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

Total cost: $1.2345
Average cost per query: $0.1371
``` 

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

### Example Output
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
