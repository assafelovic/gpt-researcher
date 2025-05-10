#!/usr/bin/env python
"""
Example MCP server for GPT Researcher

This is a simple MCP server that demonstrates how to create a custom
data source that can be used with GPT Researcher.

To use this with GPT Researcher:
    
    RETRIEVER=mcp python -m gpt_researcher.main \
      --query "your query" \
      --mcp_server_command python \
      --mcp_server_args "examples/mcp_server_example.py" \
      --mcp_tool_name "search"
"""

import argparse
import json
import logging
import sys
from typing import Dict, List, Optional, Any

try:
    from mcp.server.fastmcp import FastMCP, Image
    HAS_MCP = True
except ImportError:
    HAS_MCP = False
    print("MCP package not installed. Install with 'pip install mcp'")
    sys.exit(1)

# Sample data for our MCP server
SAMPLE_DATA = {
    "ai": [
        {
            "title": "GPT-4: A Comprehensive Guide",
            "content": "GPT-4 is a large multimodal model that can accept image and text inputs and produce text outputs. It exhibits human-level performance on various professional and academic benchmarks.",
            "url": "https://example.com/gpt4-guide"
        },
        {
            "title": "The History of Machine Learning",
            "content": "Machine learning has evolved significantly since its inception in the 1950s. From early pattern recognition systems to modern deep learning networks, the field has seen remarkable progress.",
            "url": "https://example.com/ml-history"
        },
        {
            "title": "Understanding Neural Networks",
            "content": "Neural networks are computing systems inspired by the biological neural networks in animal brains. They consist of layers of interconnected nodes or 'neurons' that process and transform data.",
            "url": "https://example.com/neural-networks"
        }
    ],
    "climate": [
        {
            "title": "Climate Change: Current Evidence",
            "content": "The Earth's climate has changed throughout history. The current warming trend is particularly significant because it is primarily the result of human activities since the mid-20th century.",
            "url": "https://example.com/climate-evidence"
        },
        {
            "title": "Renewable Energy Solutions",
            "content": "Renewable energy sources like solar, wind, and hydroelectric power are critical for reducing greenhouse gas emissions and mitigating climate change impacts.",
            "url": "https://example.com/renewable-energy"
        }
    ],
    "health": [
        {
            "title": "Understanding Nutrition Basics",
            "content": "Good nutrition is an important part of leading a healthy lifestyle. It involves consuming a variety of foods that give you the nutrients you need to maintain your health.",
            "url": "https://example.com/nutrition-basics"
        },
        {
            "title": "The Science of Sleep",
            "content": "Sleep is essential for health and wellbeing. During sleep, your body works to support healthy brain function and maintain physical health.",
            "url": "https://example.com/sleep-science"
        }
    ]
}

# Create the MCP server
mcp = FastMCP("GPTResearcherExampleServer")

@mcp.tool()
def search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Search for information based on the query.
    
    Args:
        query: The search query string
        max_results: Maximum number of results to return
        
    Returns:
        A list of search results with url and content fields
    """
    # Find the most relevant category for the query
    scores = {}
    for category, entries in SAMPLE_DATA.items():
        score = 0
        for word in query.lower().split():
            if word in category:
                score += 10
            for entry in entries:
                if word in entry["title"].lower() or word in entry["content"].lower():
                    score += 1
        scores[category] = score
    
    # Get the best matching categories
    sorted_categories = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    # Collect results from the best matching categories
    results = []
    for category, _ in sorted_categories:
        if len(results) >= max_results:
            break
        
        remaining = max_results - len(results)
        entries = SAMPLE_DATA[category][:remaining]
        
        for entry in entries:
            results.append({
                "href": entry["url"],  # GPT Researcher expects "href" for URLs
                "body": f"{entry['title']}\n\n{entry['content']}"  # GPT Researcher expects "body" for content
            })
    
    return results

@mcp.tool()
def list_categories() -> List[str]:
    """
    List all available categories in the database.
    
    Returns:
        A list of category names
    """
    return list(SAMPLE_DATA.keys())

@mcp.tool()
def get_category_info(category: str) -> List[Dict[str, str]]:
    """
    Get all information in a specific category.
    
    Args:
        category: The category name
        
    Returns:
        A list of entries in the category
    """
    if category not in SAMPLE_DATA:
        return [{"href": "error://category-not-found", "body": f"Category '{category}' not found"}]
    
    results = []
    for entry in SAMPLE_DATA[category]:
        results.append({
            "href": entry["url"],
            "body": f"{entry['title']}\n\n{entry['content']}"
        })
    
    return results

if __name__ == "__main__":
    # Run the MCP server
    mcp.run() 