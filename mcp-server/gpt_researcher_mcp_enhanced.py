#!/usr/bin/env python3
"""
Enhanced GPT-Researcher MCP Server
Built with FastMCP following MCP best practices
Provides research, analysis, and document processing capabilities
"""

import asyncio
import json
import os
import sys
import re
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal
from enum import Enum

# MCP and FastMCP imports
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator, ConfigDict
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastMCP server with proper naming convention
mcp = FastMCP("gpt_researcher_mcp")

# Configuration from environment
DOC_PATH = Path(os.getenv('DOC_PATH', 'C:/my_docs'))
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')

# LLM configurations
STRATEGIC_LLM = os.getenv('STRATEGIC_LLM', 'gpt-4o')
SMART_LLM = os.getenv('SMART_LLM', 'gpt-4o')
FAST_LLM = os.getenv('FAST_LLM', 'gpt-3.5-turbo')

# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"
    HTML = "html"
    TEXT = "text"

class AnalysisType(str, Enum):
    """Types of analysis available."""
    SUMMARY = "summary"
    TRENDS = "trends"
    STATISTICS = "statistics"
    DETAILED = "detailed"

class FileAnalysisType(str, Enum):
    """Types of file analysis."""
    COUNT = "count"
    DETAILS = "details"
    CONTENT = "content"
    METADATA = "metadata"

class MetricType(str, Enum):
    """Text metrics that can be calculated."""
    WORD_COUNT = "word_count"
    CHAR_COUNT = "char_count"
    READABILITY = "readability"
    SENTIMENT = "sentiment"

class OpportunityType(str, Enum):
    """Types of opportunities to identify."""
    FUNDING = "funding"
    PARTNERSHIP = "partnership"
    MARKET = "market"
    INNOVATION = "innovation"
    SOCIAL = "social"
    ECONOMIC = "economic"
    ALL = "all"

# ============================================================================
# PYDANTIC MODELS WITH VALIDATION
# ============================================================================

class ResearchInput(BaseModel):
    """Input model for research operations."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    topic: str = Field(
        ..., 
        description="Research topic to investigate (e.g., 'AI in healthcare', 'climate change solutions')",
        min_length=1,
        max_length=500
    )
    pages: int = Field(
        default=3,
        description="Number of pages for the report (1-10)",
        ge=1,
        le=10
    )
    
    @field_validator('topic')
    @classmethod
    def validate_topic(cls, v: str) -> str:
        """Ensure topic is meaningful."""
        if len(v.strip()) < 3:
            raise ValueError("Topic must be at least 3 characters")
        return v.strip()

class AnalyzeDataInput(BaseModel):
    """Input model for data analysis."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    data: str = Field(
        ...,
        description="JSON data to analyze",
        min_length=2
    )
    analysis_type: AnalysisType = Field(
        default=AnalysisType.SUMMARY,
        description="Type of analysis to perform"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format for the analysis"
    )
    
    @field_validator('data')
    @classmethod
    def validate_json_data(cls, v: str) -> str:
        """Validate that data is proper JSON."""
        try:
            json.loads(v)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON data: {e}")
        return v

class FileOperationInput(BaseModel):
    """Input model for file operations."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    file_pattern: str = Field(
        default="*",
        description="File pattern to match (e.g., '*.txt', '*.pdf', 'project*')",
        max_length=100
    )
    analysis_type: FileAnalysisType = Field(
        default=FileAnalysisType.DETAILS,
        description="Type of file analysis"
    )
    recursive: bool = Field(
        default=False,
        description="Search subdirectories recursively"
    )
    max_files: int = Field(
        default=20,
        description="Maximum number of files to analyze",
        ge=1,
        le=100
    )
    
    @field_validator('file_pattern')
    @classmethod
    def validate_pattern(cls, v: str) -> str:
        """Ensure file pattern is safe."""
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError("File pattern cannot contain path traversal")
        return v

class StakeholderAnalysisInput(BaseModel):
    """Input model for stakeholder analysis."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    file_pattern: str = Field(
        default="*.txt",
        description="Pattern for project files to analyze"
    )
    max_files: int = Field(
        default=20,
        description="Maximum files to analyze",
        ge=1,
        le=50
    )
    use_ai_analysis: bool = Field(
        default=True,
        description="Use AI for advanced analysis"
    )
    categories: Optional[List[str]] = Field(
        default_factory=lambda: ["primary", "secondary", "indirect"],
        description="Stakeholder categories to identify"
    )

