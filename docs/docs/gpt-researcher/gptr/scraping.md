# Scraping Options

GPT Researcher now offers two methods for web scraping: static scraping with BeautifulSoup and dynamic scraping with Selenium. This document explains how to switch between these methods and the benefits of each approach.

## Configuring Scraping Method

You can choose your preferred scraping method by setting the `SCRAPER` environment variable:

1. For BeautifulSoup (static scraping):
   ```
   export SCRAPER="bs"
   ```

2. For Selenium (dynamic browser scraping):
   ```
   export SCRAPER="browser"
   ```

Note: If not set, GPT Researcher will default to BeautifulSoup for scraping.

## Scraping Methods Explained

### BeautifulSoup (Static Scraping)

When `SCRAPER="bs"`, GPT Researcher uses BeautifulSoup for static scraping. This method:

- Sends a single HTTP request to fetch the page content
- Parses the static HTML content
- Extracts text and data from the parsed HTML

Benefits:
- Faster and more lightweight
- Doesn't require additional setup
- Works well for simple, static websites

Limitations:
- Cannot handle dynamic content loaded by JavaScript
- May miss content that requires user interaction to display

### Selenium (Browser Scraping)

When `SCRAPER="browser"`, GPT Researcher uses Selenium for dynamic scraping. This method:

- Opens a real browser instance (Chrome by default)
- Loads the page and executes JavaScript
- Waits for dynamic content to load
- Extracts text and data from the fully rendered page

Benefits:
- Can scrape dynamically loaded content
- Simulates real user interactions (scrolling, clicking, etc.)
- Works well for complex, JavaScript-heavy websites

Limitations:
- Slower than static scraping
- Requires more system resources
- Requires additional setup (Selenium and WebDriver installation)

## Additional Setup for Selenium

If you choose to use Selenium (SCRAPER="browser"), you'll need to:

1. Install the Selenium package:
   ```
   pip install selenium
   ```

2. Download the appropriate WebDriver for your browser:
   - For Chrome: [ChromeDriver](https://sites.google.com/a/chromium.org/chromedriver/downloads)
   - For Firefox: [GeckoDriver](https://github.com/mozilla/geckodriver/releases)
   - For Safari: Built-in, no download required

   Ensure the WebDriver is in your system's PATH.

## Choosing the Right Method

- Use BeautifulSoup (static) for:
  - Simple websites with mostly static content
  - Scenarios where speed is a priority
  - When you don't need to interact with the page

- Use Selenium (dynamic) for:
  - Websites with content loaded via JavaScript
  - Sites that require scrolling or clicking to load more content
  - When you need to simulate user interactions

## Troubleshooting

- If Selenium fails to start, ensure you have the correct WebDriver installed and it's in your system's PATH.
- If you encounter an `ImportError` related to Selenium, make sure you've installed the Selenium package.
- If the scraper misses expected content, try switching between static and dynamic scraping to see which works better for your target website.

Remember, the choice between static and dynamic scraping can significantly impact the quality and completeness of the data GPT Researcher can gather. Choose the method that best suits your research needs and the websites you're targeting.