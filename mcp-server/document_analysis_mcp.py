#!/usr/bin/env python3
"""
Document Analysis & Stakeholder MCP Server
Comprehensive document processing with stakeholder analysis, funding matching, and reporting
Built with FastMCP following MCP best practices
"""

import asyncio
import json
import os
import re
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal, Union
from enum import Enum
import traceback

# MCP and FastMCP imports
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator, ConfigDict
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("document_analysis_mcp")

# Configuration
DOC_PATH = Path(os.getenv('DOC_PATH', 'C:/my_docs'))
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')

# LLM models
STRATEGIC_LLM = os.getenv('STRATEGIC_LLM', 'gpt-4o')
SMART_LLM = os.getenv('SMART_LLM', 'gpt-4o')
FAST_LLM = os.getenv('FAST_LLM', 'gpt-3.5-turbo')

# ============================================================================
# ENUMS
# ============================================================================

class ResponseFormat(str, Enum):
    """Output formats."""
    MARKDOWN = "markdown"
    JSON = "json"
    HTML = "html"
    TEXT = "text"
    PDF = "pdf"

class ReportType(str, Enum):
    """Report types."""
    SUMMARY = "summary"
    DETAILED = "detailed"
    EXECUTIVE = "executive"
    TECHNICAL = "technical"

class SolutionType(str, Enum):
    """Solution types for stakeholder problems."""
    TECHNICAL = "technical"
    ORGANIZATIONAL = "organizational"
    FINANCIAL = "financial"
    ALL = "all"

class OpportunityType(str, Enum):
    """Opportunity types."""
    FUNDING = "funding"
    PARTNERSHIP = "partnership"
    MARKET = "market"
    INNOVATION = "innovation"
    SOCIAL = "social"
    ECONOMIC = "economic"
    ALL = "all"

class StakeholderCategory(str, Enum):
    """Stakeholder categories."""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    INDIRECT = "indirect"
    INTERNAL = "internal"
    EXTERNAL = "external"

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class ReadFileInput(BaseModel):
    """Read file content with safety checks."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    filename: str = Field(
        ...,
        description="Filename in DOC_PATH or relative path",
        min_length=1,
        max_length=255
    )
    max_chars: int = Field(
        default=50000,
        description="Maximum characters to read",
        ge=100,
        le=1000000
    )
    encoding: str = Field(
        default="utf-8",
        description="File encoding (utf-8, latin-1, etc.)"
    )
    
    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """Prevent path traversal attacks."""
        if '..' in v or v.startswith('/') or v.startswith('\\'):
            raise ValueError("Invalid filename - no path traversal allowed")
        return v

class SearchFilesInput(BaseModel):
    """Search text within files."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    search_text: str = Field(
        ...,
        description="Text to search for in files",
        min_length=1,
        max_length=200
    )
    file_pattern: str = Field(
        default="*.txt",
        description="File pattern to search within"
    )
    case_sensitive: bool = Field(
        default=False,
        description="Case-sensitive search"
    )
    max_results: int = Field(
        default=20,
        description="Maximum results to return",
        ge=1,
        le=100
    )

class StakeholderIdentifyInput(BaseModel):
    """Identify stakeholders from project files."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    file_pattern: str = Field(
        default="*.txt",
        description="Pattern for files to analyze"
    )
    max_files: int = Field(
        default=20,
        description="Maximum files to process",
        ge=1,
        le=50
    )
    use_ai_analysis: bool = Field(
        default=True,
        description="Use AI for advanced analysis"
    )
    categories: List[StakeholderCategory] = Field(
        default_factory=lambda: [
            StakeholderCategory.PRIMARY,
            StakeholderCategory.SECONDARY,
            StakeholderCategory.INDIRECT
        ],
        description="Categories to identify"
    )

class StakeholderProblemsInput(BaseModel):
    """Analyze problems for stakeholders."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    file_pattern: str = Field(
        default="*.txt",
        description="Files to analyze"
    )
    stakeholders: Optional[List[str]] = Field(
        default=None,
        description="Specific stakeholders to analyze (None = all)"
    )
    max_files: int = Field(
        default=20,
        ge=1,
        le=50
    )
    use_ai_analysis: bool = Field(
        default=True,
        description="Use AI analysis"
    )

