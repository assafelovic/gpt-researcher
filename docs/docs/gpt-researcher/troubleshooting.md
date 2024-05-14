# Troubleshooting
We're constantly working to provide a more stable version. If you're running into any issues, please first check out the resolved issues or ask us via our [Discord community](https://discord.gg/2pFkc83fRq).

**model: gpt-4 does not exist**
This relates to not having permission to use gpt-4 yet. Based on OpenAI, it will be [widely available for all by end of July](https://help.openai.com/en/articles/7102672-how-can-i-access-gpt-4).

**cannot load library 'gobject-2.0-0'**

The issue relates to the library WeasyPrint (which is used to generate PDFs from the research report). Please follow this guide to resolve it: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html

Or you can install this package manually

In case of MacOS you can install this lib using
`brew install glib gobject-introspection`

In case of Linux you can install this lib using
`sudo apt install libglib2.0-dev`

**cannot load library 'pango'**

In case of MacOS you can install this lib using
`brew install pango`

In case of Linux you can install this lib using
`sudo apt install libpango-1.0-0`

**cannot load library 'gobject-2.0-0'**

**Error processing the url**

We're using [Selenium](https://www.selenium.dev) for site scraping. Some sites fail to be scraped. In these cases, restart and try running again.


**Chrome version issues**

Many users have an issue with their chromedriver because the latest chrome browser version doesn't have a compatible chrome driver yet.

To downgrade your Chrome web browser using [slimjet](https://www.slimjet.com/chrome/google-chrome-old-version.php), follow these steps. First, visit the website and scroll down to find the list of available older Chrome versions. Choose the version you wish to install
making sure it's compatible with your operating system.
Once you've selected the desired version, click on the corresponding link to download the installer. Before proceeding with the installation, it's crucial to uninstall your current version of Chrome to avoid conflicts.

It's important to check if the version you downgrade to, has a chromedriver available in the official [chrome driver website](https://chromedriver.chromium.org/downloads)

**If none of the above work, you can [try out our hosted beta](https://app.tavily.com)**