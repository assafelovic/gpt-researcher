from __future__ import annotations

from typing import TYPE_CHECKING, Any

from gpt_researcher.config.config import Config
from gpt_researcher.scraper.scraper import Scraper
from gpt_researcher.utils.logger import get_formatted_logger

if TYPE_CHECKING:
    import logging

    from gpt_researcher.config.config import Config
    from gpt_researcher.utils.workers import WorkerPool

logger: logging.Logger = get_formatted_logger()


async def scrape_urls(
    urls: list[str],
    cfg: Config,
    worker_pool: WorkerPool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Scrapes the urls.

    Args:
        urls: List of urls
        research_config: Config (optional).

    Returns:
        tuple[list[dict[str, Any]], list[dict[str, Any]]]: tuple containing scraped content and images

    """
    scraped_data: list[dict[str, Any]] = []
    images: list[dict[str, Any]] = []
    user_agent: str = (
        cfg.USER_AGENT  # type: ignore[attr-defined]
        if cfg
        else "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    )

    try:
        scraper = Scraper(urls, user_agent, cfg.SCRAPER, worker_pool=worker_pool)
        scraped_data = await scraper.run()  # type: ignore[attr-defined]
        for item in scraped_data:
            if "image_urls" in item:
                images.extend([img for img in item["image_urls"]])
    except Exception as e:
        logger.exception(f"Error in scrape_urls: {e.__class__.__name__}: {e}")

    return scraped_data, images


async def filter_urls(
    urls: list[str],
    config: Config,
) -> list[str]:
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
        if not any(excluded.casefold() in url.casefold() for excluded in config.EXCLUDED_DOMAINS):
            filtered_urls.append(url)
    return filtered_urls
