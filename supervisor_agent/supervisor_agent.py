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
    relevant_globaldata_apis: List[str]  # New field for GlobalData APIs
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
        
        # Define GlobalData API endpoints
        self.globaldata_apis = {
            "biomarker": [
                "/api/Biomarker/GetBiomarkersDetails",
                "/api/Biomarker/GetBiomarkersDailyUpdates"
            ],
            "clinical_trials": [
                "/api/ClinicalTrials/GetClinicalTrialsDetails",
                "/api/ClinicalTrials/GetClinicalTrialsLocationsandcontactDetails",
                "/api/ClinicalTrials/GetClinicalTrialsDailyUpdates"
            ],
            "company": [
                "/api/Company/GetCompanyDetails",
                "/api/Company/GetDailyDeletedCompanies"
            ],
            "deals": [
                "/api/Deals/GetDealsDetails",
                "/api/Deals/GetDealsDailyUpdates",
                "/api/Deals/GetDailyDeletedDeals"
            ],
            "drugs": [
                "/api/Drugs/GetPipelineDrugDetails",
                "/api/Drugs/GetMarketedDrugDetails",
                "/api/Drugs/GetDrugsDailyUpdates",
                "/api/Drugs/GetHistoryofEvents",
                "/api/Drugs/GetStubDrugs"
            ],
            "drug_sales": [
                "/api/DrugSales/GetDrugSalesDetails",
                "/api/DrugSales/GetDrugSalesDailyUpdates"
            ],
            "epidemiology": [
                "/api/Epidemiology/GetEpidemiologyDetails",
                ],
            "filings": [
                "/api/Filings/GetCompanyFilingListing",
                "/api/Filings/GetCompanyFilingDetails"
            ],
            "investigators": [
                "/api/Investigators/GetInvestigatorsDetails",
                "/api/Investigators/GetInvestigatorsDailyUpdates"
            ],
            "loa": [
                "/api/LOA/GetLOADetails"
            ],
            "news": [
                "/api/News/GetNewsDetails",
                "/api/News/GetNewsDailyUpdates",
                "/api/News/GetDailyDeletedNews"
            ],
            "npv": [
                "/api/NPV/GetNPVDetails"
            ],
            "patents": [
                "/api/Patents/GetPatentsListing",
                "/api/Content/GetPatentsDescriptionandClaims"
            ],
            "poli": [
                "/api/Poli/GetPoliDrugs",
                "/api/Poli/GetPoliTherapyDetails",
                "/api/Poli/GetHTAAssesmentDetails",
                "/api/Poli/GETIRPDetails",
                "/api/Poli/GetDeletedPoliDrugsDetails",
                "/api/Poli/GetDrugs",
                "/api/Poli/GetTherapyAreas",
                "/api/Poli/GetTherapyLines",
                "/api/Poli/GetTherapyTypes",
                "/api/Poli/GetDiseaseStage",
                "/api/Poli/GetForexCurrencies",
                "/api/Poli/GetCurrencyConverter"
            ],
            "rmt": [
                "/api/RMT/GetRMTDetails",
                "/api/RMT/GetRMTDailyUpdates"
            ],
            "sites": [
                "/api/Sites/GetTrialSitesDetails",
                "/api/Sites/GetTrialSiteDailyUpdates"
            ]
        }
        
        # Define section characteristics and keywords
        self.section_mapping = {
            ReportSection.DISEASE_OVERVIEW: {
                "keywords": ["disease", "symptoms", "diagnosis", "etiology", "pathology", "treatment paradigm", "unmet needs", "patient segments"],
                "api_endpoints": ["Local", "pubmed_central", "tavily"],
                "persona": "MD, PhD with specialization in relevant disease",
                "globaldata_api_categories": ["poli", "news", "drugs"]
            },
            ReportSection.EPIDEMIOLOGY: {
                "keywords": ["prevalence", "incidence", "epidemiology", "patient population", "demographics", "geography", "forecast"],
                "api_endpoints": ["tavily", "pubmed_central", "Local"],
                "persona": "PhD epidemiologist",
                "globaldata_api_categories": ["poli", "news", "drugs", "epidemiology"]
            },
            ReportSection.COMPETITIVE_LANDSCAPE: {
                "keywords": ["pipeline", "competitors", "drugs", "clinical trials", "market share", "pricing", "reimbursement", "assets"],
                "api_endpoints": ["tavily", "Local", "pubmed_central"],
                "persona": "Wall street analyst with biotech focus",
                "globaldata_api_categories": ["drugs", "clinical_trials", "company", "drug_sales", "patents"]
            },
            ReportSection.DEAL_LANDSCAPE: {
                "keywords": ["deals", "licensing", "partnerships", "acquisitions", "M&A", "collaborations", "investment", "financing"],
                "api_endpoints": ["tavily", "Local", "pubmed_central"],
                "persona": "Wall street analyst with biotech focus",
                "globaldata_api_categories": ["deals", "company", "news"]
            },
            ReportSection.TARGET_PRODUCT_PROFILE: {
                "keywords": ["target product profile", "TPP", "differentiation", "endpoints", "dosing", "route of administration", "comparator"],
                "api_endpoints": ["tavily", "Local", "pubmed_central"],
                "persona": "Chief medical officer of pharmaceutical company",
                "globaldata_api_categories": ["drugs", "clinical_trials", "biomarker"]
            },
            ReportSection.MARKET_MODEL: {
                "keywords": ["market size", "revenue forecast", "sales", "pricing", "market penetration", "addressable market"],
                "api_endpoints": ["tavily", "Local", "pubmed_central"],
                "persona": "Wall street analyst with biotech focus",
                "globaldata_api_categories": ["drug_sales", "npv", "poli", "company"]
            },
            ReportSection.CLINICAL_DEVELOPMENT: {
                "keywords": ["clinical trial design", "endpoints", "biomarkers", "enrollment", "PoS", "budget", "recruitment"],
                "api_endpoints": ["tavily", "Local", "pubmed_central"],
                "persona": "Chief medical officer with clinical trial experience",
                "globaldata_api_categories": ["clinical_trials", "sites", "investigators", "biomarker"]
            },
            ReportSection.KOLS: {
                "keywords": ["key opinion leaders", "KOLs", "investigators", "experts", "consultants", "clinical trial experience"],
                "api_endpoints": ["tavily", "Local", "pubmed_central"],
                "persona": "Business development associate",
                "globaldata_api_categories": ["investigators", "clinical_trials"]
            }
        }

    def _map_globaldata_apis_to_section(self, section: ReportSection) -> List[str]:
        """Map relevant GlobalData APIs to a specific section"""
        section_info = self.section_mapping[section]
        relevant_apis = []
        
        for category in section_info["globaldata_api_categories"]:
            if category in self.globaldata_apis:
                relevant_apis.extend(self.globaldata_apis[category])
        
        return relevant_apis

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
        print(section_relevance)
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
        relevant_globaldata_apis = self._map_globaldata_apis_to_section(section)
        
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
                relevant_globaldata_apis=relevant_globaldata_apis,
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
        relevant_globaldata_apis = self._map_globaldata_apis_to_section(section)
        
        return SectionAnalysis(
            section=section,
            relevance_score=relevance_score,
            sub_queries=[f"Analyze {section.value.replace('_', ' ')} for the query: {query}"],
            keywords=section_info["keywords"][:8],
            api_endpoints=section_info["api_endpoints"],
            relevant_globaldata_apis=relevant_globaldata_apis,
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
**External API Endpoints**: {', '.join(section_analysis.api_endpoints)}

**Relevant GlobalData APIs**:
"""
            for api in section_analysis.relevant_globaldata_apis:
                plan += f"- {api}\n"
            
            plan += "\n"
        
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
                "external_api_endpoints": analysis.api_endpoints,
                "globaldata_apis": analysis.relevant_globaldata_apis,
                "rationale": analysis.rationale
            }
        
        return api_structure

    def get_all_globaldata_apis_for_query(self, analysis_result: QueryAnalysisResult) -> Dict[str, List[str]]:
        """Get all relevant GlobalData APIs organized by section"""
        apis_by_section = {}
        
        for analysis in analysis_result.detected_sections:
            section_name = analysis.section.value.replace('_', ' ').title()
            apis_by_section[section_name] = analysis.relevant_globaldata_apis
        
        return apis_by_section


# Example usage and testing
# def main():
#     # Initialize pipeline (you would use your actual OpenAI API key)
#     pipeline = AIAgentQueryPipeline("your-openai-api-key-here")

#     # Test with the provided prompts
#     test_queries = [
#         """I am working on a project focused on proposing and validating cancer targets for an in-situ CAR-T platform. We are especially interested in cell surface targets relevant to non-small cell lung cancer (NSCLC), small cell lung cancer (SCLC), and colorectal cancer (CRC).
# AbbVie is our company of interest. Please help with the following research and analysis:
# 1. Pipeline Review: AbbVie (Oncology focus)
#     • List all AbbVie pipeline programs from the past 3–5 years in NSCLC, SCLC, and CRC.
#     • Include current assets, discontinued/terminated programs, and announced preclinical collaborations.
#     • Focus on programs involving antibody-based therapeutics (e.g., monoclonal antibodies, ADCs, bispecific antibodies).

# 2. Target Identification
#     • For each pipeline asset, identify the associated antigen/target (e.g., DLL3, CEACAM5, TROP2).
#     • Expand to include targets AbbVie may have access to via:
#     • Acquisitions (e.g., full rights as with full M&A deals),
#     • In-licensing agreements (include the licensing terms and scope if available), or
#     • Option agreements or collaborations (include any known status of exercised options or remaining rights).

# 3.  Target Rights Classification
#     • For each target, clearly indicate AbbVie’s ownership status:
#         ◦ Full rights (via acquisition or full internal development)
#         ◦ Partial/limited rights (e.g., for a specific indication, territory, or therapeutic modality)
#         ◦ Optioned/future rights (if AbbVie retains the right to pursue the target under certain conditions)
#     • Describe the limitations of each access type in practical terms, e.g.:
#         ◦ Restrictions to ADCs only
#         ◦ Limited geographic commercialization
#         ◦ Co-development obligations

# 4. In-Situ CAR-T Suitability & Prioritization
#  Prioritize identified targets for their potential use in our in-situ CAR-T platform based on:
#     • Tumor specificity and overexpression in NSCLC, SCLC, or CRC
#     • Cell surface stability/internalization behavior
#     • Prior evidence in CAR-T or ADC platforms
#     • Expression in normal tissues (i.e., toxicity concerns)
#     • Competitive landscape (how crowded or differentiated the target is)

# 5. Structured Output Format
# Please return results in a table with these columns:
#     • Target 
#     • Tumor Type(s) 
#     • AbbVie Source (Pipeline/Partner) 
#     • Partner/Company 
#     • Rights Type (Acquisition/In-License/Option) 
#     • Rights Details 
#     • Platform Type (ADC, mAb, etc.) 
#     • CAR-T Suitability Score (1-5) 
#     • Other Notes

# Highlight any underexplored or emerging targets in AbbVie’s ecosystem that might be especially attractive or differentiated for in-situ CAR-T development, particularly those not widely used in current CAR-T pipelines.
# """,
        
#         """My company is evaluating the opportunity for a high dose once monthly injectable GLP-1/GIP/Glucagon receptor triple agonist for long-term weight loss maintenance therapy for obesity. Evaluate the market opportunity and unmet need for long-term obesity maintenance therapies. Focus on segmentation across the following axes:
#     • BMI categories: Class I (30–35), Class II (35–40), Class III (≥40)
#     • Patient subgroups: with vs. without Type 2 diabetes, prior bariatric surgery, responders vs. non-responders to induction therapy
#     • Current standard of care and limitations (e.g., semaglutide, tirzepatide, lifestyle adherence, drop-off rates after weight loss plateau)
#     • Pipeline therapies explicitly being developed or positioned for maintenance (vs. induction), including mechanisms (e.g., amylin analogs, GLP-1/GIP modulators, FGF21 analogs, etc.)
#     • Real-world adherence data and discontinuation drivers post-weight loss
#     • Expected commercial segmentation: e.g., how payers and physicians differentiate between induction and maintenance use (pricing, access hurdles)
#     • Sales forecasts for therapies with long-term administration profiles (≥12 months)
#     • Competitive positioning of novel candidates offering less frequent dosing, improved tolerability, or weight regain prevention efficacy
# """,
        
#         """Conduct a comprehensive analysis of the therapeutic landscape for post-myocardial infarction (MI) treatment, with a focus on agents targeting cardioprotective or remodeling-prevention mechanisms. Include:
#     • List of active clinical-stage programs (Ph1–Ph3) in post-MI or ischemia-reperfusion settings, segmented by MOA (e.g., mitochondrial protection, anti-inflammatory, anti-fibrotic, stem cell-derived, YAP activators, etc.)
#     • Trial design characteristics (e.g., time to intervention post-MI, target patient population, primary endpoints)
#     • Unmet needs in early-phase or subacute cardioprotection, especially in the context of modern PCI and dual antiplatelet therapy (DAPT)
#     • Commercial benchmarks (recent deal terms, partnerships, or exits for post-MI assets)
#     • Any examples of prior trial failures in this space and why they failed 
#     • Geographic considerations (e.g., differences in standards of care or trial feasibility across US, EU, China)
# """
#     ]
    
#     for i, query in enumerate(test_queries, 1):
#         print(f"\n{'='*60}")
#         print(f"ANALYSIS {i}")
#         print(f"{'='*60}")
        
#         try:
#             result = pipeline.analyze_query(query)
#             research_plan = pipeline.generate_research_plan(result)
#             print(research_plan)
            
#             # Show API mapping
#             api_mapping = pipeline.get_all_globaldata_apis_for_query(result)
#             print(f"\nGlobalData API Mapping by Section:")
#             for section, apis in api_mapping.items():
#                 print(f"\n{section}:")
#                 for api in apis:
#                     print(f"  - {api}")
            
#             # Also show API export structure
#             api_data = pipeline.export_for_api_calls(result)
#             print(f"\nAPI Export Structure:")
#             print(json.dumps(api_data, indent=2))
            
#         except Exception as e:
#             print(f"Error analyzing query {i}: {str(e)}")

# if __name__ == "__main__":
#     main()