class OpportunitiesInput(BaseModel):
    """Identify opportunities from project analysis."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    file_pattern: str = Field(
        default="*.txt",
        description="Files to analyze"
    )
    max_files: int = Field(
        default=20,
        ge=1,
        le=50
    )
    opportunity_types: List[OpportunityType] = Field(
        default_factory=lambda: [OpportunityType.ALL],
        description="Types of opportunities to identify"
    )
    use_ai_analysis: bool = Field(
        default=True,
        description="Use AI for analysis"
    )

class FundingMatchInput(BaseModel):
    """Find matching funding programs."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    funding_websites: List[str] = Field(
        ...,
        description="URLs of funding websites to search",
        min_items=1,
        max_items=10
    )
    project_files_pattern: str = Field(
        default="*.txt",
        description="Project files to match against"
    )
    max_files_to_analyze: int = Field(
        default=10,
        ge=1,
        le=30
    )
    top_matches: int = Field(
        default=5,
        description="Number of top matches to return",
        ge=1,
        le=20
    )
    
    @field_validator('funding_websites')
    @classmethod
    def validate_urls(cls, v: List[str]) -> List[str]:
        """Validate URLs are properly formatted."""
        for url in v:
            if not url.startswith(('http://', 'https://')):
                raise ValueError(f"Invalid URL: {url}")
        return v

