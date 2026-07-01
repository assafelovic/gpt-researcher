#!/usr/bin/env python3
"""
GPT Researcher MCP Server - Enhanced Version

A comprehensive MCP server providing research, analysis, and reporting tools.
Includes stakeholder analysis, funding program matching, and document processing.

Author: GPT Researcher Team
License: MIT
"""

import asyncio
import json
import sys
import os
import re
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging

from mcp.server.stdio import stdio_server
from mcp.server import Server
from mcp.types import Tool, TextContent
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB max file size
MAX_FILES_PER_OPERATION = 100
DEFAULT_DOC_PATH = os.path.expanduser("~/documents")  # Cross-platform default
CHUNK_SIZE = 8000  # For API calls
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"

# Initialize MCP server
app = Server("gpt-researcher-mcp")

# Environment configuration
DOC_PATH = os.environ.get('DOC_PATH', DEFAULT_DOC_PATH)
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
OPENAI_BASE_URL = os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1')
TAVILY_API_KEY = os.environ.get('TAVILY_API_KEY')
STRATEGIC_LLM = os.environ.get('STRATEGIC_LLM', 'openai:gpt-4o')
SMART_LLM = os.environ.get('SMART_LLM', 'openai:gpt-4o')
FAST_LLM = os.environ.get('FAST_LLM', 'openai:gpt-3.5-turbo')


# ============================================================================
# SECURITY & VALIDATION UTILITIES
# ============================================================================

def validate_path(base_path: str, requested_path: str) -> Optional[Path]:
    """
    Validate that requested_path is within base_path to prevent path traversal.

    Args:
        base_path: The allowed base directory
        requested_path: The requested file path

    Returns:
        Validated Path object or None if invalid
    """
    try:
        base = Path(base_path).resolve()
        target = (base / requested_path).resolve()

        # Check if target is within base
        if base in target.parents or base == target:
            return target
        else:
            logger.warning(f"Path traversal attempt detected: {requested_path}")
            return None
    except Exception as e:
        logger.error(f"Path validation error: {e}")
        return None


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent security issues.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove path separators and dangerous characters
    filename = re.sub(r'[/\\]', '', filename)
    filename = re.sub(r'[<>:"|?*]', '', filename)
    # Limit length
    return filename[:255]


def check_file_size(file_path: Path, max_size: int = MAX_FILE_SIZE) -> bool:
    """
    Check if file size is within limits.

    Args:
        file_path: Path to file
        max_size: Maximum allowed size in bytes

    Returns:
        True if file is within size limit
    """
    try:
        return file_path.stat().st_size <= max_size
    except Exception:
        return False


# ============================================================================
# FILE OPERATIONS
# ============================================================================

def safe_read_file(file_path: Path, max_chars: int = 50000, encoding: str = 'utf-8') -> Tuple[str, Optional[str]]:
    """
    Safely read file content with size limits and error handling.

    Args:
        file_path: Path to file
        max_chars: Maximum characters to read
        encoding: File encoding

    Returns:
        Tuple of (content, error_message)
    """
    try:
        if not file_path.exists():
            return "", f"File not found: {file_path.name}"

        if not file_path.is_file():
            return "", f"Not a file: {file_path.name}"

        if not check_file_size(file_path):
            return "", f"File too large (max {MAX_FILE_SIZE} bytes): {file_path.name}"

        with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
            content = f.read(max_chars)

        return content, None
    except PermissionError:
        return "", f"Permission denied: {file_path.name}"
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return "", f"Error reading file: {str(e)}"


def extract_text_from_files(
    base_path: Path,
    pattern: str,
    max_files: int,
    max_chars_per_file: int
) -> Tuple[str, List[str]]:
    """
    Extract and combine text from multiple files safely.

    Args:
        base_path: Base directory to search
        pattern: File pattern to match
        max_files: Maximum number of files to process
        max_chars_per_file: Maximum characters per file

    Returns:
        Tuple of (combined_text, list_of_processed_files)
    """
    texts = []
    processed_files = []

    try:
        files = list(base_path.glob(pattern))[:max_files]

        for file_path in files:
            if file_path.is_file():
                content, error = safe_read_file(file_path, max_chars_per_file)
                if error:
                    logger.warning(f"Skipping file {file_path.name}: {error}")
                    continue

                texts.append(f"File: {file_path.name}\n{content}\n")
                processed_files.append(file_path.name)

        return "\n".join(texts), processed_files
    except Exception as e:
        logger.error(f"Error extracting text from files: {e}")
        return "", []


# ============================================================================
# TEXT PROCESSING UTILITIES
# ============================================================================

def extract_keywords_from_text(text: str, num_keywords: int = 20, min_length: int = 4) -> List[str]:
    """
    Extract keywords from text using frequency analysis.

    Args:
        text: Input text
        num_keywords: Number of keywords to return
        min_length: Minimum keyword length

    Returns:
        List of keywords
    """
    # Common stop words to exclude
    stop_words = {
        'this', 'that', 'with', 'from', 'they', 'have', 'been', 'will',
        'would', 'could', 'should', 'there', 'their', 'which', 'when',
        'where', 'what', 'about', 'than', 'into', 'through', 'during',
        'before', 'after', 'above', 'below', 'between', 'under', 'again'
    }

    # Extract words
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())

    # Count frequencies
    word_counts = {}
    for word in words:
        if len(word) >= min_length and word not in stop_words:
            word_counts[word] = word_counts.get(word, 0) + 1

    # Sort and return top keywords
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    return [word for word, count in sorted_words[:num_keywords]]