class ComprehensiveReportInput(BaseModel):
    """Input model for comprehensive report generation."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    file_pattern: str = Field(
        default="*.txt",
        description="Pattern for files to include"
    )
    max_files: int = Field(
        default=20,
        description="Maximum files to process",
        ge=1,
        le=50
    )
    include_problems: bool = Field(
        default=True,
        description="Include problem analysis"
    )
    include_solutions: bool = Field(
        default=True,
        description="Include solution recommendations"
    )
    include_opportunities: bool = Field(
        default=True,
        description="Include opportunity identification"
    )
    format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format for the report"
    )

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def analyze_with_openai(prompt: str, max_tokens: int = 2000) -> Optional[str]:
    """Make async request to OpenAI API."""
    if not OPENAI_API_KEY:
        return None
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OPENAI_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                json={
                    "model": SMART_LLM,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": 0.7
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('choices', [{}])[0].get('message', {}).get('content', '')
    except Exception as e:
        return f"Error: {str(e)}"
    
    return None

def extract_text_from_files(
    directory: Path, 
    pattern: str = "*", 
    max_files: int = 20,
    max_chars_per_file: int = 10000
) -> str:
    """Extract text content from multiple files."""
    texts = []
    files_processed = 0
    
    try:
        files = list(directory.glob(pattern))[:max_files]
        
        for file_path in files:
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(max_chars_per_file)
                        texts.append(f"=== {file_path.name} ===\n{content}\n")
                        files_processed += 1
                except Exception:
                    continue
    except Exception as e:
        return f"Error reading files: {str(e)}"
    
    return '\n'.join(texts) if texts else "No readable files found"

def parse_json_from_text(text: str) -> Optional[Dict]:
    """Extract and parse JSON from AI response text."""
    try:
        # Try direct JSON parsing
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON-like structure
        json_match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
    
    return None

# ============================================================================
# TOOL IMPLEMENTATIONS
# ============================================================================

@mcp.tool(
    name="gpt_research",
    annotations={
        "title": "GPT Researcher - Advanced Research Tool",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def gpt_research(params: ResearchInput) -> str:
    """
    Run GPT Researcher on a topic and generate a comprehensive report.
    
    This tool uses the GPT Researcher library to conduct in-depth research
    on any topic, gathering information from multiple sources and synthesizing
    it into a well-structured report.
    
    Args:
        params: ResearchInput with topic and pages configuration
    
    Returns:
        JSON or Markdown formatted research report
    """
    try:
        # Run GPT Researcher
        cmd = [
            sys.executable, "-m", "gpt_researcher", 
            params.topic, 
            "--report_length", str(params.pages)
        ]
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await proc.communicate()
        
        if proc.returncode == 0:
            report = stdout.decode('utf-8')
            
            return json.dumps({
                "status": "success",
                "topic": params.topic,
                "pages": params.pages,
                "report": report,
                "timestamp": datetime.now().isoformat()
            }, indent=2)
        else:
            error_msg = stderr.decode('utf-8')
            return json.dumps({
                "status": "error",
                "topic": params.topic,
                "error": error_msg,
                "suggestion": "Check if gpt-researcher is installed and API keys are configured"
            }, indent=2)
            
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "suggestion": "Ensure gpt-researcher is installed: pip install gpt-researcher"
        }, indent=2)

@mcp.tool(
    name="analyze_project_data",
    annotations={
        "title": "Analyze Project Data",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def analyze_project_data(params: AnalyzeDataInput) -> str:
    """
    Analyze JSON data and provide insights based on the specified analysis type.
    
    Supports multiple analysis types:
    - summary: Overview and key metrics
    - trends: Pattern identification
    - statistics: Statistical analysis
    - detailed: Comprehensive analysis
    
    Args:
        params: AnalyzeDataInput with data and analysis configuration
    
    Returns:
        Formatted analysis results in specified format
    """
    try:
        data = json.loads(params.data)
        
        # Perform analysis based on type
        if params.analysis_type == AnalysisType.SUMMARY:
            result = {
                "type": "summary",
                "total_items": len(data) if isinstance(data, (list, dict)) else 1,
                "data_type": type(data).__name__,
                "key_count": len(data.keys()) if isinstance(data, dict) else None,
                "preview": str(data)[:200] + "..." if len(str(data)) > 200 else str(data)
            }
            
        elif params.analysis_type == AnalysisType.STATISTICS:
            # Extract numeric values for statistics
            numbers = []
            
            def extract_numbers(obj):
                if isinstance(obj, (int, float)):
                    numbers.append(obj)
                elif isinstance(obj, dict):
                    for v in obj.values():
                        extract_numbers(v)
                elif isinstance(obj, list):
                    for item in obj:
                        extract_numbers(item)
            
            extract_numbers(data)
            
            if numbers:
                import statistics
                result = {
                    "type": "statistics",
                    "count": len(numbers),
                    "mean": statistics.mean(numbers),
                    "median": statistics.median(numbers),
                    "min": min(numbers),
                    "max": max(numbers),
                    "stdev": statistics.stdev(numbers) if len(numbers) > 1 else 0
                }
            else:
                result = {
                    "type": "statistics",
                    "message": "No numeric data found for statistical analysis"
                }
                
        elif params.analysis_type == AnalysisType.TRENDS:
            # AI-powered trend analysis if API key available
            if OPENAI_API_KEY:
                prompt = f"Analyze the following data for trends and patterns:\n{json.dumps(data, indent=2)[:3000]}"
                ai_analysis = await analyze_with_openai(prompt, max_tokens=1000)
                result = {
                    "type": "trends",
                    "ai_analysis": ai_analysis or "AI analysis unavailable",
                    "data_structure": type(data).__name__
                }
            else:
                result = {
                    "type": "trends",
                    "message": "AI analysis requires OPENAI_API_KEY",
                    "data_structure": type(data).__name__
                }
                
        else:  # DETAILED
            result = {
                "type": "detailed",
                "complete_analysis": {
                    "structure": type(data).__name__,
                    "size": len(str(data)),
                    "complexity": "simple" if len(str(data)) < 1000 else "complex",
                    "data": data
                }
            }
        
        # Format output
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(result, indent=2)
        elif params.response_format == ResponseFormat.MARKDOWN:
            md = f"# Data Analysis Report\n\n"
            md += f"**Analysis Type:** {params.analysis_type.value}\n\n"
            md += f"## Results\n\n"
            for key, value in result.items():
                if key != "data":
                    md += f"- **{key}:** {value}\n"
            return md
        else:
            return str(result)
            
    except json.JSONDecodeError as e:
        return json.dumps({
            "status": "error",
            "error": f"Invalid JSON: {str(e)}",
            "suggestion": "Ensure the data parameter contains valid JSON"
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        }, indent=2)

@mcp.tool(
    name="analyze_documents",
    annotations={
        "title": "Analyze Documents in Directory",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def analyze_documents(params: FileOperationInput) -> str:
    """
    Analyze files in the configured document directory with various analysis types.
    
    Analysis types:
    - count: File count and basic stats
    - details: Detailed file information
    - content: Extract and preview content
    - metadata: File metadata analysis
    
    Args:
        params: FileOperationInput with pattern and analysis configuration
    
    Returns:
        JSON formatted analysis results
    """
    if not DOC_PATH.exists():
        return json.dumps({
            "status": "error",
            "error": f"Document path {DOC_PATH} does not exist",
            "suggestion": "Configure DOC_PATH environment variable"
        }, indent=2)
    
    try:
        # Get matching files
        if params.recursive:
            files = list(DOC_PATH.rglob(params.file_pattern))
        else:
            files = list(DOC_PATH.glob(params.file_pattern))
        
        files = files[:params.max_files]
        
        if params.analysis_type == FileAnalysisType.COUNT:
            result = {
                "type": "count",
                "total_files": len(files),
                "pattern": params.file_pattern,
                "recursive": params.recursive,
                "path": str(DOC_PATH)
            }
            
        elif params.analysis_type == FileAnalysisType.DETAILS:
            file_details = []
            for f in files:
                if f.is_file():
                    stat = f.stat()
                    file_details.append({
                        "name": f.name,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "extension": f.suffix
                    })
            
            result = {
                "type": "details",
                "files": file_details,
                "total": len(file_details)
            }
            
        elif params.analysis_type == FileAnalysisType.CONTENT:
            contents = []
            for f in files[:5]:  # Limit content extraction
                if f.is_file():
                    try:
                        with open(f, 'r', encoding='utf-8', errors='ignore') as file:
                            content = file.read(500)
                            contents.append({
                                "file": f.name,
                                "preview": content,
                                "size": len(content)
                            })
                    except Exception as e:
                        contents.append({
                            "file": f.name,
                            "error": str(e)
                        })
            
            result = {
                "type": "content",
                "previews": contents,
                "files_previewed": len(contents)
            }
            
        else:  # METADATA
            metadata = {
                "total_files": len(files),
                "total_size": sum(f.stat().st_size for f in files if f.is_file()),
                "file_types": {},
                "oldest_file": None,
                "newest_file": None
            }
            
            for f in files:
                if f.is_file():
                    ext = f.suffix or "no_extension"
                    metadata["file_types"][ext] = metadata["file_types"].get(ext, 0) + 1
                    
                    mtime = f.stat().st_mtime
                    if metadata["oldest_file"] is None or mtime < metadata["oldest_file"][1]:
                        metadata["oldest_file"] = (f.name, mtime)
                    if metadata["newest_file"] is None or mtime > metadata["newest_file"][1]:
                        metadata["newest_file"] = (f.name, mtime)
            
            if metadata["oldest_file"]:
                metadata["oldest_file"] = {
                    "name": metadata["oldest_file"][0],
                    "modified": datetime.fromtimestamp(metadata["oldest_file"][1]).isoformat()
                }
            if metadata["newest_file"]:
                metadata["newest_file"] = {
                    "name": metadata["newest_file"][0],
                    "modified": datetime.fromtimestamp(metadata["newest_file"][1]).isoformat()
                }
            
            result = {"type": "metadata", **metadata}
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "path": str(DOC_PATH)
        }, indent=2)

@mcp.tool(
    name="identify_stakeholders",
    annotations={
        "title": "Identify Project Stakeholders",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def identify_stakeholders(params: StakeholderAnalysisInput) -> str:
    """
    Identify and categorize stakeholders from project documents using AI analysis.
    
    Analyzes project files to identify:
    - Primary stakeholders (direct involvement)
    - Secondary stakeholders (indirect involvement)
    - Indirect stakeholders (affected by outcomes)
    
    Args:
        params: StakeholderAnalysisInput with file pattern and analysis settings
    
    Returns:
        JSON formatted stakeholder analysis
    """
    if not params.use_ai_analysis:
        return json.dumps({
            "status": "error",
            "message": "AI analysis is required for stakeholder identification"
        }, indent=2)
    
    if not OPENAI_API_KEY:
        return json.dumps({
            "status": "error",
            "error": "OPENAI_API_KEY required for stakeholder analysis"
        }, indent=2)
    
    try:
        # Extract project text
        project_text = extract_text_from_files(
            DOC_PATH, 
            params.file_pattern, 
            params.max_files
        )
        
        if not project_text or project_text.startswith("Error"):
            return json.dumps({
                "status": "error",
                "error": "No project files found or readable",
                "path": str(DOC_PATH),
                "pattern": params.file_pattern
            }, indent=2)
        
        # AI prompt for stakeholder identification
        prompt = f"""Analyze the following project description and identify ALL stakeholders.
        
