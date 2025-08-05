# 1A_Experiment - GPT Researcher Scraping Experiments

This directory contains experimental code, tests, and comparison results for different web scraping approaches used in the GPT Researcher project. The primary focus is on comparing and evaluating Firecrawl scraping against traditional HTML downloading methods for improved content extraction and research capabilities.

## Overview

The experiments in this folder test various scraping methods to optimize how GPT Researcher gathers and processes web content. The main comparison is between:

1. **Firecrawl Downloader** - A specialized scraping tool integrated with GPT Researcher
2. **Standard HTML Downloader** - Traditional HTML-based web scraping methods

## Directory Structure

- **`1A_DPO_Firecrawl_vs_HTML/`** - Contains comparison results between Firecrawl and HTML downloaders
- **`1A_Firecrawl_scraped_content_results/`** - Stores raw results from Firecrawl scraping tests
- **`1A_ScraperFirecrawl_ExpRes/`** - Experimental results from GPTR Firecrawl scraper tests
- **`1A_Tone_ExpRes/`** - Tone analysis experiments on scraped content
- **`1A_md_ReportRes/`** - Markdown report results generated from scraped content
- **`downloader_firecrawldownloader/`** - Firecrawl downloader  outputs
- **`downloader_htmldownloader/`** - HTML downloader outputs
- **`ztest_attachdocs/`** - Test documents used for attachment processing experiments

## Scripts

The key scripts in this directory include:

- **`z_testFirecrawl.py`** - Test script for the GPTR FireCrawl scraping module with detailed debugging
- **`z_dpoFirecrawl.py`** - Code to run DPO FireCrawl downloader 
- **`z_dpoHTML.py`** - Code to run DPO HTML downloader 
- **`z_dbExp.py`** - Code to run GPT Researcher Deep Research with Resource Monitoring which is used to experiment with the deep and breadth

## Usage

To run the Firecrawl that is not from DPO for scraping test:

```bash
python z_testFirecrawl.py
```

To compare Firecrawl and HTML downloaders from DPO:

```bash
python z_dpoFirecrawl.py
python z_dpoHTML.py
```

## Environment Setup

These experiments require environment variables to be set, particularly:
- GL SDK for DPO HTML Scrapper and Firecrawl Scrapper 
- `FIRECRAWL_API_KEY` - API key for the Firecrawl service

The scripts use dotenv for loading environment variables, so you can create a `.env` file in the project root with your API keys.

## Experiment Results

The experiment results demonstrate the differences between Firecrawl and traditional HTML downloaders in several dimensions:

1. Content extraction quality
2. Handling of dynamic content
3. Structure preservation
4. Metadata extraction
5. Processing efficiency

Detailed comparison results can be found in the corresponding result directories.

## Integration with GPT Researcher

These experiments contribute to improving the scraping capabilities of the [GPT Researcher](https://github.com/assafelovic/gpt-researcher) project by identifying the most effective methods for web content extraction and processing.

## Notes

- Scripts prefixed with `z_` are experimental and may not be part of the main GPT Researcher workflow
- Some experiments may require specific API keys or credentials to run successfully
- The experimental results in this directory are meant for research and development purposes