def parse_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract and parse JSON from text that might contain markdown or other formatting.

    Args:
        text: Text potentially containing JSON

    Returns:
        Parsed JSON dict or None
    """
    try:
        # Try to parse directly
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON in code blocks
    json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
    match = re.search(json_pattern, text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find any JSON object
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    return None


# ============================================================================
# API UTILITIES
# ============================================================================

async def call_openai_api(
    prompt: str,
    api_key: Optional[str] = None,
    model: str = CHAT_MODEL,
    max_tokens: int = 2000,
    temperature: float = 0.7
) -> Optional[str]:
    """
    Call OpenAI API with proper error handling and retry logic.

    Args:
        prompt: The prompt to send
        api_key: OpenAI API key (uses env var if not provided)
        model: Model to use
        max_tokens: Maximum tokens in response
        temperature: Temperature for generation

    Returns:
        API response or None if error
    """
    try:
        import httpx

        api_key = api_key or OPENAI_API_KEY
        if not api_key:
            logger.error("OpenAI API key not found")
            return None

        api_endpoint = f"{OPENAI_BASE_URL}/chat/completions"

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                api_endpoint,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert analyst providing structured, actionable insights. Always return valid JSON when requested."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )

            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            else:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                return None
    except ImportError:
        logger.error("httpx library required. Install with: pip install httpx")
        return None
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        return None


async def get_embeddings(
    text: str,
    api_key: Optional[str] = None,
    model: str = EMBEDDING_MODEL
) -> Optional[List[float]]:
    """
    Get embeddings from OpenAI with error handling.

    Args:
        text: Text to embed
        api_key: OpenAI API key
        model: Embedding model to use

    Returns:
        Embedding vector or None
    """
    try:
        import httpx

        api_key = api_key or OPENAI_API_KEY
        if not api_key:
            logger.error("OpenAI API key not found")
            return None

        # Truncate text if too long
        text_chunk = text[:CHUNK_SIZE]

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OPENAI_BASE_URL}/embeddings",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "input": text_chunk
                }
            )

            if response.status_code == 200:
                data = response.json()
                return data["data"][0]["embedding"]
            else:
                logger.error(f"Embeddings API error: {response.status_code}")
                return None
    except Exception as e:
        logger.error(f"Error getting embeddings: {e}")
        return None


async def crawl_website_with_tavily(
    url: str,
    tavily_api_key: str,
    max_pages: int = 50
) -> Dict[str, Any]:
    """
    Crawl a website using Tavily API with error handling.

    Args:
        url: Website URL to crawl
        tavily_api_key: Tavily API key
        max_pages: Maximum pages to crawl

    Returns:
        Crawl results dict
    """
    try:
        import httpx

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://api.tavily.com/crawl",
                headers={
                    "Content-Type": "application/json",
                    "api-key": tavily_api_key
                },
                json={
                    "url": url,
                    "max_pages": max_pages,
                    "include_raw_content": True
                }
            )

            if response.status_code == 200:
                data = response.json()
                # Normalize response format
                if "content" in data:
                    return data
                elif "results" in data:
                    return {"content": data["results"], "url": url}
                elif isinstance(data, list):
                    return {"content": data, "url": url}
                else:
                    return {"content": [data], "url": url}
            else:
                error_msg = f"Tavily API error: {response.status_code}"
                logger.error(error_msg)
                return {"error": error_msg, "content": []}
    except ImportError:
        return {"error": "httpx library required. Install with: pip install httpx", "content": []}
    except Exception as e:
        logger.error(f"Error crawling website {url}: {e}")
        return {"error": str(e), "content": []}


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Similarity score (0-1)
    """
    try:
        import math

        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)
    except Exception as e:
        logger.error(f"Error calculating cosine similarity: {e}")
        return 0.0


# ============================================================================
# REPORT GENERATION UTILITIES
# ============================================================================