Categories to consider: {', '.join(params.categories or ['primary', 'secondary', 'indirect'])}

Project Description:
{project_text[:8000]}

Return a JSON object with this structure:
{{
    "stakeholders": [
        {{
            "name": "Stakeholder name/group",
            "category": "primary/secondary/indirect",
            "role": "Their role in the project",
            "interest": "What they care about",
            "influence": "high/medium/low",
            "needs": ["need1", "need2"],
            "expectations": ["expectation1", "expectation2"]
        }}
    ],
    "summary": "Brief summary of stakeholder landscape",
    "total_identified": number
}}"""
        
        # Get AI analysis
        ai_response = await analyze_with_openai(prompt, max_tokens=3000)
        
        if ai_response:
            parsed_data = parse_json_from_text(ai_response)
            if parsed_data:
                return json.dumps(parsed_data, indent=2)
            else:
                # Return raw response if JSON parsing fails
                return json.dumps({
                    "status": "success",
                    "raw_analysis": ai_response,
                    "note": "Could not parse structured data"
                }, indent=2)
        else:
            return json.dumps({
                "status": "error",
                "error": "Failed to get AI analysis"
            }, indent=2)
            
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        }, indent=2)

@mcp.tool(
    name="generate_stakeholder_report",
    annotations={
        "title": "Generate Comprehensive Stakeholder Report",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def generate_stakeholder_report(params: ComprehensiveReportInput) -> str:
    """
    Generate a comprehensive stakeholder analysis report with problems, solutions, and opportunities.
    
    Creates a detailed report including:
    - Stakeholder identification and mapping
    - Problem analysis for each stakeholder
    - Solution recommendations
    - Opportunity identification
    - Executive summary
    
    Args:
        params: ComprehensiveReportInput with report configuration
    
    Returns:
        Formatted report in specified format (markdown/json/html)
    """
    if not OPENAI_API_KEY:
        return json.dumps({
            "status": "error",
            "error": "OPENAI_API_KEY required for comprehensive analysis"
        }, indent=2)
    
    try:
        # Extract project text
        project_text = extract_text_from_files(
            DOC_PATH,
            params.file_pattern,
            params.max_files
        )
        
        if not project_text or project_text.startswith("Error"):
            return json.dumps({
                "status": "error",
                "error": "No project files found",
                "path": str(DOC_PATH)
            }, indent=2)
        
        # Build comprehensive prompt
        sections = []
        if params.include_problems:
            sections.append("problems and challenges for each stakeholder")
        if params.include_solutions:
            sections.append("actionable solutions for identified problems")
        if params.include_opportunities:
            sections.append("opportunities for synergy and collaboration")
        
        prompt = f"""Perform a comprehensive stakeholder analysis of this project.