class ComprehensiveReportInput(BaseModel):
    """Generate comprehensive analysis report."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    title: str = Field(
        default="Stakeholder Analysis Report",
        description="Report title",
        max_length=200
    )
    file_pattern: str = Field(
        default="*.txt",
        description="Files to include"
    )
    max_files: int = Field(
        default=20,
        ge=1,
        le=50
    )
    include_problems: bool = Field(
        default=True,
        description="Include problem analysis"
    )
    include_solutions: bool = Field(
        default=True,
        description="Include solutions"
    )
    include_opportunities: bool = Field(
        default=True,
        description="Include opportunities"
    )
    include_metadata: bool = Field(
        default=True,
        description="Include file metadata"
    )
    format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )
    report_type: ReportType = Field(
        default=ReportType.DETAILED,
        description="Report type"
    )

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def call_openai_api(
    prompt: str,
    model: str = None,
    max_tokens: int = 2000,
    temperature: float = 0.7
) -> Optional[str]:
    """Call OpenAI API with error handling."""
    if not OPENAI_API_KEY:
        return None
    
    model = model or SMART_LLM
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OPENAI_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are a professional analyst. Always return structured, actionable insights."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('choices', [{}])[0].get('message', {}).get('content', '')
            else:
                return f"API Error: {response.status_code} - {response.text}"
                
    except httpx.TimeoutException:
        return "API request timed out"
    except Exception as e:
        return f"API Error: {str(e)}"

async def crawl_with_tavily(urls: List[str], max_pages: int = 10) -> Dict:
    """Crawl websites using Tavily API."""
    if not TAVILY_API_KEY:
        return {"error": "TAVILY_API_KEY not configured"}
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            results = []
            
            for url in urls[:max_pages]:
                response = await client.post(
                    "https://api.tavily.com/search",
                    headers={"api-key": TAVILY_API_KEY},
                    json={
                        "query": f"site:{url} funding programs grants",
                        "search_depth": "advanced",
                        "max_results": 10
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results.extend(data.get('results', []))
            
            return {"results": results, "count": len(results)}
            
    except Exception as e:
        return {"error": str(e)}

def extract_text_from_files(
    directory: Path,
    pattern: str = "*",
    max_files: int = 20,
    max_chars_per_file: int = 10000
) -> str:
    """Extract and combine text from multiple files."""
    texts = []
    file_count = 0
    
    try:
        files = list(directory.glob(pattern))[:max_files]
        
        for file_path in files:
            if file_path.is_file() and file_count < max_files:
                try:
                    # Skip binary files
                    if file_path.suffix.lower() in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.rar']:
                        continue
                        
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(max_chars_per_file)
                        if content.strip():
                            texts.append(f"\n=== File: {file_path.name} ===\n{content}\n")
                            file_count += 1
                            
                except Exception as e:
                    continue
                    
    except Exception as e:
        return f"Error reading files: {str(e)}"
    
    if not texts:
        return "No readable text files found"
    
    return '\n'.join(texts)

def parse_json_from_response(text: str) -> Optional[Dict]:
    """Extract JSON from AI response text."""
    if not text:
        return None
    
    try:
        # Direct parse
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Extract from markdown
    patterns = [
        r'```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```',
        r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})',
        r'(\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\])'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
    
    return None

def format_stakeholder_markdown(stakeholder: Dict) -> str:
    """Format stakeholder data as markdown."""
    md = f"### {stakeholder.get('name', 'Unknown Stakeholder')}\n\n"
    md += f"**Category:** {stakeholder.get('category', 'N/A')}\n"
    md += f"**Role:** {stakeholder.get('role', 'N/A')}\n"
    md += f"**Influence:** {stakeholder.get('influence', 'N/A')}\n"
    md += f"**Interest:** {stakeholder.get('interest', 'N/A')}\n\n"
    
    if 'needs' in stakeholder:
        md += "**Needs:**\n"
        for need in stakeholder.get('needs', []):
            md += f"- {need}\n"
        md += "\n"
    
    if 'problems' in stakeholder:
        md += "**Problems:**\n"
        for problem in stakeholder.get('problems', []):
            if isinstance(problem, dict):
                md += f"- {problem.get('description', problem.get('problem', 'N/A'))} "
                md += f"(Severity: {problem.get('severity', 'N/A')})\n"
            else:
                md += f"- {problem}\n"
        md += "\n"
    
    if 'solutions' in stakeholder:
        md += "**Solutions:**\n"
        for solution in stakeholder.get('solutions', []):
            if isinstance(solution, dict):
                md += f"- {solution.get('description', solution.get('solution', 'N/A'))} "
                md += f"(Type: {solution.get('type', 'N/A')})\n"
            else:
                md += f"- {solution}\n"
        md += "\n"
    
    return md

# ============================================================================
# TOOL IMPLEMENTATIONS
# ============================================================================

@mcp.tool(
    name="read_file_content",
    annotations={
        "title": "Read File Content Safely",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def read_file_content(params: ReadFileInput) -> str:
    """
    Read and return content of a specific file with safety checks.
    
    Safely reads file content with:
    - Path traversal prevention
    - Size limits
    - Encoding handling
    - Binary file detection
    
    Args:
        params: ReadFileInput with filename and read configuration
    
    Returns:
        JSON with file content or error message
    """
    try:
        # Construct safe path
        file_path = DOC_PATH / params.filename
        
        # Verify file is within DOC_PATH
        if not file_path.resolve().is_relative_to(DOC_PATH.resolve()):
            return json.dumps({
                "status": "error",
                "error": "Access denied - file outside allowed directory"
            }, indent=2)
        
        if not file_path.exists():
            return json.dumps({
                "status": "error",
                "error": f"File not found: {params.filename}"
            }, indent=2)
        
        if not file_path.is_file():
            return json.dumps({
                "status": "error",
                "error": "Path is not a file"
            }, indent=2)
        
        # Get file info
        stat = file_path.stat()
        
        # Check if likely binary
        binary_extensions = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.rar', '.jpg', '.png', '.exe'}
        if file_path.suffix.lower() in binary_extensions:
            return json.dumps({
                "status": "error",
                "error": "Binary file detected",
                "suggestion": "This appears to be a binary file that cannot be read as text"
            }, indent=2)
        
        # Read file
        try:
            with open(file_path, 'r', encoding=params.encoding, errors='replace') as f:
                content = f.read(params.max_chars)
                
            truncated = len(content) == params.max_chars
            
            return json.dumps({
                "status": "success",
                "filename": params.filename,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "encoding": params.encoding,
                "truncated": truncated,
                "content": content,
                "char_count": len(content)
            }, indent=2)
            
        except UnicodeDecodeError:
            return json.dumps({
                "status": "error",
                "error": "File encoding error",
                "suggestion": f"Try different encoding (current: {params.encoding}). Common: utf-8, latin-1, cp1252"
            }, indent=2)
            
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        }, indent=2)

@mcp.tool(
    name="search_in_files",
    annotations={
        "title": "Search Text in Files",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def search_in_files(params: SearchFilesInput) -> str:
    """
    Search for text within files matching a pattern.
    
    Features:
    - Case-sensitive/insensitive search
    - Context around matches
    - Multiple file support
    - Line number tracking
    
    Args:
        params: SearchFilesInput with search text and options
    
    Returns:
        JSON with search results and context
    """
    try:
        files = list(DOC_PATH.glob(params.file_pattern))[:params.max_results]
        results = []
        
        search_text = params.search_text if params.case_sensitive else params.search_text.lower()
        
        for file_path in files:
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    
                    matches = []
                    for i, line in enumerate(lines, 1):
                        compare_line = line if params.case_sensitive else line.lower()
                        if search_text in compare_line:
                            # Get context (previous and next line)
                            context = {
                                "line_number": i,
                                "text": line.strip(),
                                "before": lines[i-2].strip() if i > 1 else None,
                                "after": lines[i].strip() if i < len(lines) else None
                            }
                            matches.append(context)
                    
                    if matches:
                        results.append({
                            "file": file_path.name,
                            "path": str(file_path.relative_to(DOC_PATH)),
                            "matches": len(matches),
                            "contexts": matches[:5]  # Limit contexts per file
                        })
                        
                except Exception:
                    continue
        
        return json.dumps({
            "status": "success",
            "search_text": params.search_text,
            "case_sensitive": params.case_sensitive,
            "files_searched": len(files),
            "files_with_matches": len(results),
            "results": results
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        }, indent=2)

@mcp.tool(
    name="identify_stakeholders",
    annotations={
        "title": "Identify Project Stakeholders with AI",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def identify_stakeholders(params: StakeholderIdentifyInput) -> str:
    """
    Identify and categorize all project stakeholders using AI analysis.
    
    Analyzes project documents to identify:
    - Primary stakeholders (direct involvement)
    - Secondary stakeholders (indirect involvement)  
    - Internal vs External stakeholders
    - Their roles, interests, and influence levels
    
    Args:
        params: StakeholderIdentifyInput with file pattern and categories
    
    Returns:
        JSON with comprehensive stakeholder mapping
    """
    if not params.use_ai_analysis:
        return json.dumps({
            "status": "error",
            "message": "AI analysis is required for stakeholder identification"
        }, indent=2)
    
    if not OPENAI_API_KEY:
        return json.dumps({
            "status": "error",
            "error": "OPENAI_API_KEY required for AI analysis"
        }, indent=2)
    
    try:
        # Extract project text
        project_text = extract_text_from_files(
            DOC_PATH,
            params.file_pattern,
            params.max_files,
            15000
        )
        
        if project_text.startswith("Error") or project_text == "No readable text files found":
            return json.dumps({
                "status": "error",
                "error": project_text,
                "path": str(DOC_PATH),
                "pattern": params.file_pattern
            }, indent=2)
        
        # Prepare categories for prompt
        categories_str = ', '.join([cat.value for cat in params.categories])
        
        # AI prompt
        prompt = f"""Analyze the following project documents to identify ALL stakeholders.