def generate_markdown_report(
    title: str,
    content: str,
    sections: Optional[List[str]] = None,
    metadata: Optional[Dict[str, str]] = None
) -> str:
    """
    Generate a well-formatted markdown report.

    Args:
        title: Report title
        content: Main content
        sections: Optional section headings
        metadata: Optional metadata dict

    Returns:
        Formatted markdown string
    """
    lines = [f"# {title}\n"]

    if metadata:
        for key, value in metadata.items():
            lines.append(f"**{key}:** {value}")
        lines.append("\n---\n")

    if sections:
        for i, section in enumerate(sections, 1):
            lines.append(f"## Section {i}: {section}\n")

    lines.append(content)
    lines.append(f"\n\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

    return "\n".join(lines)


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available MCP tools."""
    return [
        # Core Research Tools
        Tool(
            name="research",
            description="Run GPT Researcher on a topic and return comprehensive report",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Research topic or question"
                    },
                    "pages": {
                        "type": "integer",
                        "default": 3,
                        "description": "Number of pages (1-2: quick, 3+: detailed)"
                    }
                },
                "required": ["topic"]
            }
        ),

        # File Analysis Tools
        Tool(
            name="analyze_doc_files",
            description="Analyze files in DOC_PATH directory with various analysis types",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_pattern": {
                        "type": "string",
                        "default": "*",
                        "description": "File pattern to match (e.g., *.txt, *.pdf)"
                    },
                    "analysis_type": {
                        "type": "string",
                        "enum": ["count", "details", "content", "metadata"],
                        "default": "details"
                    },
                    "recursive": {
                        "type": "boolean",
                        "default": False
                    }
                }
            }
        ),

        Tool(
            name="read_file_content",
            description="Read and analyze content of a specific file safely",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Filename in DOC_PATH or relative path"
                    },
                    "max_chars": {
                        "type": "integer",
                        "default": 50000,
                        "description": "Maximum characters to read"
                    }
                },
                "required": ["filename"]
            }
        ),

        Tool(
            name="search_in_files",
            description="Search for text content in files within DOC_PATH",
            inputSchema={
                "type": "object",
                "properties": {
                    "search_text": {
                        "type": "string",
                        "description": "Text to search for"
                    },
                    "file_pattern": {
                        "type": "string",
                        "default": "*.txt"
                    },
                    "case_sensitive": {
                        "type": "boolean",
                        "default": False
                    }
                },
                "required": ["search_text"]
            }
        ),

        # Report Tools
        Tool(
            name="generate_report",
            description="Generate a structured report from content",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "report_type": {
                        "type": "string",
                        "enum": ["summary", "analysis", "detailed", "executive"],
                        "default": "summary"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["markdown", "html", "plain"],
                        "default": "markdown"
                    }
                },
                "required": ["title", "content"]
            }
        ),

        Tool(
            name="save_report",
            description="Save a report to file in DOC_PATH",
            inputSchema={
                "type": "object",
                "properties": {
                    "report_content": {"type": "string"},
                    "filename": {"type": "string"},
                    "format": {
                        "type": "string",
                        "enum": ["txt", "md", "html", "json"],
                        "default": "md"
                    },
                    "append_timestamp": {
                        "type": "boolean",
                        "default": False
                    }
                },
                "required": ["report_content", "filename"]
            }
        ),

        # Stakeholder Analysis Tools
        Tool(
            name="identify_stakeholders",
            description="Analyze project files and identify stakeholders with AI",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_pattern": {
                        "type": "string",
                        "default": "*.txt"
                    },
                    "max_files": {
                        "type": "integer",
                        "default": 20
                    },
                    "use_ai_analysis": {
                        "type": "boolean",
                        "default": True
                    }
                }
            }
        ),

        Tool(
            name="analyze_stakeholder_problems",
            description="Identify problems and challenges for each stakeholder",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_pattern": {
                        "type": "string",
                        "default": "*.txt"
                    },
                    "max_files": {
                        "type": "integer",
                        "default": 20
                    }
                }
            }
        ),

        Tool(
            name="generate_stakeholder_solutions",
            description="Generate solutions for stakeholder problems",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_pattern": {
                        "type": "string",
                        "default": "*.txt"
                    },
                    "max_files": {
                        "type": "integer",
                        "default": 20
                    },
                    "solution_type": {
                        "type": "string",
                        "enum": ["practical", "strategic", "innovative", "all"],
                        "default": "all"
                    }
                }
            }
        ),

        Tool(
            name="identify_opportunities",
            description="Identify opportunities, synergies, and benefits from project analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_pattern": {
                        "type": "string",
                        "default": "*.txt"
                    },
                    "max_files": {
                        "type": "integer",
                        "default": 20
                    },
                    "opportunity_types": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["funding", "partnership", "market", "innovation", "social", "economic", "all"]
                        },
                        "default": ["all"]
                    }
                }
            }
        ),

        Tool(
            name="generate_comprehensive_stakeholder_report",
            description="Generate comprehensive stakeholder analysis with problems, solutions, and opportunities",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_pattern": {
                        "type": "string",
                        "default": "*.txt"
                    },
                    "max_files": {
                        "type": "integer",
                        "default": 20
                    },
                    "include_problems": {
                        "type": "boolean",
                        "default": True
                    },
                    "include_solutions": {
                        "type": "boolean",
                        "default": True
                    },
                    "include_opportunities": {
                        "type": "boolean",
                        "default": True
                    }
                }
            }
        ),

        # Funding Program Matching
        Tool(
            name="find_matching_funding_programs",
            description="Match project files with European funding programs using AI embeddings",
            inputSchema={
                "type": "object",
                "properties": {
                    "funding_websites": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "URLs of funding program websites"
                    },
                    "project_files_pattern": {
                        "type": "string",
                        "default": "*.txt"
                    },
                    "top_matches": {
                        "type": "integer",
                        "default": 5
                    }
                },
                "required": ["funding_websites"]
            }
        ),

        # Utility Tools
        Tool(
            name="extract_keywords",
            description="Extract keywords from text using frequency analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "num_keywords": {
                        "type": "integer",
                        "default": 10
                    }
                },
                "required": ["text"]
            }
        ),

        Tool(
            name="validate_json",
            description="Validate and pretty-print JSON with error fixing",
            inputSchema={
                "type": "object",
                "properties": {
                    "json_string": {"type": "string"},
                    "fix_errors": {
                        "type": "boolean",
                        "default": True
                    }
                },
                "required": ["json_string"]
            }
        )
    ]


# ============================================================================
# TOOL IMPLEMENTATIONS
# ============================================================================

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls with proper routing and error handling."""

    try:
        # Route to appropriate handler
        if name == "research":
            return await handle_research(arguments)
        elif name == "analyze_doc_files":
            return await handle_analyze_doc_files(arguments)
        elif name == "read_file_content":
            return await handle_read_file_content(arguments)
        elif name == "search_in_files":
            return await handle_search_in_files(arguments)
        elif name == "generate_report":
            return await handle_generate_report(arguments)
        elif name == "save_report":
            return await handle_save_report(arguments)
        elif name == "identify_stakeholders":
            return await handle_identify_stakeholders(arguments)
        elif name == "analyze_stakeholder_problems":
            return await handle_analyze_stakeholder_problems(arguments)
        elif name == "generate_stakeholder_solutions":
            return await handle_generate_stakeholder_solutions(arguments)
        elif name == "identify_opportunities":
            return await handle_identify_opportunities(arguments)
        elif name == "generate_comprehensive_stakeholder_report":
            return await handle_comprehensive_stakeholder_report(arguments)
        elif name == "find_matching_funding_programs":
            return await handle_find_matching_funding_programs(arguments)
        elif name == "extract_keywords":
            return await handle_extract_keywords(arguments)
        elif name == "validate_json":
            return await handle_validate_json(arguments)
        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error executing tool {name}: {str(e)}"
        )]


# ============================================================================
# TOOL HANDLERS
# ============================================================================

