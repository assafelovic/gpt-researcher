from __future__ import annotations

from typing import Any

from colorama import Fore, Style

from gpt_researcher.config.config import Config
from gpt_researcher.config.variables.default import DEFAULT_CONFIG
from gpt_researcher.scraper import Scraper
from gpt_researcher.utils.logger import get_formatted_logger

logger = get_formatted_logger()


def scrape_urls(
    urls: list[str],
    cfg: Config | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Scrape the urls.

    Args:
        urls (list[str]): List of urls.
        cfg (Config, optional): Config.

    Returns:
        tuple[list[dict[str, Any]], list[dict[str, Any]]]: Tuple containing scraped content and images.
    """
    scraped_data: list[dict[str, Any]] = []
    images: list[dict[str, Any]] = []
    user_agent: str = (
        DEFAULT_CONFIG["USER_AGENT"]
        if cfg is None
        else cfg.user_agent  # pyright: ignore[reportAttributeAccessIssue]
    )

    try:
        scraper_type: str = (
            DEFAULT_CONFIG["SCRAPER"]
            if cfg is None
            else cfg.scraper  # pyright: ignore[reportAttributeAccessIssue]
        )
        scraper: Scraper = Scraper(
            urls,
            user_agent,
            scraper_type,
        )
        scraped_data: list[dict[str, Any]] = scraper.run()
        images.extend(
            [
                image_url
                for item in scraped_data
                if "image_urls" in item
                for image_url in item["image_urls"]
            ]
        )
    except Exception as e:
        print(f"{Fore.RED}Error in scrape_urls: {e.__class__.__name__}: {e}{Style.RESET_ALL}")

    return scraped_data, images


async def filter_urls(urls: list[str], config: Config) -> list[str]:
    """Filter URLs based on configuration settings.

    Args:
        urls (list[str]): List of URLs to filter.
        config (Config): Configuration object.

    Returns:
        list[str]: Filtered list of URLs.
    """
    filtered_urls: list[str] = []
    for url in urls:
        # Add your filtering logic here
        # For example, you might want to exclude certain domains or URL patterns
        if not any(
            excluded in url
            for excluded in config.excluded_domains  # pyright: ignore[reportAttributeAccessIssue]
        ):
            filtered_urls.append(url)
    return filtered_urls


async def extract_main_content(html_content: str) -> str:
    """Extract the main content from HTML.

    Args:
        html_content (str): Raw HTML content.

    Returns:
        str: Extracted main content.
    """
    # Implement content extraction logic here
    # This could involve using libraries like BeautifulSoup or custom parsing logic
    # For now, we'll just return the raw HTML as a placeholder
    return html_content


async def process_scraped_data(
    scraped_data: list[dict[str, Any]],
    config: Config | None = None,
) -> list[dict[str, Any]]:
    """Process the scraped data to extract and clean the main content.

    Args:
        scraped_data (list[dict[str, Any]]): List of dictionaries containing scraped data.
        config (Config, optional): Configuration object.

    Returns:
        list[dict[str, Any]]: Processed scraped data.
    """
    processed_data: list[dict[str, Any]] = []
    for item in scraped_data:
        if item["status"] == "success":
            main_content: str = await extract_main_content(item["content"])
            processed_data.append(
                {
                    "url": item["url"],
                    "content": main_content,
                    "status": "success",
                }
            )
        else:
            processed_data.append(item)
    return processed_data