Categories to identify: {categories_str}

For each stakeholder, determine:
1. Name/Title (specific individual or group)
2. Category (primary/secondary/indirect/internal/external)
3. Role in the project
4. Their main interests/concerns
5. Level of influence (high/medium/low)
6. What they need from the project
7. Their expectations

Project Documents:
{project_text[:12000]}

Return a comprehensive JSON response:
{{
    "stakeholders": [
        {{
            "name": "stakeholder name/title",
            "category": "category",
            "role": "their specific role",
            "interest": "main interests",
            "influence": "high/medium/low",
            "power": "decision-making power level",
            "needs": ["need1", "need2"],
            "expectations": ["expectation1", "expectation2"],
            "potential_issues": ["issue1", "issue2"]
        }}
    ],
    "summary": "executive summary of stakeholder landscape",
    "key_relationships": ["relationship1", "relationship2"],
    "critical_stakeholders": ["most important stakeholders"],
    "total_identified": number
}}"""
        
        # Get AI analysis
        ai_response = await call_openai_api(prompt, model=SMART_LLM, max_tokens=3000)
        
        if not ai_response:
            return json.dumps({
                "status": "error",
                "error": "Failed to get AI analysis"
            }, indent=2)
        
        # Parse response
        parsed = parse_json_from_response(ai_response)
        
        if parsed:
            # Add metadata
            parsed["metadata"] = {
                "analysis_date": datetime.now().isoformat(),
                "files_analyzed": params.max_files,
                "categories_searched": categories_str,
                "ai_model": SMART_LLM
            }
            return json.dumps(parsed, indent=2)
        else:
            # Return raw analysis if parsing fails
            return json.dumps({
                "status": "partial",
                "raw_analysis": ai_response,
                "note": "Could not parse structured data, showing raw analysis"
            }, indent=2)
            
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }, indent=2)

@mcp.tool(
    name="analyze_stakeholder_problems",
    annotations={
        "title": "Analyze Stakeholder Problems",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def analyze_stakeholder_problems(params: StakeholderProblemsInput) -> str:
    """
    Identify and analyze problems/challenges for each stakeholder.
    
    Deep analysis of:
    - Current pain points
    - Barriers to engagement
    - Conflicting interests
    - Resource constraints
    - Risk factors
    
    Args:
        params: StakeholderProblemsInput with stakeholders and analysis options
    
    Returns:
        JSON with detailed problem analysis per stakeholder
    """
    if not params.use_ai_analysis or not OPENAI_API_KEY:
        return json.dumps({
            "status": "error",
            "error": "AI analysis with OPENAI_API_KEY required"
        }, indent=2)
    
    try:
        # Extract project text
        project_text = extract_text_from_files(
            DOC_PATH,
            params.file_pattern,
            params.max_files,
            15000
        )
        
        if project_text.startswith("Error"):
            return json.dumps({
                "status": "error",
                "error": project_text
            }, indent=2)
        
        # Build stakeholder context
        stakeholder_context = ""
        if params.stakeholders:
            stakeholder_context = f"Focus on these stakeholders: {', '.join(params.stakeholders)}\n"
        
        prompt = f"""Analyze the project to identify problems and challenges for stakeholders.