async def handle_research(arguments: dict) -> list[TextContent]:
    """Handle research tool."""
    topic = arguments.get("topic", "")
    pages = arguments.get("pages", 3)

    if not OPENAI_API_KEY:
        return [TextContent(
            type="text",
            text="Error: OPENAI_API_KEY not configured. Set it in your .env file."
        )]

    if not TAVILY_API_KEY:
        return [TextContent(
            type="text",
            text="Error: TAVILY_API_KEY not configured. Set it in your .env file."
        )]

    try:
        from gpt_researcher import GPTResearcher
        from gpt_researcher.utils.enum import ReportType

        report_type = ReportType.DetailedReport.value if pages >= 3 else ReportType.ResearchReport.value

        researcher = GPTResearcher(
            query=topic,
            report_type=report_type,
            verbose=False
        )

        await researcher.conduct_research()
        report = await researcher.write_report()
        sources = researcher.get_research_sources()

        sources_text = ""
        if sources:
            sources_text = "\n\n## Sources\n" + "\n".join([f"- {source}" for source in sources[:10]])

        return [TextContent(
            type="text",
            text=f"# Research Report: {topic}\n\n{report}{sources_text}"
        )]
    except ImportError:
        return [TextContent(
            type="text",
            text="Error: gpt-researcher not installed. Install with: pip install gpt-researcher"
        )]
    except Exception as e:
        logger.error(f"Research error: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Research failed: {str(e)}\n\nEnsure API keys are set correctly."
        )]


async def handle_analyze_doc_files(arguments: dict) -> list[TextContent]:
    """Handle file analysis tool."""
    file_pattern = arguments.get("file_pattern", "*")
    analysis_type = arguments.get("analysis_type", "details")
    recursive = arguments.get("recursive", False)

    try:
        doc_path = Path(DOC_PATH)
        if not doc_path.exists():
            return [TextContent(
                type="text",
                text=f"DOC_PATH does not exist: {DOC_PATH}\n\nConfigure DOC_PATH in your .env file."
            )]

        # Get files
        if recursive:
            files = list(doc_path.rglob(file_pattern))
        else:
            files = list(doc_path.glob(file_pattern))

        files = [f for f in files if f.is_file()][:MAX_FILES_PER_OPERATION]

        if analysis_type == "count":
            return [TextContent(
                type="text",
                text=f"Found {len(files)} files matching '{file_pattern}' in {DOC_PATH}"
            )]

        elif analysis_type == "details":
            file_info = []
            for file_path in files[:20]:
                try:
                    stat = file_path.stat()
                    file_info.append({
                        "name": file_path.name,
                        "size_bytes": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "type": file_path.suffix
                    })
                except Exception as e:
                    logger.warning(f"Error getting info for {file_path}: {e}")

            return [TextContent(
                type="text",
                text=f"# File Analysis\n\n**Pattern:** {file_pattern}\n**Location:** {DOC_PATH}\n**Files Found:** {len(files)}\n\n## Files\n\n```json\n{json.dumps(file_info, indent=2)}\n```"
            )]

        elif analysis_type == "metadata":
            total_size = sum(f.stat().st_size for f in files)
            file_types = {}
            for f in files:
                ext = f.suffix.lower() or "no_extension"
                file_types[ext] = file_types.get(ext, 0) + 1

            metadata = {
                "total_files": len(files),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "file_types": file_types
            }

            return [TextContent(
                type="text",
                text=f"# File Metadata Analysis\n\n```json\n{json.dumps(metadata, indent=2)}\n```"
            )]

        else:
            return [TextContent(
                type="text",
                text=f"Unknown analysis type: {analysis_type}"
            )]

    except Exception as e:
        logger.error(f"File analysis error: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error analyzing files: {str(e)}"
        )]


async def handle_read_file_content(arguments: dict) -> list[TextContent]:
    """Handle file reading tool with security validation."""
    filename = arguments.get("filename", "")
    max_chars = min(arguments.get("max_chars", 50000), 500000)  # Cap at 500k

    try:
        doc_path = Path(DOC_PATH)

        # Validate and resolve path securely
        if os.path.isabs(filename):
            # Absolute path - validate it's in DOC_PATH
            file_path = validate_path(DOC_PATH, Path(filename).name)
        else:
            # Relative path
            file_path = validate_path(DOC_PATH, filename)

        if not file_path:
            return [TextContent(
                type="text",
                text=f"Invalid file path: {filename}\n\nMust be within DOC_PATH: {DOC_PATH}"
            )]

        content, error = safe_read_file(file_path, max_chars)

        if error:
            return [TextContent(
                type="text",
                text=f"Error: {error}"
            )]

        result = {
            "filename": file_path.name,
            "path": str(file_path.relative_to(doc_path)),
            "size_bytes": file_path.stat().st_size,
            "chars_read": len(content),
            "content": content
        }

        return [TextContent(
            type="text",
            text=f"# File: {file_path.name}\n\n**Size:** {result['size_bytes']} bytes\n**Read:** {result['chars_read']} characters\n\n## Content\n\n```\n{content}\n```"
        )]

    except Exception as e:
        logger.error(f"File read error: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error reading file: {str(e)}"
        )]


async def handle_search_in_files(arguments: dict) -> list[TextContent]:
    """Handle file search tool."""
    search_text = arguments.get("search_text", "")
    file_pattern = arguments.get("file_pattern", "*.txt")
    case_sensitive = arguments.get("case_sensitive", False)

    try:
        doc_path = Path(DOC_PATH)
        if not doc_path.exists():
            return [TextContent(
                type="text",
                text=f"DOC_PATH does not exist: {DOC_PATH}"
            )]

        results = []
        search_term = search_text if case_sensitive else search_text.lower()

        files = list(doc_path.glob(file_pattern))[:MAX_FILES_PER_OPERATION]

        for file_path in files:
            if not file_path.is_file():
                continue

            content, error = safe_read_file(file_path)
            if error:
                continue

            content_to_search = content if case_sensitive else content.lower()

            if search_term in content_to_search:
                # Find matching lines
                lines = content.split('\n')
                matches = []
                for i, line in enumerate(lines, 1):
                    line_check = line if case_sensitive else line.lower()
                    if search_term in line_check:
                        matches.append({
                            "line": i,
                            "content": line[:200]  # Limit line length
                        })
                        if len(matches) >= 5:  # Limit matches per file
                            break

                results.append({
                    "file": file_path.name,
                    "total_matches": content_to_search.count(search_term),
                    "matches": matches
                })

        if not results:
            return [TextContent(
                type="text",
                text=f"No matches found for '{search_text}' in {file_pattern} files"
            )]

        report = f"# Search Results\n\n**Search Term:** {search_text}\n**Pattern:** {file_pattern}\n**Files Searched:** {len(files)}\n**Files with Matches:** {len(results)}\n\n"

        for result in results:
            report += f"## {result['file']}\n\n**Matches:** {result['total_matches']}\n\n"
            for match in result['matches']:
                report += f"- Line {match['line']}: `{match['content']}`\n"
            report += "\n"

        return [TextContent(type="text", text=report)]

    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error searching files: {str(e)}"
        )]


