# Troubleshooting

We're constantly working to provide a more stable version. If you're running into any issues, please first check out the resolved issues or ask us via our [Discord community](https://discord.gg/QgZXvJAccX).

### model: gpt-4 does not exist
This usually means that your OpenAI account does not have access to the specific `gpt-4` model name you are trying to use, or that the model has been deprecated/renamed.

GPT Researcher lets you fully control which models are used via the `FAST_LLM`, `SMART_LLM` and `STRATEGIC_LLM` environment variables.

If you see this error:

- Make sure your OpenAI account actually has access to the model name you configured.
- If not, change your `.env` to use models you *do* have access to, for example:

  ```env
  FAST_LLM=openai:gpt-4o-mini
  SMART_LLM=openai:gpt-4.1
  STRATEGIC_LLM=openai:o4-mini
  ```

You can find more details and provider-specific examples in the [LLM configuration guide](/docs/gpt-researcher/llms/llms).

### cannot load library 'gobject-2.0-0'

The issue relates to the library WeasyPrint (which is used to generate PDFs from the research report). Please follow this guide to resolve it: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html

Or you can install this package manually

In case of MacOS you can install this lib using
`brew install glib pango`

If you face an issue with linking afterward, you can try running `brew link glib`

In case of Linux you can install this lib using
`sudo apt install libglib2.0-dev`

### cannot load library 'pango'

In case of MacOS you can install this lib using
`brew install pango`

In case of Linux you can install this lib using
`sudo apt install libpango-1.0-0`

**Workaround for Mac M chip users**

If the above solutions don't work, you can try the following:
- Install a fresh version of Python 3.11 pointed to brew:
`brew install python@3.11`
- Install the required libraries:
`brew install pango glib gobject-introspection`
- Install the required GPT Researcher Python packages:
`pip3.11 install -r requirements.txt`
- Run the app with Python 3.11 (using brew):
`python3.11 -m uvicorn main:app --reload`

### Error processing the url

We're using [Selenium](https://www.selenium.dev) for site scraping. Some sites fail to be scraped. In these cases, restart and try running again.


### Chrome version issues

Many users have an issue with their chromedriver because the latest chrome browser version doesn't have a compatible chrome driver yet.

To downgrade your Chrome web browser using [slimjet](https://www.slimjet.com/chrome/google-chrome-old-version.php), follow these steps. First, visit the website and scroll down to find the list of available older Chrome versions. Choose the version you wish to install
making sure it's compatible with your operating system.
Once you've selected the desired version, click on the corresponding link to download the installer. Before proceeding with the installation, it's crucial to uninstall your current version of Chrome to avoid conflicts.

It's important to check if the version you downgrade to, has a chromedriver available in the official [chrome driver website](https://chromedriver.chromium.org/downloads)

**If none of the above work, you can [try out our hosted beta](https://app.tavily.com)**