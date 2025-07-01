import openai
from typing import Dict, List, Optional, Tuple
import json
import re
from dataclasses import dataclass
from enum import Enum

class ReportSection(Enum):
    DISEASE_OVERVIEW = "disease_overview"
    EPIDEMIOLOGY = "epidemiology"
    COMPETITIVE_LANDSCAPE = "competitive_landscape"
    DEAL_LANDSCAPE = "deal_landscape"
    TARGET_PRODUCT_PROFILE = "target_product_profile"
    MARKET_MODEL = "market_model"
    CLINICAL_DEVELOPMENT = "clinical_development"
    KOLS = "kols"

@dataclass
class SectionAnalysis:
    section: ReportSection
    relevance_score: float
    sub_queries: List[str]
    keywords: List[str]
    api_endpoints: List[str]
    rationale: str

@dataclass
class QueryAnalysisResult:
    original_query: str
    detected_sections: List[SectionAnalysis]
    primary_focus: str
    secondary_focuses: List[str]
    overall_complexity: str

class AIAgentQueryPipeline:
    def __init__(self, openai_api_key: str, model: str = "gpt-4"):
        """
        Initialize the AI Agent Query Pipeline
        
        Args:
            openai_api_key: OpenAI API key
            model: OpenAI model to use (default: gpt-4)
        """
        self.client = openai.OpenAI(api_key=openai_api_key)
        self.model = model
        
        # Define section characteristics and keywords
        self.section_mapping = {
            ReportSection.DISEASE_OVERVIEW: {
                "keywords": ["disease", "symptoms", "diagnosis", "etiology", "pathology", "treatment paradigm", "unmet needs", "patient segments"],
                "api_endpoints": ["StatPearls", "PubMed", "UpToDate", "NCCN Guidelines"],
                "persona": "MD, PhD with specialization in relevant disease"
            },
            ReportSection.EPIDEMIOLOGY: {
                "keywords": ["prevalence", "incidence", "epidemiology", "patient population", "demographics", "geography", "forecast"],
                "api_endpoints": ["GlobalData Epi Forecasts", "PubMed", "AlphaSense"],
                "persona": "PhD epidemiologist"
            },
            ReportSection.COMPETITIVE_LANDSCAPE: {
                "keywords": ["pipeline", "competitors", "drugs", "clinical trials", "market share", "pricing", "reimbursement", "assets"],
                "api_endpoints": ["GlobalData", "Cortellis", "PharmaProjects", "ClinicalTrials.gov"],
                "persona": "Wall street analyst with biotech focus"
            },
            ReportSection.DEAL_LANDSCAPE: {
                "keywords": ["deals", "licensing", "partnerships", "acquisitions", "M&A", "collaborations", "investment", "financing"],
                "api_endpoints": ["GlobalData Deals", "Pitchbook", "BioSciDB", "AlphaSense"],
                "persona": "Wall street analyst with biotech focus"
            },
            ReportSection.TARGET_PRODUCT_PROFILE: {
                "keywords": ["target product profile", "TPP", "differentiation", "endpoints", "dosing", "route of administration", "comparator"],
                "api_endpoints": ["ClinicalTrials.gov", "PubMed", "GlobalData Reports"],
                "persona": "Chief medical officer of pharmaceutical company"
            },
            ReportSection.MARKET_MODEL: {
                "keywords": ["market size", "revenue forecast", "sales", "pricing", "market penetration", "addressable market"],
                "api_endpoints": ["AlphaSense", "GlobalData Market Models", "PubMed"],
                "persona": "Wall street analyst with biotech focus"
            },
            ReportSection.CLINICAL_DEVELOPMENT: {
                "keywords": ["clinical trial design", "endpoints", "biomarkers", "enrollment", "PoS", "budget", "recruitment"],
                "api_endpoints": ["ClinicalTrials.gov", "GlobalData Clinical Data", "PubMed"],
                "persona": "Chief medical officer with clinical trial experience"
            },
            ReportSection.KOLS: {
                "keywords": ["key opinion leaders", "KOLs", "investigators", "experts", "consultants", "clinical trial experience"],
                "api_endpoints": ["GlobalData Investigator Database", "Google Search"],
                "persona": "Business development associate"
            }
        }

    def analyze_query(self, user_query: str) -> QueryAnalysisResult:
        """
        Main function to analyze user query and break it down into sections
        
        Args:
            user_query: The user's research query
            
        Returns:
            QueryAnalysisResult: Comprehensive analysis of the query
        """
        # Step 1: Identify relevant sections
        section_relevance = self._identify_relevant_sections(user_query)
        
        # Step 2: Generate section-specific analyses
        section_analyses = []
        for section, relevance_score in section_relevance.items():
            if relevance_score > 0.3:  # Only include sections with significant relevance
                analysis = self._analyze_section(user_query, section, relevance_score)
                section_analyses.append(analysis)
        
        # Step 3: Determine primary and secondary focuses
        primary_focus, secondary_focuses = self._determine_focus_hierarchy(section_analyses)
        
        # Step 4: Assess overall complexity
        complexity = self._assess_complexity(user_query, section_analyses)
        
        return QueryAnalysisResult(
            original_query=user_query,
            detected_sections=section_analyses,
            primary_focus=primary_focus,
            secondary_focuses=secondary_focuses,
            overall_complexity=complexity
        )

    def _identify_relevant_sections(self, query: str) -> Dict[ReportSection, float]:
        """Identify which report sections are relevant to the query"""
        
        prompt = f"""
        Analyze the following research query and determine which report sections are relevant.
        
        Query: "{query}"
        
        Report Sections:
        1. Disease Overview - Disease background, symptoms, diagnosis, treatment paradigm, unmet needs
        2. Epidemiology - Prevalence, incidence, patient populations, geographic distribution
        3. Competitive Landscape - Pipeline drugs, clinical trials, marketed products, competitors
        4. Deal Landscape - Licensing deals, partnerships, acquisitions, investments
        5. Target Product Profile - Product differentiation, clinical endpoints, dosing, administration
        6. Market Model - Market size, revenue forecasts, pricing, penetration rates
        7. Clinical Development - Trial design, endpoints, biomarkers, enrollment, budgets
        8. KOLs - Key opinion leaders, investigators, clinical experts
        
        For each section, provide a relevance score from 0.0 to 1.0 (where 1.0 is highly relevant).
        
        Respond in JSON format:
        {{
            "disease_overview": 0.0-1.0,
            "epidemiology": 0.0-1.0,
            "competitive_landscape": 0.0-1.0,
            "deal_landscape": 0.0-1.0,
            "target_product_profile": 0.0-1.0,
            "market_model": 0.0-1.0,
            "clinical_development": 0.0-1.0,
            "kols": 0.0-1.0
        }}
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        try:
            scores = json.loads(response.choices[0].message.content)
            return {ReportSection(k): v for k, v in scores.items()}
        except:
            # Fallback: basic keyword matching
            return self._fallback_section_identification(query)

    def _analyze_section(self, query: str, section: ReportSection, relevance_score: float) -> SectionAnalysis:
        """Generate detailed analysis for a specific section"""
        
        section_info = self.section_mapping[section]
        
        prompt = f"""
        As a {section_info['persona']}, analyze the following query for the {section.value.replace('_', ' ').title()} section.
        
        Original Query: "{query}"
        Section Focus: {section.value.replace('_', ' ').title()}
        Section Keywords: {', '.join(section_info['keywords'])}
        
        Generate:
        1. 3-5 specific sub-queries that would need to be answered for this section
        2. 8-12 relevant keywords for data search/API calls
        3. Rationale for why this section is relevant (2-3 sentences)
        
        Focus on the aspects of the original query that relate to this specific section.
        Make sub-queries specific and actionable for research.
        
        Respond in JSON format:
        {{
            "sub_queries": ["query1", "query2", "query3", ...],
            "keywords": ["keyword1", "keyword2", ...],
            "rationale": "explanation of relevance"
        }}
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        
        try:
            analysis = json.loads(response.choices[0].message.content)
            return SectionAnalysis(
                section=section,
                relevance_score=relevance_score,
                sub_queries=analysis["sub_queries"],
                keywords=analysis["keywords"],
                api_endpoints=section_info["api_endpoints"],
                rationale=analysis["rationale"]
            )
        except:
            # Fallback analysis
            return self._fallback_section_analysis(query, section, relevance_score)

    def _determine_focus_hierarchy(self, analyses: List[SectionAnalysis]) -> Tuple[str, List[str]]:
        """Determine primary and secondary focus areas"""
        if not analyses:
            return "Unknown", []
        
        # Sort by relevance score
        sorted_analyses = sorted(analyses, key=lambda x: x.relevance_score, reverse=True)
        
        primary = sorted_analyses[0].section.value.replace('_', ' ').title()
        secondary = [a.section.value.replace('_', ' ').title() for a in sorted_analyses[1:4]]
        
        return primary, secondary

    def _assess_complexity(self, query: str, analyses: List[SectionAnalysis]) -> str:
        """Assess the overall complexity of the query"""
        num_sections = len(analyses)
        avg_relevance = sum(a.relevance_score for a in analyses) / len(analyses) if analyses else 0
        
        if num_sections >= 6 or avg_relevance > 0.8:
            return "High - Comprehensive multi-section analysis required"
        elif num_sections >= 3 or avg_relevance > 0.6:
            return "Medium - Multi-section analysis with moderate depth"
        else:
            return "Low - Focused analysis on specific areas"

    def _fallback_section_identification(self, query: str) -> Dict[ReportSection, float]:
        """Fallback method using keyword matching"""
        scores = {}
        query_lower = query.lower()
        
        for section, info in self.section_mapping.items():
            score = 0
            for keyword in info["keywords"]:
                if keyword.lower() in query_lower:
                    score += 0.2
            scores[section] = min(score, 1.0)
        
        return scores

    def _fallback_section_analysis(self, query: str, section: ReportSection, relevance_score: float) -> SectionAnalysis:
        """Fallback section analysis"""
        section_info = self.section_mapping[section]
        
        return SectionAnalysis(
            section=section,
            relevance_score=relevance_score,
            sub_queries=[f"Analyze {section.value.replace('_', ' ')} for the query: {query}"],
            keywords=section_info["keywords"][:8],
            api_endpoints=section_info["api_endpoints"],
            rationale=f"This section is relevant based on keyword matching and query context."
        )

    def generate_research_plan(self, analysis_result: QueryAnalysisResult) -> str:
        """Generate a structured research plan based on the analysis"""
        
        plan = f"""
# Research Plan for Query Analysis

## Original Query
{analysis_result.original_query}

## Analysis Summary
- **Primary Focus**: {analysis_result.primary_focus}
- **Secondary Areas**: {', '.join(analysis_result.secondary_focuses)}
- **Complexity Level**: {analysis_result.overall_complexity}
- **Sections Required**: {len(analysis_result.detected_sections)}

## Detailed Section Breakdown

"""
        
        for i, section_analysis in enumerate(analysis_result.detected_sections, 1):
            plan += f"""
### {i}. {section_analysis.section.value.replace('_', ' ').title()}
**Relevance Score**: {section_analysis.relevance_score:.2f}
**Rationale**: {section_analysis.rationale}

**Sub-Queries**:
"""
            for j, sub_query in enumerate(section_analysis.sub_queries, 1):
                plan += f"{j}. {sub_query}\n"
            
            plan += f"""
**Keywords**: {', '.join(section_analysis.keywords)}
**API Endpoints**: {', '.join(section_analysis.api_endpoints)}

"""
        
        return plan

    def export_for_api_calls(self, analysis_result: QueryAnalysisResult) -> Dict:
        """Export structured data for API integration"""
        
        api_structure = {
            "query_id": hash(analysis_result.original_query),
            "original_query": analysis_result.original_query,
            "complexity": analysis_result.overall_complexity,
            "sections": {}
        }
        
        for analysis in analysis_result.detected_sections:
            api_structure["sections"][analysis.section.value] = {
                "relevance_score": analysis.relevance_score,
                "sub_queries": analysis.sub_queries,
                "search_keywords": analysis.keywords,
                "api_endpoints": analysis.api_endpoints,
                "rationale": analysis.rationale
            }
        
        return api_structure