async def handle_generate_report(arguments: dict) -> list[TextContent]:
    """Handle report generation tool."""
    title = arguments.get("title", "Report")
    content = arguments.get("content", "")
    report_type = arguments.get("report_type", "summary")
    format_type = arguments.get("format", "markdown")

    try:
        metadata = {
            "Date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "Type": report_type.title()
        }

        if format_type == "markdown":
            report = generate_markdown_report(title, content, metadata=metadata)
        elif format_type == "html":
            report = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 40px; line-height: 1.6; color: #333; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .metadata {{ background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .content {{ margin: 30px 0; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="metadata">
        <p><strong>Date:</strong> {metadata['Date']}</p>
        <p><strong>Type:</strong> {metadata['Type']}</p>
    </div>
    <div class="content">
        {content.replace(chr(10), '<br>')}
    </div>
</body>
</html>"""
        else:  # plain
            report = f"{title}\n{'=' * len(title)}\n\nDate: {metadata['Date']}\nType: {metadata['Type']}\n\n{content}"

        return [TextContent(type="text", text=report)]

    except Exception as e:
        logger.error(f"Report generation error: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error generating report: {str(e)}"
        )]


async def handle_save_report(arguments: dict) -> list[TextContent]:
    """Handle report saving tool."""
    report_content = arguments.get("report_content", "")
    filename = sanitize_filename(arguments.get("filename", ""))
    format_type = arguments.get("format", "md")
    append_timestamp = arguments.get("append_timestamp", False)

    try:
        doc_path = Path(DOC_PATH)
        doc_path.mkdir(parents=True, exist_ok=True)

        # Add extension if missing
        ext_map = {"txt": ".txt", "md": ".md", "html": ".html", "json": ".json"}
        if not any(filename.endswith(ext) for ext in ext_map.values()):
            filename += ext_map.get(format_type, ".md")

        # Add timestamp if requested
        if append_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{timestamp}{ext}"

        file_path = doc_path / filename

        # Write file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        result = {
            "success": True,
            "filename": file_path.name,
            "path": str(file_path),
            "size_bytes": file_path.stat().st_size
        }

        return [TextContent(
            type="text",
            text=f"# Report Saved\n\n**File:** {result['filename']}\n**Location:** {result['path']}\n**Size:** {result['size_bytes']} bytes"
        )]

    except Exception as e:
        logger.error(f"Save report error: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error saving report: {str(e)}"
        )]


async def handle_identify_stakeholders(arguments: dict) -> list[TextContent]:
    """Handle stakeholder identification tool."""
    file_pattern = arguments.get("file_pattern", "*.txt")
    max_files = min(arguments.get("max_files", 20), MAX_FILES_PER_OPERATION)
    use_ai = arguments.get("use_ai_analysis", True)

    try:
        doc_path = Path(DOC_PATH)
        if not doc_path.exists():
            return [TextContent(
                type="text",
                text=f"DOC_PATH does not exist: {DOC_PATH}"
            )]

        project_text, processed_files = extract_text_from_files(
            doc_path, file_pattern, max_files, 10000
        )

        if not project_text:
            return [TextContent(
                type="text",
                text="No project files found or files are empty"
            )]

        if not use_ai:
            keywords = extract_keywords_from_text(project_text, 30)
            return [TextContent(
                type="text",
                text=f"# Stakeholder Keywords (Basic Analysis)\n\n{', '.join(keywords)}\n\n*Note: Enable AI analysis for better results*"
            )]

        if not OPENAI_API_KEY:
            return [TextContent(
                type="text",
                text="Error: OPENAI_API_KEY required for AI analysis"
            )]

        # AI analysis
        prompt = f"""Analyze this project and identify all stakeholders.

Project Content:
{project_text[:CHUNK_SIZE]}

Categorize stakeholders into: Beneficiaries, Partners, Funders, Regulators, Implementers, Community, Suppliers, Competitors.

Return JSON:
{{
    "stakeholders": [
        {{
            "name": "stakeholder name",
            "category": "category",
            "role": "description",
            "interest": "their interest",
            "influence": "high/medium/low"
        }}
    ],
    "summary": "brief stakeholder landscape summary"
}}"""

        response = await call_openai_api(prompt, max_tokens=3000)

        if not response:
            return [TextContent(
                type="text",
                text="Error: AI analysis failed. Check API configuration."
            )]

        data = parse_json_from_text(response)

        if data:
            # Format as markdown
            report = f"""# Stakeholder Analysis

**Files Analyzed:** {len(processed_files)}
**Summary:** {data.get('summary', 'N/A')}

## Stakeholders

"""

            # Group by category
            by_category = {}
            for s in data.get('stakeholders', []):
                cat = s.get('category', 'Other')
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(s)

            for category, stakeholders in by_category.items():
                report += f"### {category}\n\n"
                for s in stakeholders:
                    report += f"""**{s.get('name', 'Unknown')}**
- Role: {s.get('role', 'N/A')}
- Interest: {s.get('interest', 'N/A')}
- Influence: {s.get('influence', 'N/A')}