{stakeholder_context}

For each stakeholder or stakeholder group, identify:
1. Current problems they face
2. Challenges in the project context
3. Barriers to their participation
4. Conflicting interests with other stakeholders
5. Resource or capability constraints
6. Risk factors affecting them

Project Context:
{project_text[:12000]}

Return detailed JSON:
{{
    "stakeholder_problems": [
        {{
            "stakeholder": "name/group",
            "problems": [
                {{
                    "problem": "description",
                    "severity": "high/medium/low",
                    "impact": "impact description",
                    "root_cause": "underlying cause",
                    "affected_areas": ["area1", "area2"]
                }}
            ],
            "barriers": ["barrier1", "barrier2"],
            "conflicts": ["conflict1", "conflict2"],
            "constraints": ["constraint1", "constraint2"],
            "risk_level": "high/medium/low"
        }}
    ],
    "common_problems": ["problems affecting multiple stakeholders"],
    "critical_issues": ["most urgent problems to address"],
    "problem_summary": "executive summary"
}}"""
        
        ai_response = await call_openai_api(prompt, model=SMART_LLM, max_tokens=3500)
        
        if not ai_response:
            return json.dumps({
                "status": "error",
                "error": "Failed to analyze problems"
            }, indent=2)
        
        parsed = parse_json_from_response(ai_response)
        
        if parsed:
            parsed["metadata"] = {
                "analysis_date": datetime.now().isoformat(),
                "focused_stakeholders": params.stakeholders or "all"
            }
            return json.dumps(parsed, indent=2)
        else:
            return json.dumps({
                "status": "partial",
                "raw_analysis": ai_response
            }, indent=2)
            
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        }, indent=2)

@mcp.tool(
    name="identify_opportunities",
    annotations={
        "title": "Identify Project Opportunities",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def identify_opportunities(params: OpportunitiesInput) -> str:
    """
    Identify opportunities, synergies, and potential benefits from the project.
    
    Analyzes for:
    - Funding opportunities
    - Partnership possibilities
    - Market opportunities
    - Innovation potential
    - Social impact opportunities
    - Economic benefits
    
    Args:
        params: OpportunitiesInput with opportunity types to identify
    
    Returns:
        JSON with categorized opportunities and recommendations
    """
    if not params.use_ai_analysis or not OPENAI_API_KEY:
        return json.dumps({
            "status": "error",
            "error": "AI analysis required"
        }, indent=2)
    
    try:
        project_text = extract_text_from_files(
            DOC_PATH,
            params.file_pattern,
            params.max_files,
            15000
        )
        
        if project_text.startswith("Error"):
            return json.dumps({
                "status": "error",
                "error": project_text
            }, indent=2)
        
        # Build opportunity types context
        if OpportunityType.ALL in params.opportunity_types:
            opp_types = "all types (funding, partnership, market, innovation, social, economic)"
        else:
            opp_types = ', '.join([t.value for t in params.opportunity_types])
        
        prompt = f"""Analyze the project to identify opportunities and synergies.

Focus on these opportunity types: {opp_types}

Identify:
1. Funding opportunities (grants, investments, revenue streams)
2. Partnership opportunities (collaborations, alliances)
3. Market opportunities (new markets, customer segments)
4. Innovation opportunities (new solutions, improvements)
5. Social impact opportunities (community benefits)
6. Economic opportunities (cost savings, efficiency gains)

Project Information:
{project_text[:12000]}

