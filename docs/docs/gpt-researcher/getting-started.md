# Getting Started
> **Step 0** - Install Python 3.11 or later. [See here](https://www.tutorialsteacher.com/python/install-python) for a step-by-step guide.

> **Step 1** - Download the project and navigate to its directory

```bash
$ git clone https://github.com/assafelovic/gpt-researcher.git
$ cd gpt-researcher
```

> **Step 3** - Set up API keys using two methods: exporting them directly or storing them in a `.env` file.

For Linux/Temporary Windows Setup, use the export method:

```bash
export OPENAI_API_KEY={Your OpenAI API Key here}
export TAVILY_API_KEY={Your Tavily API Key here}
```

For a more permanent setup, create a `.env` file in the current `gpt-researcher` folder and input the keys as follows:

```bash
OPENAI_API_KEY={Your OpenAI API Key here}
TAVILY_API_KEY={Your Tavily API Key here}
```

- **For LLM, we recommend [OpenAI GPT](https://platform.openai.com/docs/guides/gpt)**, but you can use any other LLM model (including open sources) supported by [Langchain Adapter](https://python.langchain.com/docs/guides/adapters/openai), simply change the llm model and provider in config/config.py. 
- **For search engine, we recommend [Tavily Search API](https://app.tavily.com)**, but you can also refer to other search engines of your choice by changing the search provider in config/config.py to `"duckduckgo"`, `"googleAPI"`, `"bing"`, `"googleSerp"`, or `"searx"`. Then add the corresponding env API key as seen in the config.py file.

## Quickstart

> **Step 1** - Install dependencies

```bash
$ pip install -r requirements.txt
```

> **Step 2** - Run the agent with FastAPI

```bash
$ uvicorn main:app --reload
```

> **Step 3** - Go to http://localhost:8000 on any browser and enjoy researching!

## Using Virtual Environment or Poetry
Select either based on your familiarity with each:

### Virtual Environment

#### *Establishing the Virtual Environment with Activate/Deactivate configuration*

Create a virtual environment using the `venv` package with the environment name `<your_name>`, for example, `env`. Execute the following command in the PowerShell/CMD terminal:

```bash
python -m venv env
```

To activate the virtual environment, use the following activation script in PowerShell/CMD terminal:

```bash
.\env\Scripts\activate
```

To deactivate the virtual environment, run the following deactivation script in PowerShell/CMD terminal:

```bash
deactivate
```

#### *Install the dependencies for a Virtual environment*

After activating the `env` environment, install dependencies using the `requirements.txt` file with the following command:

```bash
python -m pip install -r requirements.txt
```

<br />

### Poetry

#### *Establishing the Poetry dependencies and virtual environment with Poetry version `~1.7.1`*

Install project dependencies and simultaneously create a virtual environment for the specified project. By executing this command, Poetry reads the project's "pyproject.toml" file to determine the required dependencies and their versions, ensuring a consistent and isolated development environment. The virtual environment allows for a clean separation of project-specific dependencies, preventing conflicts with system-wide packages and enabling more straightforward dependency management throughout the project's lifecycle.

```bash
poetry install
```

#### *Activate the virtual environment associated with a Poetry project*

By running this command, the user enters a shell session within the isolated environment associated with the project, providing a dedicated space for development and execution. This virtual environment ensures that the project dependencies are encapsulated, avoiding conflicts with system-wide packages. Activating the Poetry shell is essential for seamlessly working on a project, as it ensures that the correct versions of dependencies are used and provides a controlled environment conducive to efficient development and testing.

```bash
poetry shell
```

### *Run the app*
> Launch the FastAPI application agent on a *Virtual Environment or Poetry* setup by executing the following command:
```bash
python -m uvicorn main:app --reload
```
> Visit http://localhost:8000 in any web browser and explore your research!

<br />


## Try it with Docker

> **Step 1** - Install Docker

Follow instructions at https://docs.docker.com/engine/install/

> **Step 2** - Create .env file with your OpenAI Key or simply export it

```bash
$ export OPENAI_API_KEY={Your API Key here}
$ export TAVILY_API_KEY={Your Tavily API Key here}
```

> **Step 3** - Run the application

```bash
$ docker-compose up
```

> **Step 4** - Go to http://localhost:8000 on any browser and enjoy researching!