"""

            return [TextContent(type="text", text=report)]
        else:
            return [TextContent(type="text", text=f"Stakeholder Analysis:\n\n{response}")]

    except Exception as e:
        logger.error(f"Stakeholder identification error: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error identifying stakeholders: {str(e)}"
        )]


async def handle_analyze_stakeholder_problems(arguments: dict) -> list[TextContent]:
    """Handle stakeholder problem analysis tool."""
    file_pattern = arguments.get("file_pattern", "*.txt")
    max_files = min(arguments.get("max_files", 20), MAX_FILES_PER_OPERATION)

    try:
        if not OPENAI_API_KEY:
            return [TextContent(
                type="text",
                text="Error: OPENAI_API_KEY required"
            )]

        doc_path = Path(DOC_PATH)
        project_text, _ = extract_text_from_files(doc_path, file_pattern, max_files, 10000)

        if not project_text:
            return [TextContent(
                type="text",
                text="No project files found"
            )]

        prompt = f"""Analyze stakeholder problems in this project.

Project:
{project_text[:CHUNK_SIZE]}

Return JSON:
{{
    "stakeholder_problems": [
        {{
            "stakeholder": "name",
            "problems": [
                {{
                    "problem": "description",
                    "severity": "high/medium/low",
                    "impact": "impact description",
                    "root_cause": "cause"
                }}
            ],
            "summary": "summary for this stakeholder"
        }}
    ],
    "overall_analysis": "overall summary"
}}"""

        response = await call_openai_api(prompt, max_tokens=4000)

        if not response:
            return [TextContent(
                type="text",
                text="Error: AI analysis failed"
            )]

        data = parse_json_from_text(response)

        if data:
            report = f"""# Stakeholder Problems Analysis

## Overall Analysis
{data.get('overall_analysis', 'N/A')}

## Problems by Stakeholder

"""

            for sp in data.get('stakeholder_problems', []):
                report += f"### {sp.get('stakeholder', 'Unknown')}\n\n"
                report += f"**Summary:** {sp.get('summary', 'N/A')}\n\n"

                for problem in sp.get('problems', []):
                    report += f"""**{problem.get('problem', 'N/A')}**
- Severity: {problem.get('severity', 'N/A')}
- Impact: {problem.get('impact', 'N/A')}
- Root Cause: {problem.get('root_cause', 'N/A')}

"""

            return [TextContent(type="text", text=report)]
        else:
            return [TextContent(type="text", text=response)]

    except Exception as e:
        logger.error(f"Problem analysis error: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error analyzing problems: {str(e)}"
        )]


async def handle_generate_stakeholder_solutions(arguments: dict) -> list[TextContent]:
    """Handle solution generation tool."""
    file_pattern = arguments.get("file_pattern", "*.txt")
    max_files = min(arguments.get("max_files", 20), MAX_FILES_PER_OPERATION)
    solution_type = arguments.get("solution_type", "all")

    try:
        if not OPENAI_API_KEY:
            return [TextContent(
                type="text",
                text="Error: OPENAI_API_KEY required"
            )]

        doc_path = Path(DOC_PATH)
        project_text, _ = extract_text_from_files(doc_path, file_pattern, max_files, 10000)

        if not project_text:
            return [TextContent(
                type="text",
                text="No project files found"
            )]

        solution_types_map = {
            "practical": "practical, implementable",
            "strategic": "strategic, long-term",
            "innovative": "innovative, creative",
            "all": "practical, strategic, and innovative"
        }

        prompt = f"""Generate {solution_types_map.get(solution_type, 'all')} solutions for stakeholders.

Project:
{project_text[:CHUNK_SIZE]}

Return JSON:
{{
    "stakeholder_solutions": [
        {{
            "stakeholder": "name",
            "solutions": [
                {{
                    "solution": "description",
                    "type": "practical/strategic/innovative",
                    "benefits": "benefits",
                    "implementation": "how to implement",
                    "resources_needed": "resources",
                    "timeline": "timeline"
                }}
            ],
            "summary": "overall strategy"
        }}
    ],
    "overall_strategy": "comprehensive strategy"
}}"""

        response = await call_openai_api(prompt, max_tokens=5000)

        if not response:
            return [TextContent(
                type="text",
                text="Error: AI analysis failed"
            )]

        data = parse_json_from_text(response)

        if data:
            report = f"""# Stakeholder Solutions

## Overall Strategy
{data.get('overall_strategy', 'N/A')}

## Solutions by Stakeholder

"""

            for ss in data.get('stakeholder_solutions', []):
                report += f"### {ss.get('stakeholder', 'Unknown')}\n\n"
                report += f"**Strategy:** {ss.get('summary', 'N/A')}\n\n"

                for sol in ss.get('solutions', []):
                    report += f"""**{sol.get('solution', 'N/A')}**
- Type: {sol.get('type', 'N/A')}
- Benefits: {sol.get('benefits', 'N/A')}
- Implementation: {sol.get('implementation', 'N/A')}
- Resources: {sol.get('resources_needed', 'N/A')}
- Timeline: {sol.get('timeline', 'N/A')}

"""

            return [TextContent(type="text", text=report)]
        else:
            return [TextContent(type="text", text=response)]

    except Exception as e:
        logger.error(f"Solution generation error: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error generating solutions: {str(e)}"
        )]


async def handle_identify_opportunities(arguments: dict) -> list[TextContent]:
    """Handle opportunity identification tool."""
    file_pattern = arguments.get("file_pattern", "*.txt")
    max_files = min(arguments.get("max_files", 20), MAX_FILES_PER_OPERATION)
    opportunity_types = arguments.get("opportunity_types", ["all"])

    try:
        if not OPENAI_API_KEY:
            return [TextContent(
                type="text",
                text="Error: OPENAI_API_KEY required"
            )]

        doc_path = Path(DOC_PATH)
        project_text, _ = extract_text_from_files(doc_path, file_pattern, max_files, 10000)

        if not project_text:
            return [TextContent(
                type="text",
                text="No project files found"
            )]

        opp_types_str = ', '.join(opportunity_types) if "all" not in opportunity_types else "all types"

        prompt = f"""Identify opportunities in this project.

Focus on: {opp_types_str} opportunities.

