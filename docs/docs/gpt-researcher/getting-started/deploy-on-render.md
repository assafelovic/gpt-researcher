# Deploy on Render

You can deploy GPT Researcher to [Render](https://render.com) with the `render.yaml` Blueprint in the root of the repository.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/assafelovic/gpt-researcher)

## What the Blueprint creates

The Blueprint creates one Python web service. The service installs the packages in `requirements.txt` and runs the FastAPI server, which also serves the web UI.

## Steps

1. Click **Deploy to Render**. To deploy your own fork, replace the `repo` value in the button URL with the URL of your fork.
2. Enter the two required secrets:
   - `OPENAI_API_KEY`: get a key from the [OpenAI dashboard](https://platform.openai.com/api-keys).
   - `TAVILY_API_KEY`: get a key from the [Tavily dashboard](https://app.tavily.com).
3. Click **Deploy Blueprint**.
4. When the deploy is live, open the service URL and run a research query.

To add more settings, such as a different LLM provider or retriever, go to the service's **Environment** page in the Render Dashboard. See [Configuration](/docs/gpt-researcher/gptr/config) for the list of variables.

## Notes

- The native Python runtime does not include a browser. Use the default Tavily retriever and the default `bs` scraper. Do not set `SCRAPER=selenium`.
- The Blueprint uses the `starter` instance type. For memory-heavy work, such as Deep Research, change the instance type to `standard` in the Render Dashboard.
