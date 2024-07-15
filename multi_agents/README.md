# LangGraph x GPT Researcher
[LangGraph](https://python.langchain.com/docs/langgraph) is a library for building stateful, multi-actor applications with LLMs. 
This example uses Langgraph to automate the process of an in depth research on any given topic.

## Use case
By using Langgraph, the research process can be significantly improved in depth and quality by leveraging multiple agents with specialized skills. 
Inspired by the recent [STORM](https://arxiv.org/abs/2402.14207) paper, this example showcases how a team of AI agents can work together to conduct research on a given topic, from planning to publication.

An average run generates a 5-6 page research report in multiple formats such as PDF, Docx and Markdown.

Please note: This example uses the OpenAI API only for optimized performance.

## The Multi Agent Team
The research team is made up of 7 AI agents:
- **Chief Editor** - Oversees the research process and manages the team. This is the "master" agent that coordinates the other agents using Langgraph.
- **Researcher** (gpt-researcher) - A specialized autonomous agent that conducts in depth research on a given topic.
- **Editor** - Responsible for planning the research outline and structure.
- **Reviewer** - Validates the correctness of the research results given a set of criteria.
- **Revisor** - Revises the research results based on the feedback from the reviewer.
- **Writer** - Responsible for compiling and writing the final report.
- **Publisher** - Responsible for publishing the final report in various formats.

## How it works
Generally, the process is based on the following stages: 
1. Planning stage
2. Data collection and analysis
3. Review and revision
4. Writing and submission
5. Publication

### Architecture
<div align="center">
<img align="center" height="600" src="https://cowriter-images.s3.amazonaws.com/gptr-langgraph-architecture.png">
</div>
<br clear="all"/>

### Steps
More specifically (as seen in the architecture diagram) the process is as follows:
- Browser (gpt-researcher) - Browses the internet for initial research based on the given research task.
- Editor - Plans the report outline and structure based on the initial research.
- For each outline topic (in parallel):
  - Researcher (gpt-researcher) - Runs an in depth research on the subtopics and writes a draft.
  - Reviewer - Validates the correctness of the draft given a set of criteria and provides feedback.
  - Revisor - Revises the draft until it is satisfactory based on the reviewer feedback.
- Writer - Compiles and writes the final report including an introduction, conclusion and references section from the given research findings.
- Publisher - Publishes the final report to multi formats such as PDF, Docx, Markdown, etc.

## How to run
1. Install required packages:
    ```bash
    pip install -r requirements.txt
    ```
3. Update env variables
   ```bash
   export OPENAI_API_KEY={Your OpenAI API Key here}
   export TAVILY_API_KEY={Your Tavily API Key here}
   ```
2. Run the application:
    ```bash
    python main.py
    ```

## Usage
To change the research query and customize the report, edit the `task.json` file in the main directory.
#### Task.json contains the following fields:
- `query` - The research query or task.
- `model` - The OpenAI LLM to use for the agents.
- `max_sections` - The maximum number of sections in the report. Each section is a subtopic of the research query.
- `publish_formats` - The formats to publish the report in. The reports will be written in the `output` directory.
- `source` - The location from which to conduct the research. Options: `web` or `local`. For local, please add `DOC_PATH` env var.
- `follow_guidelines` - If true, the research report will follow the guidelines below. It will take longer to complete. If false, the report will be generated faster but may not follow the guidelines.
- `guidelines` - A list of guidelines that the report must follow.
- `verbose` - If true, the application will print detailed logs to the console.

#### For example:
```json
{
  "query": "Is AI in a hype cycle?",
  "model": "gpt-4o",
  "max_sections": 3, 
  "publish_formats": { 
    "markdown": true,
    "pdf": true,
    "docx": true
  },
  "source": "web",
  "follow_guidelines": true,
  "guidelines": [
    "The report MUST fully answer the original question",
    "The report MUST be written in apa format",
    "The report MUST be written in english"
  ],
  "verbose": true
}
```

## To Deploy

```shell
pip install langgraph-cli
langgraph up
```

From there, see documentation [here](https://github.com/langchain-ai/langgraph-example) on how to use the streaming and async endpoints, as well as the playground.

## NextJS Frontend App

The React app (located in `frontend` directory) is our Frontend 2.0 which we hope will enable us to display the robustness of the backend on the frontend, as well.

It comes with loads of added features, such as: 
 - a drag-n-drop user interface for uploading and deleting files to be used as local documents by GPTResearcher.
 - a GUI for setting your GPTR environment variables.
 - the ability to trigger the multi_agents flow via the Backend Module or Langgraph Cloud Host (currently in closed beta).
 - stability fixes
 - and more coming soon!

### Run the NextJS React App with Docker

> **Step 1** - [Install Docker](https://docs.gptr.dev/docs/gpt-researcher/getting-started#try-it-with-docker)

> **Step 2** - Clone the '.env.example' file, add your API Keys to the cloned file and save the file as '.env'

> **Step 3** - Within the docker-compose file comment out services that you don't want to run with Docker.

```bash
$ docker-compose up --build
```

> **Step 4** - By default, if you haven't uncommented anything in your docker-compose file, this flow will start 2 processes:
 - the Python server running on localhost:8000<br>
 - the React app running on localhost:3000<br>

Visit localhost:3000 on any browser and enjoy researching!


### Run the NextJS React App with NPM

```bash
cd frontend
nvm install 18.17.0
nvm use v18.17.0
npm install --legacy-peer-deps
npm run dev
```