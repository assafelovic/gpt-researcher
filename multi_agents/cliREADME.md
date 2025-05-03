# Multi-Agent CLI

This is a command-line interface for running multi-agent research tasks. It allows you to configure research tasks using JSON files and specify the output format.

## Usage

```bash
python -m multi_agents.main [OPTIONS]
```
cli
## Options

*   `-t`, `--config-file`: Path to a single JSON configuration file. This file will override the default `task.json`.
*   `--config-files`: Paths to one or more JSON configuration files. These files will be merged with the default `task.json`, with later files overriding earlier ones in case of key conflicts.
*   `--query-file`: Path to a file containing the research query. The file can contain either a JSON object with a "query" key or plain text.
*   `-o`, `--output-file`: Path to write the research report. The file extension (`.md`, `.pdf`, or `.docx`) will determine the output format.

## Configuration

The CLI uses a default configuration defined in `task.json`. You can override this configuration by providing one or more custom configuration files using the `--config-file` or `--config-files` options.

The `task.json` file contains various settings for the research task, such as the research query, desired report format, and agent configurations.

## Examples

1.  Run a research task with the default configuration:

    ```bash
    python -m multi_agents.main
    ```

2.  Run a research task with a custom configuration file:

    ```bash
    python -m multi_agents.main -t custom_config.json
    ```

3.  Run a research task with multiple custom configuration files:

    ```bash
    python -m multi_agents.main --config-files config1.json config2.json
    ```

4.  Run a research task with a query from a file and save the output as a Markdown file:

    ```bash
    python -m multi_agents.main --query-file my_query.txt -o report.md
    ```

5.  Run a research task with a JSON query file and save the output as a PDF file:

    ```bash
    python -m multi_agents.main --query-file my_query.json -o report.pdf