Project:
{project_text[:CHUNK_SIZE]}

Return JSON:
{{
    "opportunities": [
        {{
            "opportunity": "description",
            "type": "funding/partnership/market/innovation/social/economic",
            "potential_impact": "impact",
            "feasibility": "high/medium/low",
            "stakeholders_involved": ["list"],
            "next_steps": "steps",
            "timeline": "timeline",
            "resources_required": "resources"
        }}
    ],
    "synergies": [
        {{
            "synergy": "description",
            "stakeholders": ["list"],
            "benefits": "benefits"
        }}
    ],
    "overall_summary": "summary"
}}"""

        response = await call_openai_api(prompt, max_tokens=4000)

        if not response:
            return [TextContent(
                type="text",
                text="Error: AI analysis failed"
            )]

        data = parse_json_from_text(response)

        if data:
            report = f"""# Opportunities Analysis

## Summary
{data.get('overall_summary', 'N/A')}

## Opportunities

"""

            # Group by type
            by_type = {}
            for opp in data.get('opportunities', []):
                opp_type = opp.get('type', 'Other')
                if opp_type not in by_type:
                    by_type[opp_type] = []
                by_type[opp_type].append(opp)

            for opp_type, opportunities in by_type.items():
                report += f"### {opp_type.title()} Opportunities\n\n"
                for opp in opportunities:
                    report += f"""**{opp.get('opportunity', 'N/A')}**
- Impact: {opp.get('potential_impact', 'N/A')}
- Feasibility: {opp.get('feasibility', 'N/A')}
- Stakeholders: {', '.join(opp.get('stakeholders_involved', []))}
- Next Steps: {opp.get('next_steps', 'N/A')}
- Timeline: {opp.get('timeline', 'N/A')}

"""

            # Add synergies
            synergies = data.get('synergies', [])
            if synergies:
                report += "\n## Synergies\n\n"
                for syn in synergies:
                    report += f"""**{syn.get('synergy', 'N/A')}**
- Stakeholders: {', '.join(syn.get('stakeholders', []))}
- Benefits: {syn.get('benefits', 'N/A')}

"""

            return [TextContent(type="text", text=report)]
        else:
            return [TextContent(type="text", text=response)]

    except Exception as e:
        logger.error(f"Opportunity identification error: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error identifying opportunities: {str(e)}"
        )]


async def handle_comprehensive_stakeholder_report(arguments: dict) -> list[TextContent]:
    """Handle comprehensive stakeholder report generation."""
    file_pattern = arguments.get("file_pattern", "*.txt")
    max_files = min(arguments.get("max_files", 20), MAX_FILES_PER_OPERATION)
    include_problems = arguments.get("include_problems", True)
    include_solutions = arguments.get("include_solutions", True)
    include_opportunities = arguments.get("include_opportunities", True)

    try:
        if not OPENAI_API_KEY:
            return [TextContent(
                type="text",
                text="Error: OPENAI_API_KEY required"
            )]

        doc_path = Path(DOC_PATH)
        project_text, processed_files = extract_text_from_files(doc_path, file_pattern, max_files, 10000)

        if not project_text:
            return [TextContent(
                type="text",
                text="No project files found"
            )]

        sections = []
        if include_problems:
            sections.append("problems and challenges for each stakeholder")
        if include_solutions:
            sections.append("solutions and recommendations")
        if include_opportunities:
            sections.append("opportunities and synergies")

        sections_str = ", ".join(sections) if sections else "stakeholder identification"

        prompt = f"""Comprehensive stakeholder analysis including: {sections_str}

Project:
{project_text[:CHUNK_SIZE]}

Return comprehensive JSON with stakeholders array containing name, category, role, interest, influence{', problems' if include_problems else ''}{', solutions' if include_solutions else ''}, and executive_summary. {'Include opportunities array.' if include_opportunities else ''}"""

        response = await call_openai_api(prompt, max_tokens=6000)

        if not response:
            return [TextContent(
                type="text",
                text="Error: AI analysis failed"
            )]

        data = parse_json_from_text(response)

        if data:
            report = f"""# Comprehensive Stakeholder Analysis

**Files Analyzed:** {len(processed_files)}

## Executive Summary
{data.get('executive_summary', 'N/A')}

## Stakeholders

"""

            # Group by category
            by_category = {}
            for s in data.get('stakeholders', []):
                cat = s.get('category', 'Other')
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(s)

            for category, stakeholders in by_category.items():
                report += f"### {category}\n\n"
                for s in stakeholders:
                    report += f"""**{s.get('name', 'Unknown')}**
- Role: {s.get('role', 'N/A')}
- Interest: {s.get('interest', 'N/A')}
- Influence: {s.get('influence', 'N/A')}
"""

                    if include_problems and 'problems' in s:
                        report += "\n**Problems:**\n"
                        problems = s['problems']
                        if isinstance(problems, list):
                            for p in problems:
                                if isinstance(p, dict):
                                    report += f"- {p.get('problem', 'N/A')} (Severity: {p.get('severity', 'N/A')})\n"
                                else:
                                    report += f"- {p}\n"
                        else:
                            report += f"- {problems}\n"

                    if include_solutions and 'solutions' in s:
                        report += "\n**Solutions:**\n"
                        solutions = s['solutions']
                        if isinstance(solutions, list):
                            for sol in solutions:
                                if isinstance(sol, dict):
                                    report += f"- {sol.get('solution', 'N/A')} ({sol.get('type', 'N/A')})\n"
                                else:
                                    report += f"- {sol}\n"
                        else:
                            report += f"- {solutions}\n"

                    report += "\n"

            if include_opportunities and 'opportunities' in data:
                report += "\n## Opportunities\n\n"
                for opp in data['opportunities']:
                    report += f"""**{opp.get('opportunity', 'N/A')}**
- Type: {opp.get('type', 'N/A')}
- Impact: {opp.get('impact', 'N/A')}
- Feasibility: {opp.get('feasibility', 'N/A')}