Return comprehensive JSON:
{{
    "opportunities": [
        {{
            "opportunity": "description",
            "type": "funding/partnership/market/innovation/social/economic",
            "impact": "high/medium/low",
            "timeframe": "short/medium/long-term",
            "requirements": ["requirement1", "requirement2"],
            "stakeholders_involved": ["stakeholder1", "stakeholder2"],
            "potential_value": "estimated value or benefit",
            "implementation_difficulty": "easy/moderate/difficult",
            "risks": ["risk1", "risk2"]
        }}
    ],
    "synergies": [
        {{
            "description": "synergy description",
            "stakeholders": ["involved parties"],
            "mutual_benefits": ["benefit1", "benefit2"]
        }}
    ],
    "quick_wins": ["opportunities that can be implemented quickly"],
    "strategic_opportunities": ["long-term strategic opportunities"],
    "recommendations": ["action1", "action2"],
    "summary": "executive summary of opportunities"
}}"""
        
        ai_response = await call_openai_api(prompt, model=SMART_LLM, max_tokens=3500)
        
        if not ai_response:
            return json.dumps({
                "status": "error",
                "error": "Failed to identify opportunities"
            }, indent=2)
        
        parsed = parse_json_from_response(ai_response)
        
        if parsed:
            parsed["metadata"] = {
                "analysis_date": datetime.now().isoformat(),
                "opportunity_types": opp_types,
                "files_analyzed": params.max_files
            }
            return json.dumps(parsed, indent=2)
        else:
            return json.dumps({
                "status": "partial",
                "raw_analysis": ai_response
            }, indent=2)
            
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        }, indent=2)

@mcp.tool(
    name="find_matching_funding",
    annotations={
        "title": "Find Matching Funding Programs",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def find_matching_funding(params: FundingMatchInput) -> str:
    """
    Find and match funding programs to your project using AI and web search.
    
    Features:
    - Crawls funding websites with Tavily
    - Extracts funding requirements
    - Matches against project characteristics
    - Ranks by compatibility score
    
    Args:
        params: FundingMatchInput with funding URLs and project files
    
    Returns:
        JSON with ranked funding matches and recommendations
    """
    if not TAVILY_API_KEY or not OPENAI_API_KEY:
        return json.dumps({
            "status": "error",
            "error": "Both TAVILY_API_KEY and OPENAI_API_KEY required"
        }, indent=2)
    
    try:
        # Extract project information
        project_text = extract_text_from_files(
            DOC_PATH,
            params.project_files_pattern,
            params.max_files_to_analyze,
            20000
        )
        
        if project_text.startswith("Error"):
            return json.dumps({
                "status": "error",
                "error": project_text
            }, indent=2)
        
        # Crawl funding websites
        crawl_results = await crawl_with_tavily(
            params.funding_websites,
            max_pages=20
        )
        
        if "error" in crawl_results:
            return json.dumps({
                "status": "error",
                "error": f"Crawling failed: {crawl_results['error']}"
            }, indent=2)
        
        # Prepare funding data for analysis
        funding_data = json.dumps(crawl_results.get('results', [])[:10], indent=2)[:8000]
        
        # AI matching prompt
        prompt = f"""Match funding programs to the project based on compatibility.

PROJECT DESCRIPTION:
{project_text[:6000]}

FUNDING PROGRAMS DATA:
{funding_data}

Analyze each funding program and:
1. Extract key requirements and criteria
2. Match against project characteristics
3. Calculate compatibility score (0-100)
4. Identify gaps or missing requirements
5. Provide recommendations

Return detailed JSON:
{{
    "matches": [
        {{
            "program_name": "funding program name",
            "source_url": "URL",
            "compatibility_score": 85,
            "eligible": true/false,
            "requirements_met": ["req1", "req2"],
            "requirements_missing": ["req1", "req2"],
            "funding_amount": "amount or range",
            "deadline": "deadline if known",
            "recommendations": ["how to improve eligibility"],
            "next_steps": ["action1", "action2"]
        }}
    ],
    "best_matches": ["top 3 program names"],
    "immediate_actions": ["urgent actions needed"],
    "summary": "executive summary of funding opportunities"
}}"""
        
        ai_response = await call_openai_api(prompt, model=STRATEGIC_LLM, max_tokens=4000)
        
        if not ai_response:
            return json.dumps({
                "status": "error",
                "error": "Failed to analyze funding matches"
            }, indent=2)
        
        parsed = parse_json_from_response(ai_response)
        
        if parsed:
            # Sort by compatibility score
            if "matches" in parsed:
                parsed["matches"] = sorted(
                    parsed["matches"],
                    key=lambda x: x.get("compatibility_score", 0),
                    reverse=True
                )[:params.top_matches]
            
            parsed["metadata"] = {
                "analysis_date": datetime.now().isoformat(),
                "websites_searched": len(params.funding_websites),
                "programs_analyzed": crawl_results.get('count', 0)
            }
            
            return json.dumps(parsed, indent=2)
        else:
            return json.dumps({
                "status": "partial",
                "crawl_results": crawl_results.get('count', 0),
                "raw_analysis": ai_response
            }, indent=2)
            
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        }, indent=2)

@mcp.tool(
    name="generate_comprehensive_report",
    annotations={
        "title": "Generate Comprehensive Analysis Report",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def generate_comprehensive_report(params: ComprehensiveReportInput) -> str:
    """
    Generate a comprehensive stakeholder analysis report with all components.
    
    Includes:
    - Executive summary
    - Stakeholder mapping
    - Problem analysis
    - Solution recommendations
    - Opportunity assessment
    - Action plan
    - Risk analysis
    
    Args:
        params: ComprehensiveReportInput with report configuration
    
    Returns:
        Formatted report in requested format (markdown/json/html)
    """
    if not OPENAI_API_KEY:
        return json.dumps({
            "status": "error",
            "error": "OPENAI_API_KEY required for report generation"
        }, indent=2)
    
    try:
        # Extract project text
        project_text = extract_text_from_files(
            DOC_PATH,
            params.file_pattern,
            params.max_files,
            20000
        )
        
        if project_text.startswith("Error"):
            return json.dumps({
                "status": "error",
                "error": project_text
            }, indent=2)
        
        # Build comprehensive prompt based on options
        sections = []
        if params.include_problems:
            sections.append("stakeholder problems and challenges")
        if params.include_solutions:
            sections.append("actionable solutions and recommendations")
        if params.include_opportunities:
            sections.append("opportunities and synergies")
        
        report_style = {
            ReportType.SUMMARY: "concise summary with key points only",
            ReportType.DETAILED: "comprehensive analysis with full details",
            ReportType.EXECUTIVE: "executive-level overview with strategic insights",
            ReportType.TECHNICAL: "technical analysis with implementation details"
        }.get(params.report_type, "detailed analysis")
        
        prompt = f"""Generate a {report_style} stakeholder analysis report.

