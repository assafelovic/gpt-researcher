import os
from openai import OpenAI
from dotenv import load_dotenv
import json
# Load environment variables
load_dotenv()

# Configuration
O1_MODEL = 'o3-mini-2025-01-31'
api_key = os.getenv("OPENAI_API_KEY")
o1_client = OpenAI(api_key=api_key)

api_insights = {
        "pipeline_analysis": {
            "insights": "Use Drugs Intelligence (Slide 6 & 7) for pipeline programs. Can sort by Molecule Type under Drug Details. Get MoA and Targets information.",
            "filters": "Focus on antibody-based therapeutics (mAbs, ADCs, bispecific antibodies)",
            "additional_data": "Include current assets, discontinued/terminated programs, and preclinical collaborations"
        },
        "partnership_analysis": {
            "insights": "Use Fundamental Intelligence > Deals > Company ID Search for partnership details. Search affiliated drugs for comprehensive view.",
            "scope": "Include acquisitions, in-licensing agreements, option agreements, and collaborations",
            "details": "Get licensing terms, scope, exercised options, and remaining rights information"
        },
        "target_identification": {
            "insights": "Get targets from MoA or Targets fields in Drugs Intelligence. Use Deals data for access rights via acquisitions and licensing.",
            "classification": "Determine full rights, partial/limited rights, or optioned/future rights",
            "limitations": "Check for restrictions (ADCs only, geographic limitations, co-development obligations)"
        },
        "competitive_landscape": {
            "insights": "Search by target in Drugs Intelligence section to understand competitive landscape",
            "analysis": "Evaluate how crowded or differentiated each target is",
            "benchmarking": "Compare against existing pipeline and marketed assets"
        },
        "epidemiology_analysis": {
            "insights": "Use Therapeutic Analysis > Epidemiology (slide 27) for BMI categories and patient segmentation",
            "segmentation": "Analyze by BMI categories (Class I: 30-35, Class II: 35-40, Class III: ≥40)",
            "subgroups": "Segment by diabetes status, prior bariatric surgery, treatment response"
        },
        "market_analysis": {
            "insights": "Use Drugs Intelligence Pipeline (Slide 10) for drug sales and consensus forecasts",
            "forecasting": "Focus on therapies with long-term administration profiles (≥12 months)",
            "pricing": "Use Pricing Intelligence for commercial segmentation and payer differentiation"
        },
        "clinical_trials": {
            "insights": "Use Drugs Intelligence Pipeline + Trials Intelligence for trial design characteristics",
            "analysis": "Focus on time to intervention post-MI, target populations, primary endpoints",
            "geographic": "Consider differences in standards of care across US, EU, China"
        },
        "deal_landscape": {
            "insights": "Use Fundamental Intelligence > Deals (slide 30) for commercial benchmarks",
            "scope": "Include recent deal terms, partnerships, exits for relevant assets",
            "analysis": "Evaluate deal activity trends and market movements"
        }
}

def generate_research_plan(query: str) -> str:
    """
    Generate a comprehensive research plan in markdown format using OpenAI's O1 model.
    
    Args:
        query: The research query string
        
    Returns:
        Markdown formatted research plan
    """
    prompt = f"""
    You are an expert research strategist. Create a comprehensive, methodical research plan for the following query.

    ---

    ## 🧰 Available Research Tools:
    1. **OpenAI File Search Tool** – Search and analyze uploaded knowledge base files (PDFs, documents, datasets)
    2. **GlobalData APIs** – Access pharmaceutical and biotech intelligence:
    - **Pharma Intelligence API** – Drug pipelines, clinical trials, regulatory approvals
    - **Deals Intelligence API** – Licensing, partnerships, M&A transactions
    - **Clinical Trials Intelligence API** – Trial data, endpoints, populations
    - **Patent Intelligence API** – IP landscape, expiry dates
    - **Company Intelligence API** – Profiles, financials, strategic focus
    - **Competitive Intelligence API** – Market positioning, competitors
    - **Regulatory Intelligence API** – Submissions, approvals, guidance

    ---

    ## 🔍 Research Planning Framework:
    **Incorporate the user insights** provided below. These reflect proven successful approaches and should guide sub-query development.

    Generate:
    1. **Primary Sub-query**: The main, actionable research question for this section (based on user insights)
    2. **Comprehensive Sub-query**: Broader, detailed query to cover all related aspects and nuances
    3. **3–5 Keywords** for GlobalData API calls:
    - Include **1–2 disease-specific keywords** (e.g., "non-small cell lung cancer", "cancer")
    4. **Rationale** (2–3 sentences): Explain why this section is relevant and how it aligns with user insights

    ---

    ## ⚙️ Consider the Following:
    - Specific data filtering/sorting capabilities
    - Proven data sources and methods
    - Limitations and known risks
    - Integration with other data sources/tools

    ---

    ## 🧠 Research Query:
    ```text
    {query}

    📌 USER INSIGHTS FOR THIS SECTION:

    {api_insights}

    🧭 Required Research Plan Structure:
    1. Research Objective & Scope
    - Primary research question(s)
    - Success criteria & deliverables
    - Timeline and resource needs
    2. Phase-by-Phase Research Strategy
    Phase 1: Knowledge Base Analysis
    - 1a. File search strategy (internal knowledge base)
    - 1b. Keywords and query patterns
    - 1c. Info extraction & categorization approach
    Phase 2: Global Data Intelligence Collection
    -  2a. Pipeline Intelligence – Use Pharma Intelligence API
    -  2b. Deal Intelligence – Search Deals API for licensing/partnerships
    -  2c. Clinical Intelligence – Pull from Clinical Trials API
    -  2d. Patent Intelligence – Analyze IP data
    -  2e. Competitive Intelligence – Understand competitive positioning
    Phase 3: Data Integration & Cross-Validation
    - 3a. Cross-check internal files with GlobalData findings
    - 3b. Confirm deal terms via Deals Intelligence
    - 3c. Validate clinical progress via multiple APIs
    - 3d. Identify data gaps and prioritize further research
    🎯 Specific Research Strategies

    Specify for each phase:

        File Search Queries: Exact internal search terms
        GlobalData API Calls:
            Endpoint names
            Filters (e.g., company, drug type, indication, time range)
        Cross-validation logic: Match findings across multiple sources

    📤 Respond in the following JSON format:
    """
    try:
        # Generate plan using O1 model
        response = o1_client.chat.completions.create(
            model=O1_MODEL,
            messages=[{'role': 'user', 'content': prompt}]
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error generating research plan: {str(e)}"