"""

            report += f"\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"

            return [TextContent(type="text", text=report)]
        else:
            return [TextContent(type="text", text=response)]

    except Exception as e:
        logger.error(f"Comprehensive report error: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error generating comprehensive report: {str(e)}"
        )]


async def handle_find_matching_funding_programs(arguments: dict) -> list[TextContent]:
    """Handle funding program matching tool."""
    funding_websites = arguments.get("funding_websites", [])
    project_files_pattern = arguments.get("project_files_pattern", "*.txt")
    top_matches = arguments.get("top_matches", 5)

    try:
        if not TAVILY_API_KEY:
            return [TextContent(
                type="text",
                text="Error: TAVILY_API_KEY required"
            )]

        if not OPENAI_API_KEY:
            return [TextContent(
                type="text",
                text="Error: OPENAI_API_KEY required"
            )]

        if not funding_websites:
            return [TextContent(
                type="text",
                text="Error: No funding websites provided"
            )]

        doc_path = Path(DOC_PATH)
        if not doc_path.exists():
            return [TextContent(
                type="text",
                text=f"DOC_PATH does not exist: {DOC_PATH}"
            )]

        # Extract project info
        project_text, processed_files = extract_text_from_files(
            doc_path, project_files_pattern, 20, 10000
        )

        if not project_text:
            return [TextContent(
                type="text",
                text="No project files found"
            )]

        project_summary = project_text[:2000]
        project_keywords = extract_keywords_from_text(project_text, 30)

        # Get project embedding
        project_embedding = await get_embeddings(project_summary)
        if not project_embedding:
            return [TextContent(
                type="text",
                text="Error: Failed to generate project embeddings"
            )]

        # Crawl and analyze funding programs
        program_data = []

        for url in funding_websites:
            crawl_result = await crawl_website_with_tavily(url, TAVILY_API_KEY, 50)

            if "error" in crawl_result:
                logger.warning(f"Error crawling {url}: {crawl_result['error']}")
                continue

            content_items = crawl_result.get("content", [])

            for item in content_items:
                if isinstance(item, dict):
                    content = item.get("content", "") or item.get("raw_content", "")
                    title = item.get("title", "")
                    page_url = item.get("url", url)

                    if content and len(content) > 100:
                        program_text = f"Title: {title}\nContent: {content[:4000]}"
                        program_embedding = await get_embeddings(program_text)

                        if program_embedding:
                            similarity = cosine_similarity(project_embedding, program_embedding)

                            program_data.append({
                                "title": title,
                                "url": page_url,
                                "source_website": url,
                                "content_preview": content[:500],
                                "similarity_score": round(similarity, 4),
                                "keywords": extract_keywords_from_text(content, 10)
                            })

        if not program_data:
            return [TextContent(
                type="text",
                text="No funding programs found. Check website URLs and API keys."
            )]

        # Sort and get top matches
        program_data.sort(key=lambda x: x["similarity_score"], reverse=True)
        top_programs = program_data[:top_matches]

        # Generate report
        report = f"""# Funding Program Matching Report

## Project Analysis
- **Files Analyzed:** {len(processed_files)}
- **Total Characters:** {len(project_text)}
- **Key Keywords:** {', '.join(project_keywords[:15])}

## Top {len(top_programs)} Matching Programs

"""

        for i, program in enumerate(top_programs, 1):
            report += f"""### {i}. {program['title']}

- **Similarity Score:** {program['similarity_score']:.2%}
- **Source:** {program['source_website']}
- **URL:** {program['url']}
- **Keywords:** {', '.join(program['keywords'][:10])}

**Preview:**
{program['content_preview'][:300]}...

---

"""

        report += f"""
## Summary
- **Total Programs Analyzed:** {len(program_data)}
- **Websites Crawled:** {len(funding_websites)}
- **Analysis Date:** {datetime.now().isoformat()}
"""

        return [TextContent(type="text", text=report)]

    except Exception as e:
        logger.error(f"Funding program matching error: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error finding funding programs: {str(e)}"
        )]


async def handle_extract_keywords(arguments: dict) -> list[TextContent]:
    """Handle keyword extraction tool."""
    text = arguments.get("text", "")
    num_keywords = arguments.get("num_keywords", 10)

    try:
        keywords = extract_keywords_from_text(text, num_keywords)
        return [TextContent(
            type="text",
            text=f"**Keywords:** {', '.join(keywords)}"
        )]
    except Exception as e:
        logger.error(f"Keyword extraction error: {e}")
        return [TextContent(
            type="text",
            text=f"Error extracting keywords: {str(e)}"
        )]


async def handle_validate_json(arguments: dict) -> list[TextContent]:
    """Handle JSON validation tool."""
    json_string = arguments.get("json_string", "")
    fix_errors = arguments.get("fix_errors", True)

    try:
        parsed = json.loads(json_string)
        pretty = json.dumps(parsed, indent=2)
        return [TextContent(
            type="text",
            text=f"✅ **Valid JSON**\n\n```json\n{pretty}\n```"
        )]
    except json.JSONDecodeError as e:
        if fix_errors:
            # Try common fixes
            fixed = json_string.replace("'", '"')
            try:
                parsed = json.loads(fixed)
                pretty = json.dumps(parsed, indent=2)
                return [TextContent(
                    type="text",
                    text=f"✅ **Fixed JSON** (replaced single quotes)\n\n```json\n{pretty}\n```"
                )]
            except:
                pass

        return [TextContent(
            type="text",
            text=f"❌ **JSON Error:** {str(e)}\n\n**Position:** Line {e.lineno}, Column {e.colno}\n\n**Tip:** Check for missing quotes, trailing commas, or unescaped characters."
        )]


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Run the MCP server."""
    logger.info(f"Starting GPT Researcher MCP Server")
    logger.info(f"DOC_PATH: {DOC_PATH}")
    logger.info(f"OpenAI API configured: {bool(OPENAI_API_KEY)}")
    logger.info(f"Tavily API configured: {bool(TAVILY_API_KEY)}")

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
