import asyncio
from playwright.async_api import async_playwright
from ..utils import get_relevant_images, extract_title, get_text_from_soup, clean_soup
from bs4 import BeautifulSoup
import logging

class PlaywrightScraper:
    """
    Playwright-based scraper for modern web scraping with JavaScript support
    """
    
    def __init__(self, link, session=None):
        self.link = link
        self.session = session  # Not used but kept for compatibility
        self.logger = logging.getLogger(__name__)
    
    def scrape(self):
        """
        Synchronous scrape method that runs the async version
        """
        try:
            # Check if we're already in an event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, we need to run in a new thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.scrape_async())
                    return future.result()
            else:
                return asyncio.run(self.scrape_async())
        except Exception as e:
            self.logger.error(f"Playwright sync scraper error for {self.link}: {str(e)}")
            return "", [], ""
    
    async def scrape_async(self):
        """
        Async scraping using Playwright
        """
        try:
            async with async_playwright() as p:
                # Launch browser (headless by default)
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--no-first-run',
                        '--no-zygote',
                        '--disable-gpu'
                    ]
                )
                
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080}
                )
                
                page = await context.new_page()
                
                # Set timeouts
                page.set_default_timeout(30000)  # 30 seconds
                page.set_default_navigation_timeout(30000)
                
                # Navigate to the page
                self.logger.info(f"Navigating to {self.link}")
                await page.goto(self.link, wait_until="domcontentloaded")
                
                # Wait for any dynamic content to load
                await page.wait_for_timeout(3000)  # Wait 3 seconds for JS to execute
                
                # Try to wait for main content (optional - adapt selectors as needed)
                try:
                    await page.wait_for_selector('body', timeout=5000)
                except:
                    pass  # Continue if selector not found
                
                # Get page content and title
                html_content = await page.content()
                title = await page.title()
                
                # Close browser
                await browser.close()
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(html_content, "lxml")
                
                # Remove unwanted elements before cleaning
                self._remove_unwanted_elements(soup)
                
                # Clean soup using existing utility
                soup = clean_soup(soup)
                
                # Extract content
                content = get_text_from_soup(soup)
                
                # Get images
                image_urls = get_relevant_images(soup, self.link)
                
                # Use extracted title or fallback to soup extraction
                if not title or title.strip() == "":
                    title = extract_title(soup)
                
                self.logger.info(f"Playwright scraper extracted {len(content)} characters from {self.link}")
                
                return content, image_urls, title
                
        except Exception as e:
            self.logger.error(f"Playwright scraper error for {self.link}: {str(e)}")
            return "", [], ""
    
    def _remove_unwanted_elements(self, soup):
        """Remove unwanted elements like ads, navigation, etc."""
        unwanted_selectors = [
            'script', 'style', 'noscript',
            'nav', 'footer', 'aside', 'header',
            '[class*="nav"]', '[class*="menu"]',
            '[class*="ad"]', '[class*="advertisement"]',
            '[class*="social"]', '[class*="share"]',
            '[class*="cookie"]', '[class*="popup"]',
            '[class*="banner"]', '[class*="sidebar"]',
            '[id*="nav"]', '[id*="menu"]',
            '[id*="sidebar"]', '[id*="footer"]'
        ]
        
        for selector in unwanted_selectors:
            try:
                for element in soup.select(selector):
                    element.decompose()
            except:
                continue  # Continue if selector fails