Include these sections:
1. Executive Summary
2. Stakeholder Identification and Mapping
{f"3. {sections[0]}" if len(sections) > 0 else ""}
{f"4. {sections[1]}" if len(sections) > 1 else ""}
{f"5. {sections[2]}" if len(sections) > 2 else ""}
6. Recommendations and Action Plan
7. Risk Assessment
8. Conclusion

Project Information:
{project_text[:15000]}

Return comprehensive JSON report:
{{
    "title": "{params.title}",
    "executive_summary": "comprehensive overview",
    "stakeholders": [
        {{
            "name": "stakeholder",
            "category": "category",
            "role": "role",
            "influence": "level",
            "interest": "interests",
            "problems": ["problem1"] (if requested),
            "solutions": ["solution1"] (if requested)
        }}
    ],
    "problems_analysis": {{...}} (if requested),
    "solutions_framework": {{...}} (if requested),
    "opportunities": [{{...}}] (if requested),
    "recommendations": [
        {{
            "recommendation": "description",
            "priority": "high/medium/low",
            "timeframe": "immediate/short/long-term",
            "responsible": "who should act",
            "resources_needed": ["resource1"]
        }}
    ],
    "action_plan": [
        {{
            "phase": "phase name",
            "activities": ["activity1"],
            "timeline": "timeframe",
            "deliverables": ["deliverable1"]
        }}
    ],
    "risks": [
        {{
            "risk": "description",
            "probability": "high/medium/low",
            "impact": "high/medium/low",
            "mitigation": "strategy"
        }}
    ],
    "conclusion": "final thoughts and next steps",
    "appendices": {{...}}
}}"""
        
        ai_response = await call_openai_api(
            prompt,
            model=STRATEGIC_LLM,
            max_tokens=5000,
            temperature=0.6
        )
        
        if not ai_response:
            return json.dumps({
                "status": "error",
                "error": "Failed to generate report"
            }, indent=2)
        
        report_data = parse_json_from_response(ai_response)
        if not report_data:
            report_data = {"raw_content": ai_response}
        
        # Add metadata
        report_data["metadata"] = {
            "generated": datetime.now().isoformat(),
            "report_type": params.report_type.value,
            "files_analyzed": params.max_files,
            "ai_model": STRATEGIC_LLM
        }
        
        # Format based on requested format
        if params.format == ResponseFormat.JSON:
            return json.dumps(report_data, indent=2)
            
        elif params.format == ResponseFormat.MARKDOWN:
            # Convert to markdown
            md = f"# {params.title}\n\n"
            md += f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
            
            if "executive_summary" in report_data:
                md += f"## Executive Summary\n\n{report_data['executive_summary']}\n\n"
            
            if "stakeholders" in report_data:
                md += "## Stakeholder Analysis\n\n"
                
                # Group by category
                by_category = {}
                for sh in report_data.get("stakeholders", []):
                    cat = sh.get("category", "Other")
                    if cat not in by_category:
                        by_category[cat] = []
                    by_category[cat].append(sh)
                
                for category, stakeholders in by_category.items():
                    md += f"### {category.title()} Stakeholders\n\n"
                    for sh in stakeholders:
                        md += format_stakeholder_markdown(sh)
            
            if params.include_problems and "problems_analysis" in report_data:
                md += "## Problems Analysis\n\n"
                problems = report_data.get("problems_analysis", {})
                if isinstance(problems, dict):
                    for key, value in problems.items():
                        md += f"### {key}\n{value}\n\n"
            
            if params.include_solutions and "solutions_framework" in report_data:
                md += "## Solutions Framework\n\n"
                solutions = report_data.get("solutions_framework", {})
                if isinstance(solutions, dict):
                    for key, value in solutions.items():
                        md += f"### {key}\n{value}\n\n"
            
            if params.include_opportunities and "opportunities" in report_data:
                md += "## Opportunities\n\n"
                for opp in report_data.get("opportunities", []):
                    if isinstance(opp, dict):
                        md += f"### {opp.get('opportunity', 'Opportunity')}\n"
                        md += f"- **Type:** {opp.get('type', 'N/A')}\n"
                        md += f"- **Impact:** {opp.get('impact', 'N/A')}\n"
                        md += f"- **Timeframe:** {opp.get('timeframe', 'N/A')}\n\n"
            
            if "recommendations" in report_data:
                md += "## Recommendations\n\n"
                for rec in report_data.get("recommendations", []):
                    if isinstance(rec, dict):
                        md += f"### {rec.get('recommendation', 'Recommendation')}\n"
                        md += f"- **Priority:** {rec.get('priority', 'N/A')}\n"
                        md += f"- **Timeframe:** {rec.get('timeframe', 'N/A')}\n"
                        md += f"- **Responsible:** {rec.get('responsible', 'N/A')}\n\n"
            
            if "conclusion" in report_data:
                md += f"## Conclusion\n\n{report_data['conclusion']}\n"
            
            return md
            
        elif params.format == ResponseFormat.HTML:
            # Convert to HTML
            html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{params.title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .report-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        h1 {{ margin: 0; font-size: 2.5em; }}
        .metadata {{
            opacity: 0.9;
            margin-top: 10px;
        }}
        section {{
            background: white;
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h2 {{
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        h3 {{ color: #555; }}
        .stakeholder {{
            border-left: 4px solid #667eea;
            padding-left: 15px;
            margin: 20px 0;
        }}
        .priority-high {{ color: #e74c3c; font-weight: bold; }}
        .priority-medium {{ color: #f39c12; }}
        .priority-low {{ color: #95a5a6; }}
        ul {{ list-style-type: none; padding-left: 0; }}
        li {{ 
            padding: 5px 0;
            border-bottom: 1px solid #eee;
        }}
        .recommendation {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
        }}
    </style>
</head>
<body>
    <div class="report-header">
        <h1>{params.title}</h1>
        <div class="metadata">
            Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}
        </div>
    </div>
"""
            
            if "executive_summary" in report_data:
                html += f"""
    <section>
        <h2>Executive Summary</h2>
        <p>{report_data['executive_summary']}</p>
    </section>"""
            
            if "stakeholders" in report_data:
                html += """
    <section>
        <h2>Stakeholder Analysis</h2>"""
                
                for sh in report_data.get("stakeholders", []):
                    html += f"""
        <div class="stakeholder">
            <h3>{sh.get('name', 'Unknown')}</h3>
            <p><strong>Category:</strong> {sh.get('category', 'N/A')}</p>
            <p><strong>Role:</strong> {sh.get('role', 'N/A')}</p>
            <p><strong>Influence:</strong> {sh.get('influence', 'N/A')}</p>
        </div>"""
                
                html += """
    </section>"""
            
            html += """
</body>
</html>"""
            
            return html
            
        else:
            # Plain text format
            return json.dumps(report_data, indent=2)
            
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }, indent=2)