# pipeline = AIAgentQueryPipeline("API Key")    
#     # Test with the provided prompts
# query = """Conduct a comprehensive analysis of the therapeutic landscape for post-myocardial infarction (MI) treatment, with a focus on agents targeting cardioprotective or remodeling-prevention mechanisms. Include:
#     • List of active clinical-stage programs (Ph1–Ph3) in post-MI or ischemia-reperfusion settings, segmented by MOA (e.g., mitochondrial protection, anti-inflammatory, anti-fibrotic, stem cell-derived, YAP activators, etc.)
#     • Trial design characteristics (e.g., time to intervention post-MI, target patient population, primary endpoints)
#     • Unmet needs in early-phase or subacute cardioprotection, especially in the context of modern PCI and dual antiplatelet therapy (DAPT)
#     • Commercial benchmarks (recent deal terms, partnerships, or exits for post-MI assets)
#     • Any examples of prior trial failures in this space and why they failed 
#     • Geographic considerations (e.g., differences in standards of care or trial feasibility across US, EU, China)
# """

        
# try:
#     result = pipeline.analyze_query(query)
#     research_plan = pipeline.generate_research_plan(result)
#     print(research_plan)
    
#     # Also show API export structure
#     api_data = pipeline.export_for_api_calls(result)
#     print(f"\nAPI Export Structure:")
#     print(json.dumps(api_data, indent=2))
    
# except Exception as e:
#     print(f"Error analyzing query {i}: {str(e)}")
