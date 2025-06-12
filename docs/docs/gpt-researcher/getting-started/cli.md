# Run with CLI

This command-line interface (CLI) tool allows you to generate research reports using the GPTResearcher class. It provides an easy way to conduct research on various topics and generate different types of reports.

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/gpt-researcher.git
   cd gpt-researcher
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your environment variables:
   Create a `.env` file in the project root and add your API keys or other necessary configurations.

## Usage

The basic syntax for using the CLI is:

```
python cli.py "<query>" --report_type <report_type> [--tone <tone>]
```

### Arguments

- `query` (required): The research query you want to investigate.
- `--report_type` (required): The type of report to generate. Options include:
  - `research_report`: Summary - Short and fast (~2 min)
  - `detailed_report`: Detailed - In depth and longer (~5 min)
  - `resource_report`
  - `outline_report`
  - `custom_report`
  - `subtopic_report`
- `--tone` (optional): The tone of the report. Defaults to 'objective'. Options include:
  - `objective`: Impartial and unbiased presentation
  - `formal`: Academic standards with sophisticated language
  - `analytical`: Critical evaluation and examination
  - `persuasive`: Convincing viewpoint
  - `informative`: Clear and comprehensive information
  - `explanatory`: Clarifying complex concepts
  - `descriptive`: Detailed depiction
  - `critical`: Judging validity and relevance
  - `comparative`: Juxtaposing different theories
  - `speculative`: Exploring hypotheses
  - `reflective`: Personal insights
  - `narrative`: Story-based presentation
  - `humorous`: Light-hearted and engaging
  - `optimistic`: Highlighting positive aspects
  - `pessimistic`: Focusing on challenges

## Examples

1. Generate a quick research report on climate change:
   ```
   python cli.py "What are the main causes of climate change?" --report_type research_report
   ```

2. Create a detailed report on artificial intelligence with an analytical tone:
   ```
   python cli.py "The impact of artificial intelligence on job markets" --report_type detailed_report --tone analytical
   ```

3. Generate an outline report on renewable energy with a persuasive tone:
   ```
   python cli.py "Renewable energy sources and their potential" --report_type outline_report --tone persuasive
   ```

## Output

The generated report will be saved as a Markdown file in the `outputs` directory. The filename will be a unique UUID.

## Note

- The execution time may vary depending on the complexity of the query and the type of report requested.
- Make sure you have the necessary API keys and permissions set up in your `.env` file for the tool to function correctly.
- All tone options should be provided in lowercase.