# ============================================================================
# STARTUP AND VALIDATION
# ============================================================================

def validate_environment() -> List[str]:
    """Validate environment and return warnings."""
    warnings = []
    
    if not OPENAI_API_KEY:
        warnings.append("⚠️  OPENAI_API_KEY not set - AI features disabled")
    
    if not TAVILY_API_KEY:
        warnings.append("⚠️  TAVILY_API_KEY not set - Web search disabled")
    
    if not DOC_PATH.exists():
        warnings.append(f"⚠️  DOC_PATH {DOC_PATH} not found")
        try:
            DOC_PATH.mkdir(parents=True, exist_ok=True)
            warnings.append(f"✅ Created directory: {DOC_PATH}")
        except Exception as e:
            warnings.append(f"❌ Could not create directory: {e}")
    
    return warnings

# Print startup information
if __name__ == "__main__":
    print("=" * 60)
    print("📚 Document Analysis & Stakeholder MCP Server")
    print("=" * 60)
    print(f"📁 Document Path: {DOC_PATH}")
    print(f"🤖 AI Model: {SMART_LLM}")
    print(f"🔧 Tools Available: 7 specialized tools")
    print("-" * 60)
    
    # Validate environment
    warnings = validate_environment()
    if warnings:
        print("Environment Status:")
        for warning in warnings:
            print(f"  {warning}")
        print("-" * 60)
    
    print("\n✅ Server ready! Starting FastMCP...\n")
    
    # Run the server
    mcp.run()