Analyze and provide:
1. Complete stakeholder identification
{f"2. {sections[0]}" if len(sections) > 0 else ""}
{f"3. {sections[1]}" if len(sections) > 1 else ""}
{f"4. {sections[2]}" if len(sections) > 2 else ""}

Project Description:
{project_text[:10000]}

Return a detailed JSON report with:
- Executive summary
- Stakeholder list with details
- Problem analysis (if requested)
- Solution recommendations (if requested)
- Opportunity assessment (if requested)
- Key insights and recommendations"""
        
        # Get AI analysis
        ai_response = await analyze_with_openai(prompt, max_tokens=4000)
        
        if not ai_response:
            return json.dumps({
                "status": "error",
                "error": "Failed to generate report"
            }, indent=2)
        
        # Parse response
        report_data = parse_json_from_text(ai_response)
        if not report_data:
            report_data = {"raw_analysis": ai_response}
        
        # Format based on requested format
        if params.format == ResponseFormat.JSON:
            return json.dumps(report_data, indent=2)
            
        elif params.format == ResponseFormat.MARKDOWN:
            md = "# Comprehensive Stakeholder Analysis Report\n\n"
            md += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            if "executive_summary" in report_data:
                md += f"## Executive Summary\n\n{report_data['executive_summary']}\n\n"
            
            if "stakeholders" in report_data:
                md += "## Stakeholder Analysis\n\n"
                for sh in report_data.get("stakeholders", []):
                    md += f"### {sh.get('name', 'Unknown')}\n\n"
                    md += f"- **Category:** {sh.get('category', 'N/A')}\n"
                    md += f"- **Role:** {sh.get('role', 'N/A')}\n"
                    md += f"- **Influence:** {sh.get('influence', 'N/A')}\n\n"
            
            return md
            
        elif params.format == ResponseFormat.HTML:
            html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Stakeholder Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        h3 {{ color: #7f8c8d; }}
        .metadata {{ background: #ecf0f1; padding: 10px; border-radius: 5px; margin: 20px 0; }}
        .stakeholder {{ background: #fff; border: 1px solid #ddd; padding: 15px; margin: 15px 0; border-radius: 8px; }}
        .influence-high {{ border-left: 4px solid #e74c3c; }}
        .influence-medium {{ border-left: 4px solid #f39c12; }}
        .influence-low {{ border-left: 4px solid #95a5a6; }}
    </style>
</head>
<body>
    <h1>Comprehensive Stakeholder Analysis</h1>
    <div class="metadata">
        <strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
        <strong>Files Analyzed:</strong> {params.max_files}<br>
        <strong>Pattern:</strong> {params.file_pattern}
    </div>
"""
            
            if "executive_summary" in report_data:
                html += f"<h2>Executive Summary</h2><p>{report_data['executive_summary']}</p>"
            
            if "stakeholders" in report_data:
                html += "<h2>Stakeholders</h2>"
                for sh in report_data.get("stakeholders", []):
                    influence_class = f"influence-{sh.get('influence', 'low').lower()}"
                    html += f"""
    <div class="stakeholder {influence_class}">
        <h3>{sh.get('name', 'Unknown')}</h3>
        <p><strong>Category:</strong> {sh.get('category', 'N/A')}</p>
        <p><strong>Role:</strong> {sh.get('role', 'N/A')}</p>
        <p><strong>Influence Level:</strong> {sh.get('influence', 'N/A')}</p>
    </div>"""
            
            html += "</body></html>"
            return html
            
        else:
            return str(report_data)
            
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "traceback": str(e.__traceback__)
        }, indent=2)

# ============================================================================
# SERVER INITIALIZATION
# ============================================================================

def validate_environment():
    """Validate required environment variables and show warnings."""
    warnings = []
    
    if not OPENAI_API_KEY:
        warnings.append("OPENAI_API_KEY not set - AI analysis features disabled")
    
    if not TAVILY_API_KEY:
        warnings.append("TAVILY_API_KEY not set - Web research features limited")
    
    if not DOC_PATH.exists():
        warnings.append(f"DOC_PATH {DOC_PATH} does not exist - File operations disabled")
        
    return warnings

# Print environment validation on import
warnings = validate_environment()
if warnings:
    print("⚠️  Environment Warnings:")
    for warning in warnings:
        print(f"   - {warning}")
    print()

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    print("🚀 Enhanced GPT-Researcher MCP Server")
    print(f"📁 Document Path: {DOC_PATH}")
    print(f"🤖 AI Model: {SMART_LLM}")
    print(f"🔧 Tools Available: 5")
    print()
    
    # Run the FastMCP server
    mcp.run()
