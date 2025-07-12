# Scrapy Scraper for GPT Researcher

This module implements a Scrapy-based web scraper for the GPT Researcher project. It provides an alternative scraping method that leverages the powerful Scrapy framework for web crawling and data extraction.

## Features

- Uses Scrapy's robust crawling capabilities
- Extracts content, images, and titles from web pages
- Handles relative URLs for images
- Optimized for maximum speed and data quality

## Dependencies

This scraper requires the Scrapy package, which will be automatically installed if not present when the scraper is used.

## Implementation Details

The Scrapy scraper uses a temporary file to store the scraped data between the Scrapy process and the main application. It implements a custom Scrapy spider that extracts content from common content containers on web pages, falling back to the entire body content if specific containers are not found.

The implementation uses aggressive settings optimized for speed and data quality:

- Maximizes concurrent requests (16 concurrent requests, 8 per domain)
- No delay between requests for maximum speed
- Aggressive retry policy for failed requests (5 retries)
- Extended timeout (60 seconds) for content-heavy pages
- Disabled auto-throttling for maximum throughput
- Optimized request prioritization and queuing
- Compression enabled for faster downloads
- Extended URL length limits and redirect handling
