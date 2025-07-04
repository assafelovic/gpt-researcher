# import os
# import openai
# from typing import Dict, List, Optional, Tuple
# import json
# import re
# from dataclasses import dataclass
# from enum import Enum
# from dotenv import load_dotenv
# load_dotenv()

# api_key = os.getenv("OPENAI_API_KEY")
# class ReportSection(Enum):
#     DISEASE_OVERVIEW = "disease_overview"
#     EPIDEMIOLOGY = "epidemiology"
#     COMPETITIVE_LANDSCAPE = "competitive_landscape"
#     DEAL_LANDSCAPE = "deal_landscape"
#     TARGET_PRODUCT_PROFILE = "target_product_profile"
#     MARKET_MODEL = "market_model"
#     CLINICAL_DEVELOPMENT = "clinical_development"
#     KOLS = "kols"

# @dataclass
# class SectionAnalysis:
#     section: ReportSection
#     relevance_score: float
#     sub_queries: List[str]
#     keywords: List[str]
#     api_endpoints: List[str]
#     relevant_globaldata_apis: List[str]  # New field for GlobalData APIs
#     rationale: str

# @dataclass
# class QueryAnalysisResult:
#     original_query: str
#     detected_sections: List[SectionAnalysis]
#     primary_focus: str
#     secondary_focuses: List[str]
#     overall_complexity: str

# class AIAgentQueryPipeline:
#     def __init__(self, openai_api_key: str, model: str = "gpt-4"):
#         """
#         Initialize the AI Agent Query Pipeline
        
#         Args:
#             openai_api_key: OpenAI API key
#             model: OpenAI model to use (default: gpt-4)
#         """
#         self.client = openai.OpenAI(api_key=openai_api_key)
#         self.model = model
        
#         # Define GlobalData API endpoints
#         self.globaldata_apis = {
#             "biomarker": [
#                 "/api/Biomarker/GetBiomarkersDetails",
#                 "/api/Biomarker/GetBiomarkersDailyUpdates"
#             ],
#             "clinical_trials": [
#                 "/api/ClinicalTrials/GetClinicalTrialsDetails",
#                 "/api/ClinicalTrials/GetClinicalTrialsLocationsandcontactDetails",
#                 "/api/ClinicalTrials/GetClinicalTrialsDailyUpdates"
#             ],
#             "company": [
#                 "/api/Company/GetCompanyDetails",
#                 "/api/Company/GetDailyDeletedCompanies"
#             ],
#             "deals": [
#                 "/api/Deals/GetDealsDetails",
#                 "/api/Deals/GetDealsDailyUpdates",
#                 "/api/Deals/GetDailyDeletedDeals"
#             ],
#             "drugs": [
#                 "/api/Drugs/GetPipelineDrugDetails",
#                 "/api/Drugs/GetMarketedDrugDetails",
#                 "/api/Drugs/GetDrugsDailyUpdates",
#                 "/api/Drugs/GetHistoryofEvents",
#                 "/api/Drugs/GetStubDrugs"
#             ],
#             "drug_sales": [
#                 "/api/DrugSales/GetDrugSalesDetails",
#                 "/api/DrugSales/GetDrugSalesDailyUpdates"
#             ],
#             "epidemiology": [
#                 "/api/Epidemiology/GetEpidemiologyDetails",
#                 ],
#             "filings": [
#                 "/api/Filings/GetCompanyFilingListing",
#                 "/api/Filings/GetCompanyFilingDetails"
#             ],
#             "investigators": [
#                 "/api/Investigators/GetInvestigatorsDetails",
#                 "/api/Investigators/GetInvestigatorsDailyUpdates"
#             ],
#             "loa": [
#                 "/api/LOA/GetLOADetails"
#             ],
#             "news": [
#                 "/api/News/GetNewsDetails",
#                 "/api/News/GetNewsDailyUpdates",
#                 "/api/News/GetDailyDeletedNews"
#             ],
#             "npv": [
#                 "/api/NPV/GetNPVDetails"
#             ],
#             "patents": [
#                 "/api/Patents/GetPatentsListing",
#                 "/api/Content/GetPatentsDescriptionandClaims"
#             ],
#             "poli": [
#                 "/api/Poli/GetPoliDrugs",
#                 "/api/Poli/GetPoliTherapyDetails",
#                 "/api/Poli/GetHTAAssesmentDetails",
#                 "/api/Poli/GETIRPDetails",
#                 "/api/Poli/GetDeletedPoliDrugsDetails",
#                 "/api/Poli/GetDrugs",
#                 "/api/Poli/GetTherapyAreas",
#                 "/api/Poli/GetTherapyLines",
#                 "/api/Poli/GetTherapyTypes",
#                 "/api/Poli/GetDiseaseStage",
#                 "/api/Poli/GetForexCurrencies",
#                 "/api/Poli/GetCurrencyConverter"
#             ],
#             "rmt": [
#                 "/api/RMT/GetRMTDetails",
#                 "/api/RMT/GetRMTDailyUpdates"
#             ],
#             "sites": [
#                 "/api/Sites/GetTrialSitesDetails",
#                 "/api/Sites/GetTrialSiteDailyUpdates"
#             ]
#         }
        
#         # Define section characteristics and keywords
#         self.section_mapping = {
#             ReportSection.DISEASE_OVERVIEW: {
#                 "keywords": ["disease", "symptoms", "diagnosis", "etiology", "pathology", "treatment paradigm", "unmet needs", "patient segments"],
#                 "api_endpoints": ["Local", "pubmed_central", "tavily"],
#                 "persona": "MD, PhD with specialization in relevant disease",
#                 "globaldata_api_categories": ["poli", "news", "drugs"]
#             },
#             ReportSection.EPIDEMIOLOGY: {
#                 "keywords": ["prevalence", "incidence", "epidemiology", "patient population", "demographics", "geography", "forecast"],
#                 "api_endpoints": ["tavily", "pubmed_central", "Local"],
#                 "persona": "PhD epidemiologist",
#                 "globaldata_api_categories": ["poli", "news", "drugs", "epidemiology"]
#             },
#             ReportSection.COMPETITIVE_LANDSCAPE: {
#                 "keywords": ["pipeline", "competitors", "drugs", "clinical trials", "market share", "pricing", "reimbursement", "assets"],
#                 "api_endpoints": ["tavily", "Local", "pubmed_central"],
#                 "persona": "Wall street analyst with biotech focus",
#                 "globaldata_api_categories": ["drugs", "clinical_trials", "company", "drug_sales", "patents"]
#             },
#             ReportSection.DEAL_LANDSCAPE: {
#                 "keywords": ["deals", "licensing", "partnerships", "acquisitions", "M&A", "collaborations", "investment", "financing"],
#                 "api_endpoints": ["tavily", "Local", "pubmed_central"],
#                 "persona": "Wall street analyst with biotech focus",
#                 "globaldata_api_categories": ["deals", "company", "news"]
#             },
#             ReportSection.TARGET_PRODUCT_PROFILE: {
#                 "keywords": ["target product profile", "TPP", "differentiation", "endpoints", "dosing", "route of administration", "comparator"],
#                 "api_endpoints": ["tavily", "Local", "pubmed_central"],
#                 "persona": "Chief medical officer of pharmaceutical company",
#                 "globaldata_api_categories": ["drugs", "clinical_trials", "biomarker"]
#             },
#             ReportSection.MARKET_MODEL: {
#                 "keywords": ["market size", "revenue forecast", "sales", "pricing", "market penetration", "addressable market"],
#                 "api_endpoints": ["tavily", "Local", "pubmed_central"],
#                 "persona": "Wall street analyst with biotech focus",
#                 "globaldata_api_categories": ["drug_sales", "npv", "poli", "company"]
#             },
#             ReportSection.CLINICAL_DEVELOPMENT: {
#                 "keywords": ["clinical trial design", "endpoints", "biomarkers", "enrollment", "PoS", "budget", "recruitment"],
#                 "api_endpoints": ["tavily", "Local", "pubmed_central"],
#                 "persona": "Chief medical officer with clinical trial experience",
#                 "globaldata_api_categories": ["clinical_trials", "sites", "investigators", "biomarker"]
#             },
#             ReportSection.KOLS: {
#                 "keywords": ["key opinion leaders", "KOLs", "investigators", "experts", "consultants", "clinical trial experience"],
#                 "api_endpoints": ["tavily", "Local", "pubmed_central"],
#                 "persona": "Business development associate",
#                 "globaldata_api_categories": ["investigators", "clinical_trials"]
#             }
#         }


#     def _get_targeted_globaldata_apis(self, query: str, section: ReportSection, keywords: List[str]) -> List[str]:
#         """Get targeted GlobalData APIs based on specific query needs rather than all APIs in a category"""
        
#         # Define API selection logic based on query analysis
#         api_selection_rules = {
#             ReportSection.DISEASE_OVERVIEW: {
#                 "primary_apis": ["/api/Poli/GetTherapyAreas", "/api/News/GetNewsDetails"],
#                 "conditional_apis": {
#                     "drug": ["/api/Drugs/GetPipelineDrugDetails"],
#                     "therapy": ["/api/Poli/GetPoliTherapyDetails"],
#                     "disease": ["/api/Poli/GetDiseaseStage"]
#                 }
#             },
#             ReportSection.EPIDEMIOLOGY: {
#                 "primary_apis": ["/api/Poli/GetPoliTherapyDetails", "/api/Epidemiology/GetEpidemiologyDetails"],
#                 "conditional_apis": {
#                     "population": ["/api/News/GetNewsDetails"],
#                     "geographic": ["/api/Poli/GetForexCurrencies"]
#                 }
#             },
#             ReportSection.COMPETITIVE_LANDSCAPE: {
#                 "primary_apis": ["/api/Drugs/GetPipelineDrugDetails", "/api/ClinicalTrials/GetClinicalTrialsDetails"],
#                 "conditional_apis": {
#                     "company": ["/api/Company/GetCompanyDetails"],
#                     "marketed": ["/api/Drugs/GetMarketedDrugDetails"],
#                     "sales": ["/api/DrugSales/GetDrugSalesDetails"],
#                     "patent": ["/api/Patents/GetPatentsListing"]
#                 }
#             },
#             ReportSection.DEAL_LANDSCAPE: {
#                 "primary_apis": ["/api/Deals/GetDealsDetails"],
#                 "conditional_apis": {
#                     "company": ["/api/Company/GetCompanyDetails"],
#                     "news": ["/api/News/GetNewsDetails"],
#                     "filing": ["/api/Filings/GetCompanyFilingDetails"]
#                 }
#             },
#             ReportSection.TARGET_PRODUCT_PROFILE: {
#                 "primary_apis": ["/api/Drugs/GetPipelineDrugDetails", "/api/Biomarker/GetBiomarkersDetails"],
#                 "conditional_apis": {
#                     "clinical": ["/api/ClinicalTrials/GetClinicalTrialsDetails"],
#                     "history": ["/api/Drugs/GetHistoryofEvents"]
#                 }
#             },
#             ReportSection.MARKET_MODEL: {
#                 "primary_apis": ["/api/DrugSales/GetDrugSalesDetails", "/api/NPV/GetNPVDetails"],
#                 "conditional_apis": {
#                     "therapy": ["/api/Poli/GetPoliTherapyDetails"],
#                     "currency": ["/api/Poli/GetCurrencyConverter"],
#                     "company": ["/api/Company/GetCompanyDetails"]
#                 }
#             },
#             ReportSection.CLINICAL_DEVELOPMENT: {
#                 "primary_apis": ["/api/ClinicalTrials/GetClinicalTrialsDetails", "/api/Sites/GetTrialSitesDetails"],
#                 "conditional_apis": {
#                     "investigator": ["/api/Investigators/GetInvestigatorsDetails"],
#                     "biomarker": ["/api/Biomarker/GetBiomarkersDetails"],
#                     "contact": ["/api/ClinicalTrials/GetClinicalTrialsLocationsandcontactDetails"]
#                 }
#             },
#             ReportSection.KOLS: {
#                 "primary_apis": ["/api/Investigators/GetInvestigatorsDetails"],
#                 "conditional_apis": {
#                     "trial": ["/api/ClinicalTrials/GetClinicalTrialsDetails"]
#                 }
#             }
#         }
        
#         if section not in api_selection_rules:
#             return []
        
#         rules = api_selection_rules[section]
#         selected_apis = rules["primary_apis"].copy()
        
#         # Add conditional APIs based on keywords and query content
#         query_lower = query.lower()
#         keywords_lower = [k.lower() for k in keywords]
        
#         for condition, apis in rules["conditional_apis"].items():
#             # Check if condition matches query or keywords
#             if (condition in query_lower or 
#                 any(condition in keyword for keyword in keywords_lower) or
#                 any(keyword in condition for keyword in keywords_lower)):
#                 selected_apis.extend(apis)
        
#         return selected_apis

#     def analyze_query(self, user_query: str) -> QueryAnalysisResult:
#         """
#         Main function to analyze user query and break it down into sections
        
#         Args:
#             user_query: The user's research query
            
#         Returns:
#             QueryAnalysisResult: Comprehensive analysis of the query
#         """
#         # Step 1: Identify relevant sections
#         section_relevance = self._identify_relevant_sections(user_query)

#         # Step 2: Generate section-specific analyses
#         section_analyses = []
#         for section, relevance_score in section_relevance.items():
#             if relevance_score > 0.1:  # Only include sections with significant relevance
#                 analysis = self._analyze_section(user_query, section, relevance_score)
#                 print("-"*50)
#                 print(analysis)
#                 print("-"*50)
#                 section_analyses.append(analysis)
        
#         # Step 3: Determine primary and secondary focuses
#         primary_focus, secondary_focuses = self._determine_focus_hierarchy(section_analyses)
#         # Step 4: Assess overall complexity
#         complexity = self._assess_complexity(user_query, section_analyses)
        
#         return QueryAnalysisResult(
#             original_query=user_query,
#             detected_sections=section_analyses,
#             primary_focus=primary_focus,
#             secondary_focuses=secondary_focuses,
#             overall_complexity=complexity
#         )

#     def _identify_relevant_sections(self, query: str) -> Dict[ReportSection, float]:
#         """Identify which report sections are relevant to the query"""
        
#         prompt = f"""
#         Analyze the following research query and determine which report sections are relevant.
        
#         Query: "{query}"
        
#         Report Sections:
#         1. Disease Overview - Disease background, symptoms, diagnosis, treatment paradigm, unmet needs
#         2. Epidemiology - Prevalence, incidence, patient populations, geographic distribution
#         3. Competitive Landscape - Pipeline drugs, clinical trials, marketed products, competitors
#         4. Deal Landscape - Licensing deals, partnerships, acquisitions, investments
#         5. Target Product Profile - Product differentiation, clinical endpoints, dosing, administration
#         6. Market Model - Market size, revenue forecasts, pricing, penetration rates
#         7. Clinical Development - Trial design, endpoints, biomarkers, enrollment, budgets
#         8. KOLs - Key opinion leaders, investigators, clinical experts
        
#         For each section, provide a relevance score from 0.0 to 1.0 (where 1.0 is highly relevant).
        
#         Respond in JSON format:
#         {{
#             "disease_overview": 0.0-1.0,
#             "epidemiology": 0.0-1.0,
#             "competitive_landscape": 0.0-1.0,
#             "deal_landscape": 0.0-1.0,
#             "target_product_profile": 0.0-1.0,
#             "market_model": 0.0-1.0,
#             "clinical_development": 0.0-1.0,
#             "kols": 0.0-1.0
#         }}
#         """
        
#         response = self.client.chat.completions.create(
#             model=self.model,
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.1
#         )
        
#         try:
#             scores = json.loads(response.choices[0].message.content)
#             return {ReportSection(k): v for k, v in scores.items()}
#         except:
#             # Fallback: basic keyword matching
#             return self._fallback_section_identification(query)

#     def _analyze_section(self, query: str, section: ReportSection, relevance_score: float) -> SectionAnalysis:
#         """Generate detailed analysis for a specific section"""
        
#         section_info = self.section_mapping[section]
        
#         prompt = f"""
#         As a {section_info['persona']}, analyze the following query for the {section.value.replace('_', ' ').title()} section.
        
#         Original Query: "{query}"
#         Section Focus: {section.value.replace('_', ' ').title()}
#         Section Keywords: {', '.join(section_info['keywords'])}
        
#         Generate:
#         1. ONE primary sub-query that captures the main research question for this section
#         2. ONE comprehensive sub-query that covers all remaining aspects and details needed for this section
#         3. Maximum of 3-5 relevant keywords for Global data search/API calls
#            Out of these 5 keywords 1 to 2 keywords should be pointing to relevant desease like "non-small cell lung cancer", "small cell lung cancer", "cancer",

#         4. Rationale for why this section is relevant (2-3 sentences)
        
#         Focus on the aspects of the original query that relate to this specific section.
#         Make the primary sub-query direct and actionable, and the comprehensive sub-query should cover all additional details, nuances, and supporting information needed.
        
#         Respond in JSON format:
#         {{
#             "primary_query": "main research question",
#             "comprehensive_query": "detailed query covering all remaining aspects",
#             "keywords": ["keyword1", "keyword2", ...],
#             "rationale": "explanation of relevance"
#         }}
#         """
        
#         response = self.client.chat.completions.create(
#             model=self.model,
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.2
#         )
#         try:
#             analysis = json.loads(response.choices[0].message.content)
#             sub_queries = [analysis["primary_query"], analysis["comprehensive_query"]]
#             # Get targeted APIs for this specific section and query
#             targeted_apis = self._get_targeted_globaldata_apis(query, section, analysis["keywords"])
            
#             return SectionAnalysis(
#                 section=section,
#                 relevance_score=relevance_score,
#                 sub_queries=sub_queries,
#                 keywords=analysis["keywords"],
#                 api_endpoints=section_info["api_endpoints"],
#                 relevant_globaldata_apis=targeted_apis,
#                 rationale=analysis["rationale"]
#             )
#         except:
#             # Fallback analysis
#             return self._fallback_section_analysis(query, section, relevance_score)

#     def _determine_focus_hierarchy(self, analyses: List[SectionAnalysis]) -> Tuple[str, List[str]]:
#         """Determine primary and secondary focus areas"""
#         if not analyses:
#             return "Unknown", []
        
#         # Sort by relevance score
#         sorted_analyses = sorted(analyses, key=lambda x: x.relevance_score, reverse=True)
        
#         primary = sorted_analyses[0].section.value.replace('_', ' ').title()
#         secondary = [a.section.value.replace('_', ' ').title() for a in sorted_analyses[1:4]]
        
#         return primary, secondary

#     def _assess_complexity(self, query: str, analyses: List[SectionAnalysis]) -> str:
#         """Assess the overall complexity of the query"""
#         num_sections = len(analyses)
#         avg_relevance = sum(a.relevance_score for a in analyses) / len(analyses) if analyses else 0
        
#         if num_sections >= 6 or avg_relevance > 0.8:
#             return "High - Comprehensive multi-section analysis required"
#         elif num_sections >= 3 or avg_relevance > 0.6:
#             return "Medium - Multi-section analysis with moderate depth"
#         else:
#             return "Low - Focused analysis on specific areas"

#     def _fallback_section_identification(self, query: str) -> Dict[ReportSection, float]:
#         """Fallback method using keyword matching"""
#         scores = {}
#         query_lower = query.lower()
        
#         for section, info in self.section_mapping.items():
#             score = 0
#             for keyword in info["keywords"]:
#                 if keyword.lower() in query_lower:
#                     score += 0.2
#             scores[section] = min(score, 1.0)
        
#         return scores

#     def _fallback_section_analysis(self, query: str, section: ReportSection, relevance_score: float) -> SectionAnalysis:
#         """Fallback section analysis"""
#         section_info = self.section_mapping[section]
#         targeted_apis = self._get_targeted_globaldata_apis(query, section, section_info["keywords"][:8])
        
#         primary_query = f"What are the key {section.value.replace('_', ' ')} aspects for: {query[:100]}..."
#         comprehensive_query = f"Provide comprehensive analysis of all {section.value.replace('_', ' ')} factors, including detailed information, supporting data, and contextual insights related to the query."
        
#         return SectionAnalysis(
#             section=section,
#             relevance_score=relevance_score,
#             sub_queries=[primary_query, comprehensive_query],
#             keywords=section_info["keywords"][:8],
#             api_endpoints=section_info["api_endpoints"],
#             relevant_globaldata_apis=targeted_apis,
#             rationale=f"This section is relevant based on keyword matching and query context."
#         )

#     def generate_research_plan(self, analysis_result: QueryAnalysisResult) -> str:
#         """Generate a structured research plan based on the analysis"""
        
#         plan = """## Detailed Section Breakdown"""
        
#         for i, section_analysis in enumerate(analysis_result.detected_sections, 1):
#             plan += f"""
# ### {i}. {section_analysis.section.value.replace('_', ' ').title()}
# **Relevance Score**: {section_analysis.relevance_score:.2f}
# **Rationale**: {section_analysis.rationale}

# **Sub-Queries**:
# 1. **Primary Query**: {section_analysis.sub_queries[0]}
# 2. **Comprehensive Query**: {section_analysis.sub_queries[1]}"""
            
#             plan += f"""
# **Keywords**: {', '.join(section_analysis.keywords)}
# **External Sources**: {', '.join(section_analysis.api_endpoints)}
# *Relevant GlobalData APIs**:
# """
#             for api in section_analysis.relevant_globaldata_apis:
#                 plan += f"- {api}\n"
            
#             plan += "\n"
        
#         return plan

#     def export_for_api_calls(self, analysis_result: QueryAnalysisResult) -> Dict:
#         """Export structured data for API integration"""
        
#         api_structure = {
#             "query_id": hash(analysis_result.original_query),
#             "original_query": analysis_result.original_query,
#             "complexity": analysis_result.overall_complexity,
#             "sections": {}
#         }
        
#         for analysis in analysis_result.detected_sections:
#             api_structure["sections"][analysis.section.value] = {
#                 "relevance_score": analysis.relevance_score,
#                 "sub_queries": analysis.sub_queries,
#                 "search_keywords": analysis.keywords,
#                 "external_api_endpoints": analysis.api_endpoints,
#                 "globaldata_apis": analysis.relevant_globaldata_apis,
#                 "rationale": analysis.rationale
#             }
        
#         return api_structure


# Example usage and testing
# def main():
#     # Initialize pipeline (you would use your actual OpenAI API key)
#     pipeline = AIAgentQueryPipeline(api_key)
    
#     # Test with the provided prompts
#     test_queries = [
        # """I am working on a project focused on proposing and validating cancer targets for an in-situ CAR-T platform. We are especially interested in cell surface targets relevant to non-small cell lung cancer (NSCLC), small cell lung cancer (SCLC), and colorectal cancer (CRC).
        #     AbbVie is our company of interest. Please help with the following research and analysis:
        #     1. Pipeline Review: AbbVie (Oncology focus)
        #         • List all AbbVie pipeline programs from the past 3–5 years in NSCLC, SCLC, and CRC.
        #         • Include current assets, discontinued/terminated programs, and announced preclinical collaborations.
        #         • Focus on programs involving antibody-based therapeutics (e.g., monoclonal antibodies, ADCs, bispecific antibodies).

        #     2. Target Identification
        #         • For each pipeline asset, identify the associated antigen/target (e.g., DLL3, CEACAM5, TROP2).
        #         • Expand to include targets AbbVie may have access to via:
        #         • Acquisitions (e.g., full rights as with full M&A deals),
        #         • In-licensing agreements (include the licensing terms and scope if available), or
        #         • Option agreements or collaborations (include any known status of exercised options or remaining rights).

        #     3.  Target Rights Classification
        #         • For each target, clearly indicate AbbVie’s ownership status:
        #             ◦ Full rights (via acquisition or full internal development)
        #             ◦ Partial/limited rights (e.g., for a specific indication, territory, or therapeutic modality)
        #             ◦ Optioned/future rights (if AbbVie retains the right to pursue the target under certain conditions)
        #         • Describe the limitations of each access type in practical terms, e.g.:
        #             ◦ Restrictions to ADCs only
        #             ◦ Limited geographic commercialization
        #             ◦ Co-development obligations

        #     4. In-Situ CAR-T Suitability & Prioritization
        #     Prioritize identified targets for their potential use in our in-situ CAR-T platform based on:
        #         • Tumor specificity and overexpression in NSCLC, SCLC, or CRC
        #         • Cell surface stability/internalization behavior
        #         • Prior evidence in CAR-T or ADC platforms
        #         • Expression in normal tissues (i.e., toxicity concerns)
        #         • Competitive landscape (how crowded or differentiated the target is)

        #     5. Structured Output Format
        #     Please return results in a table with these columns:
        #         • Target 
        #         • Tumor Type(s) 
        #         • AbbVie Source (Pipeline/Partner) 
        #         • Partner/Company 
        #         • Rights Type (Acquisition/In-License/Option) 
        #         • Rights Details 
        #         • Platform Type (ADC, mAb, etc.) 
        #         • CAR-T Suitability Score (1-5) 
        #         • Other Notes

        #     Highlight any underexplored or emerging targets in AbbVie’s ecosystem that might be especially attractive or differentiated for in-situ CAR-T development, particularly those not widely used in current CAR-T pipelines.
#             """,
                    
#                     """My company is evaluating the opportunity for a high dose once monthly injectable GLP-1/GIP/Glucagon receptor triple agonist for long-term weight loss maintenance therapy for obesity. Evaluate the market opportunity and unmet need for long-term obesity maintenance therapies. Focus on segmentation across the following axes:
#                 • BMI categories: Class I (30–35), Class II (35–40), Class III (≥40)
#                 • Patient subgroups: with vs. without Type 2 diabetes, prior bariatric surgery, responders vs. non-responders to induction therapy
#                 • Current standard of care and limitations (e.g., semaglutide, tirzepatide, lifestyle adherence, drop-off rates after weight loss plateau)
#                 • Pipeline therapies explicitly being developed or positioned for maintenance (vs. induction), including mechanisms (e.g., amylin analogs, GLP-1/GIP modulators, FGF21 analogs, etc.)
#                 • Real-world adherence data and discontinuation drivers post-weight loss
#                 • Expected commercial segmentation: e.g., how payers and physicians differentiate between induction and maintenance use (pricing, access hurdles)
#                 • Sales forecasts for therapies with long-term administration profiles (≥12 months)
#                 • Competitive positioning of novel candidates offering less frequent dosing, improved tolerability, or weight regain prevention efficacy
#             """,
                    
            #         """Conduct a comprehensive analysis of the therapeutic landscape for post-myocardial infarction (MI) treatment, with a focus on agents targeting cardioprotective or remodeling-prevention mechanisms. Include:
            #     • List of active clinical-stage programs (Ph1–Ph3) in post-MI or ischemia-reperfusion settings, segmented by MOA (e.g., mitochondrial protection, anti-inflammatory, anti-fibrotic, stem cell-derived, YAP activators, etc.)
            #     • Trial design characteristics (e.g., time to intervention post-MI, target patient population, primary endpoints)
            #     • Unmet needs in early-phase or subacute cardioprotection, especially in the context of modern PCI and dual antiplatelet therapy (DAPT)
            #     • Commercial benchmarks (recent deal terms, partnerships, or exits for post-MI assets)
            #     • Any examples of prior trial failures in this space and why they failed 
            #     • Geographic considerations (e.g., differences in standards of care or trial feasibility across US, EU, China)
            # """
#                 ]
    
#     for i, query in enumerate(test_queries, 1):
#         print(f"\n{'='*60}")
#         print(f"ANALYSIS {i}")
#         print(f"{'='*60}")
        
#         try:
#             result = pipeline.analyze_query(query)
#             # research_plan = pipeline.generate_research_plan(result)
#             # print(research_plan)
            
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


# import os
# import openai
# from typing import Dict, List, Optional, Tuple
# import json
# import re
# from dataclasses import dataclass
# from enum import Enum
# from dotenv import load_dotenv
# load_dotenv()

# api_key = os.getenv("OPENAI_API_KEY")
# class ReportSection(Enum):
#     DISEASE_OVERVIEW = "disease_overview"
#     EPIDEMIOLOGY = "epidemiology"
#     COMPETITIVE_LANDSCAPE = "competitive_landscape"
#     DEAL_LANDSCAPE = "deal_landscape"
#     TARGET_PRODUCT_PROFILE = "target_product_profile"
#     MARKET_MODEL = "market_model"
#     CLINICAL_DEVELOPMENT = "clinical_development"
#     KOLS = "kols"

# @dataclass
# class SectionAnalysis:
#     section: ReportSection
#     relevance_score: float
#     sub_queries: List[str]
#     keywords: List[str]
#     api_endpoints: List[str]
#     relevant_globaldata_apis: List[str]  # New field for GlobalData APIs
#     rationale: str

# @dataclass
# class QueryAnalysisResult:
#     original_query: str
#     detected_sections: List[SectionAnalysis]
#     primary_focus: str
#     secondary_focuses: List[str]
#     overall_complexity: str

# class AIAgentQueryPipeline:
#     def __init__(self, openai_api_key: str, model: str = "gpt-4"):
#         """
#         Initialize the AI Agent Query Pipeline
        
#         Args:
#             openai_api_key: OpenAI API key
#             model: OpenAI model to use (default: gpt-4)
#         """
#         self.client = openai.OpenAI(api_key=openai_api_key)
#         self.model = model
        
#         # Define GlobalData API endpoints with detailed descriptions
#         self.globaldata_apis = {
#             "biomarker": {
#                 "/api/Biomarker/GetBiomarkersDetails": "Provides biomarkers data based on from date and to date. Use for biomarker research, diagnostic markers, and therapeutic targets.",
#                 "/api/Biomarker/GetBiomarkersDailyUpdates": "Provides daily updates for biomarkers data based on from date and to date. Use for recent biomarker developments."
#             },
#             "clinical_trials": {
#                 "/api/ClinicalTrials/GetClinicalTrialsDetails": "Provides clinical trial data based on keyword search, Clinical ID, from date and to date. Essential for pipeline analysis, competitive landscape, and development timelines.",
#                 "/api/ClinicalTrials/GetClinicalTrialsLocationsandcontactDetails": "Provides clinical trial locations and contact details based on keyword search, Clinical ID, from date and to date. Use for site selection and operational planning.",
#                 "/api/ClinicalTrials/GetClinicalTrialsDailyUpdates": "Provides daily updates for clinical trials data based on from date and to date. Use for recent trial developments and status changes."
#             },
#             "company": {
#                 "/api/Company/GetCompanyDetails": "Provides company details data based on from date and to date. Essential for competitive landscape, company profiling, and partnership analysis.",
#                 "/api/Company/GetDailyDeletedCompanies": "Provides daily deleted companies data based on from date and to date. Use for database maintenance and recent company changes."
#             },
#             "deals": {
#                 "/api/Deals/GetDealsDetails": "Provides deal data based on keyword search or Deal ID. Critical for deal landscape analysis, partnership trends, and market activity.",
#                 "/api/Deals/GetDealsDailyUpdates": "Provides daily updates for deals data based on from date and to date. Use for recent deal activity and market movements.",
#                 "/api/Deals/GetDailyDeletedDeals": "Provides daily deleted deals data based on from date and to date. Use for database maintenance."
#             },
#             "drugs": {
#                 "/api/Drugs/GetPipelineDrugDetails": "Provides pipeline drug data based on keyword search or Drug ID. Essential for competitive landscape and pipeline analysis.",
#                 "/api/Drugs/GetMarketedDrugDetails": "Provides marketed drug data based on keyword search or Drug ID. Use for market analysis and competitive benchmarking.",
#                 "/api/Drugs/GetDrugsDailyUpdates": "Provides daily updates for drugs data based on from date and to date. Use for recent drug developments.",
#                 "/api/Drugs/GetHistoryofEvents": "Provides drug history events based on DrugID. Use for timeline analysis and development milestones.",
#                 "/api/Drugs/GetStubDrugs": "Provides stub drugs data based on from date and to date. Use for incomplete drug records."
#             },
#             "drug_sales": {
#                 "/api/DrugSales/GetDrugSalesDetails": "Provides drug sales data based on keyword search or DrugID. Essential for market model, revenue analysis, and commercial performance.",
#                 "/api/DrugSales/GetDrugSalesDailyUpdates": "Provides daily updates for drug sales data based on from date and to date. Use for recent sales performance."
#             },
#             "epidemiology": {
#                 "/api/Epidemiology/GetEpidemiologyDetails": "Provides epidemiology data based on keyword search or IndicationID. Essential for patient population analysis, disease prevalence, and market sizing."
#             },
#             "filings": {
#                 "/api/Filings/GetCompanyFilingListing": "Get company filing records based on published date. Use for regulatory analysis and company financial information.",
#                 "/api/Filings/GetCompanyFilingDetails": "Get company filing records based on Company ID. Use for detailed company regulatory and financial analysis."
#             },
#             "investigators": {
#                 "/api/Investigators/GetInvestigatorsDetails": "Get investigator records based on published date. Essential for KOL identification and clinical trial planning.",
#                 "/api/Investigators/GetInvestigatorsDailyUpdates": "Provides daily updates for investigators data based on from date and to date. Use for recent investigator activities."
#             },
#             "loa": {
#                 "/api/LOA/GetLOADetails": "Provides LOA (Letter of Authorization) details based on DrugName and DrugID. Use for regulatory pathway analysis."
#             },
#             "news": {
#                 "/api/News/GetNewsDetails": "Provides news data based on keyword search or NewsArticle ID. Use for market intelligence, recent developments, and industry trends.",
#                 "/api/News/GetNewsDailyUpdates": "Provides daily updates for news data based on from date and to date. Use for recent news and market developments.",
#                 "/api/News/GetDailyDeletedNews": "Provides daily deleted news data based on from date and to date. Use for database maintenance."
#             },
#             "npv": {
#                 "/api/NPV/GetNPVDetails": "Provides NPV (Net Present Value) data based on DrugName search or DrugID. Essential for market model and valuation analysis."
#             },
#             "patents": {
#                 "/api/Patents/GetPatentsListing": "Get patent records based on PublishedDate. Use for intellectual property analysis and competitive intelligence.",
#                 "/api/Content/GetPatentsDescriptionandClaims": "Get patent descriptions and claims based on ID. Use for detailed patent analysis and IP landscape."
#             },
#             "poli": {
#                 "/api/Poli/GetPoliDrugs": "Get PoliDrugs records based on PoliID. Use for policy and regulatory drug information.",
#                 "/api/Poli/GetPoliTherapyDetails": "Get PoliTherapies records based on TherapyViewID. Essential for therapy area analysis and treatment landscape.",
#                 "/api/Poli/GetHTAAssesmentDetails": "Get Poli Assessment records based on TokenId. Use for health technology assessment and reimbursement analysis.",
#                 "/api/Poli/GETIRPDetails": "Get IRP (International Reference Pricing) details. Use for pricing analysis and market access.",
#                 "/api/Poli/GetDeletedPoliDrugsDetails": "Get deleted PoliDrugs. Use for database maintenance.",
#                 "/api/Poli/GetDrugs": "Get drugs data. Use for general drug information and therapy mapping.",
#                 "/api/Poli/GetTherapyAreas": "Get therapy areas. Essential for disease classification and therapeutic area analysis.",
#                 "/api/Poli/GetTherapyLines": "Get therapy lines. Use for treatment sequence and positioning analysis.",
#                 "/api/Poli/GetTherapyTypes": "Get therapy types. Use for treatment classification and competitive analysis.",
#                 "/api/Poli/GetDiseaseStage": "Get disease stages. Essential for patient segmentation and staging analysis.",
#                 "/api/Poli/GetForexCurrencies": "Get forex currencies. Use for international market analysis and currency conversion.",
#                 "/api/Poli/GetCurrencyConverter": "Get currency converter. Use for financial analysis across different markets."
#             },
#             "rmt": {
#                 "/api/RMT/GetRMTDetails": "Provides RMT (Risk Management Tool) data based on keyword search or Drug ID. Use for safety and risk analysis.",
#                 "/api/RMT/GetRMTDailyUpdates": "Provides daily updates for RMT data based on from date and to date. Use for recent safety updates."
#             },
#             "sites": {
#                 "/api/Sites/GetTrialSitesDetails": "Provides trial site data based on keyword search or Site ID. Essential for clinical development planning and site selection.",
#                 "/api/Sites/GetTrialSiteDailyUpdates": "Provides daily updates for trial sites data based on from date and to date. Use for recent site developments.",
#                 "/api/Sites/GetSiteCoordinatorDetails": "Provides site coordinator data based on SiteCoordinatorName or SiteCoordinatorId. Use for operational planning and site management."
#             }
#         }
        
#         # Define section characteristics and keywords
#         self.section_mapping = {
#             ReportSection.DISEASE_OVERVIEW: {
#                 "keywords": ["disease", "symptoms", "diagnosis", "etiology", "pathology", "treatment paradigm", "unmet needs", "patient segments"],
#                 "api_endpoints": ["Local", "pubmed_central", "tavily"],
#                 "persona": "MD, PhD with specialization in relevant disease",
#                 "primary_globaldata_apis": ["/api/Poli/GetTherapyAreas", "/api/Poli/GetDiseaseStage"]
#             },
#             ReportSection.EPIDEMIOLOGY: {
#                 "keywords": ["prevalence", "incidence", "epidemiology", "patient population", "demographics", "geography", "forecast"],
#                 "api_endpoints": ["tavily", "pubmed_central", "Local"],
#                 "persona": "PhD epidemiologist",
#                 "primary_globaldata_apis": ["/api/Epidemiology/GetEpidemiologyDetails"]
#             },
#             ReportSection.COMPETITIVE_LANDSCAPE: {
#                 "keywords": ["pipeline", "competitors", "drugs", "clinical trials", "market share", "pricing", "reimbursement", "assets"],
#                 "api_endpoints": ["tavily", "Local", "pubmed_central"],
#                 "persona": "Wall street analyst with biotech focus",
#                 "primary_globaldata_apis": ["/api/Drugs/GetPipelineDrugDetails", "/api/ClinicalTrials/GetClinicalTrialsDetails"]
#             },
#             ReportSection.DEAL_LANDSCAPE: {
#                 "keywords": ["deals", "licensing", "partnerships", "acquisitions", "M&A", "collaborations", "investment", "financing"],
#                 "api_endpoints": ["tavily", "Local", "pubmed_central"],
#                 "persona": "Wall street analyst with biotech focus",
#                 "primary_globaldata_apis": ["/api/Deals/GetDealsDetails"]
#             },
#             ReportSection.TARGET_PRODUCT_PROFILE: {
#                 "keywords": ["target product profile", "TPP", "differentiation", "endpoints", "dosing", "route of administration", "comparator"],
#                 "api_endpoints": ["tavily", "Local", "pubmed_central"],
#                 "persona": "Chief medical officer of pharmaceutical company",
#                 "primary_globaldata_apis": ["/api/Drugs/GetPipelineDrugDetails", "/api/Biomarker/GetBiomarkersDetails"]
#             },
#             ReportSection.MARKET_MODEL: {
#                 "keywords": ["market size", "revenue forecast", "sales", "pricing", "market penetration", "addressable market"],
#                 "api_endpoints": ["tavily", "Local", "pubmed_central"],
#                 "persona": "Wall street analyst with biotech focus",
#                 "primary_globaldata_apis": ["/api/DrugSales/GetDrugSalesDetails", "/api/NPV/GetNPVDetails"]
#             },
#             ReportSection.CLINICAL_DEVELOPMENT: {
#                 "keywords": ["clinical trial design", "endpoints", "biomarkers", "enrollment", "PoS", "budget", "recruitment"],
#                 "api_endpoints": ["tavily", "Local", "pubmed_central"],
#                 "persona": "Chief medical officer with clinical trial experience",
#                 "primary_globaldata_apis": ["/api/ClinicalTrials/GetClinicalTrialsDetails", "/api/Sites/GetTrialSitesDetails"]
#             },
#             ReportSection.KOLS: {
#                 "keywords": ["key opinion leaders", "KOLs", "investigators", "experts", "consultants", "clinical trial experience"],
#                 "api_endpoints": ["tavily", "Local", "pubmed_central"],
#                 "persona": "Business development associate",
#                 "primary_globaldata_apis": ["/api/Investigators/GetInvestigatorsDetails"]
#             }
#         }

#     def _get_llm_selected_apis(self, query: str, section: ReportSection, keywords: List[str]) -> List[str]:
#         """Use LLM to intelligently select the most relevant GlobalData APIs for the specific query and section"""
        
#         # Get primary APIs for this section
#         primary_apis = self.section_mapping[section]["primary_globaldata_apis"]
        
#         # Create comprehensive API catalog with descriptions
#         api_catalog = ""
#         for category, apis in self.globaldata_apis.items():
#             api_catalog += f"\n## {category.upper()} APIs:\n"
#             for endpoint, description in apis.items():
#                 api_catalog += f"- {endpoint}: {description}\n"
        
#         prompt = f"""
#         As an expert pharmaceutical data analyst, select the most relevant GlobalData APIs for this specific research query and report section.

#         **Original Query**: "{query}"
#         **Report Section**: {section.value.replace('_', ' ').title()}
#         **Section Keywords**: {', '.join(keywords)}
#         **Primary APIs for this section**: {', '.join(primary_apis)}

#         **Available GlobalData APIs:**
#         {api_catalog}

#         **Instructions:**
#         1. ALWAYS include the primary APIs for this section: {', '.join(primary_apis)}
#         2. Add ONLY the additional APIs that are specifically needed for this exact query
#         3. Be selective - only add APIs that directly contribute to answering the query
#         4. Consider the specific disease/indication, therapy area, and research focus
#         5. Maximum 5 APIs total (including primary APIs)

#         **Selection Criteria:**
#         - Does this API provide data that directly answers the query?
#         - Is this API essential for the specific section analysis?
#         - Does this API complement the primary APIs without redundancy?

#         Respond in JSON format with ONLY the selected API endpoints:
#         {{
#             "selected_apis": [
#                 "/api/endpoint1",
#                 "/api/endpoint2",
#                 ...
#             ],
#             "rationale": "Brief explanation of why these specific APIs were selected"
#         }}
#         """
        
#         try:
#             response = self.client.chat.completions.create(
#                 model=self.model,
#                 messages=[{"role": "user", "content": prompt}],
#                 temperature=0.1
#             )
            
#             result = json.loads(response.choices[0].message.content)
#             selected_apis = result.get("selected_apis", primary_apis)
            
#             # Ensure primary APIs are always included
#             final_apis = list(set(primary_apis + selected_apis))
            
#             # Limit to maximum 5 APIs
#             return final_apis[:5]
            
#         except Exception as e:
#             print(f"Error in LLM API selection: {e}")
#             # Fallback to primary APIs only
#             return primary_apis

#     def analyze_query(self, user_query: str) -> QueryAnalysisResult:
#         """
#         Main function to analyze user query and break it down into sections
        
#         Args:
#             user_query: The user's research query
            
#         Returns:
#             QueryAnalysisResult: Comprehensive analysis of the query
#         """
#         # Step 1: Identify relevant sections
#         section_relevance = self._identify_relevant_sections(user_query)

#         # Step 2: Generate section-specific analyses
#         section_analyses = []
#         for section, relevance_score in section_relevance.items():
#             if relevance_score > 0.1:  # Only include sections with significant relevance
#                 analysis = self._analyze_section(user_query, section, relevance_score)
#                 section_analyses.append(analysis)
        
#         # Step 3: Determine primary and secondary focuses
#         primary_focus, secondary_focuses = self._determine_focus_hierarchy(section_analyses)
#         # Step 4: Assess overall complexity
#         complexity = self._assess_complexity(user_query, section_analyses)
        
#         return QueryAnalysisResult(
#             original_query=user_query,
#             detected_sections=section_analyses,
#             primary_focus=primary_focus,
#             secondary_focuses=secondary_focuses,
#             overall_complexity=complexity
#         )

#     def _identify_relevant_sections(self, query: str) -> Dict[ReportSection, float]:
#         """Identify which report sections are relevant to the query"""
        
#         prompt = f"""
#         Analyze the following research query and determine which report sections are relevant.
        
#         Query: "{query}"
        
#         Report Sections:
#         1. Disease Overview - Disease background, symptoms, diagnosis, treatment paradigm, unmet needs
#         2. Epidemiology - Prevalence, incidence, patient populations, geographic distribution
#         3. Competitive Landscape - Pipeline drugs, clinical trials, marketed products, competitors
#         4. Deal Landscape - Licensing deals, partnerships, acquisitions, investments
#         5. Target Product Profile - Product differentiation, clinical endpoints, dosing, administration
#         6. Market Model - Market size, revenue forecasts, pricing, penetration rates
#         7. Clinical Development - Trial design, endpoints, biomarkers, enrollment, budgets
#         8. KOLs - Key opinion leaders, investigators, clinical experts
        
#         For each section, provide a relevance score from 0.0 to 1.0 (where 1.0 is highly relevant).
        
#         Respond in JSON format:
#         {{
#             "disease_overview": 0.0-1.0,
#             "epidemiology": 0.0-1.0,
#             "competitive_landscape": 0.0-1.0,
#             "deal_landscape": 0.0-1.0,
#             "target_product_profile": 0.0-1.0,
#             "market_model": 0.0-1.0,
#             "clinical_development": 0.0-1.0,
#             "kols": 0.0-1.0
#         }}
#         """
        
#         response = self.client.chat.completions.create(
#             model=self.model,
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.1
#         )
        
#         try:
#             scores = json.loads(response.choices[0].message.content)
#             return {ReportSection(k): v for k, v in scores.items()}
#         except:
#             # Fallback: basic keyword matching
#             return self._fallback_section_identification(query)

#     def _analyze_section(self, query: str, section: ReportSection, relevance_score: float) -> SectionAnalysis:
#         """Generate detailed analysis for a specific section"""
        
#         section_info = self.section_mapping[section]
        
#         prompt = f"""
#         As a {section_info['persona']}, analyze the following query for the {section.value.replace('_', ' ').title()} section.
        
#         Original Query: "{query}"
#         Section Focus: {section.value.replace('_', ' ').title()}
#         Section Keywords: {', '.join(section_info['keywords'])}
        
#         Generate:
#         1. ONE primary sub-query that captures the main research question for this section
#         2. ONE comprehensive sub-query that covers all remaining aspects and details needed for this section
#         3. Maximum of 3-5 relevant keywords for Global data search/API calls
#            Out of these 5 keywords 1 to 2 keywords should be pointing to relevant disease like "non-small cell lung cancer", "small cell lung cancer", "cancer",

#         4. Rationale for why this section is relevant (2-3 sentences)
        
#         Focus on the aspects of the original query that relate to this specific section.
#         Make the primary sub-query direct and actionable, and the comprehensive sub-query should cover all additional details, nuances, and supporting information needed.
        
#         Respond in JSON format:
#         {{
#             "primary_query": "main research question",
#             "comprehensive_query": "detailed query covering all remaining aspects",
#             "keywords": ["keyword1", "keyword2", ...],
#             "rationale": "explanation of relevance"
#         }}
#         """
        
#         response = self.client.chat.completions.create(
#             model=self.model,
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.2
#         )
#         try:
#             analysis = json.loads(response.choices[0].message.content)
#             sub_queries = [analysis["primary_query"], analysis["comprehensive_query"]]
            
#             # Use LLM to select the most relevant APIs
#             selected_apis = self._get_llm_selected_apis(query, section, analysis["keywords"])
            
#             return SectionAnalysis(
#                 section=section,
#                 relevance_score=relevance_score,
#                 sub_queries=sub_queries,
#                 keywords=analysis["keywords"],
#                 api_endpoints=section_info["api_endpoints"],
#                 relevant_globaldata_apis=selected_apis,
#                 rationale=analysis["rationale"]
#             )
#         except:
#             # Fallback analysis
#             return self._fallback_section_analysis(query, section, relevance_score)

#     def _determine_focus_hierarchy(self, analyses: List[SectionAnalysis]) -> Tuple[str, List[str]]:
#         """Determine primary and secondary focus areas"""
#         if not analyses:
#             return "Unknown", []
        
#         # Sort by relevance score
#         sorted_analyses = sorted(analyses, key=lambda x: x.relevance_score, reverse=True)
        
#         primary = sorted_analyses[0].section.value.replace('_', ' ').title()
#         secondary = [a.section.value.replace('_', ' ').title() for a in sorted_analyses[1:4]]
        
#         return primary, secondary

#     def _assess_complexity(self, query: str, analyses: List[SectionAnalysis]) -> str:
#         """Assess the overall complexity of the query"""
#         num_sections = len(analyses)
#         avg_relevance = sum(a.relevance_score for a in analyses) / len(analyses) if analyses else 0
        
#         if num_sections >= 6 or avg_relevance > 0.8:
#             return "High - Comprehensive multi-section analysis required"
#         elif num_sections >= 3 or avg_relevance > 0.6:
#             return "Medium - Multi-section analysis with moderate depth"
#         else:
#             return "Low - Focused analysis on specific areas"

#     def _fallback_section_identification(self, query: str) -> Dict[ReportSection, float]:
#         """Fallback method using keyword matching"""
#         scores = {}
#         query_lower = query.lower()
        
#         for section, info in self.section_mapping.items():
#             score = 0
#             for keyword in info["keywords"]:
#                 if keyword.lower() in query_lower:
#                     score += 0.2
#             scores[section] = min(score, 1.0)
        
#         return scores

#     def _fallback_section_analysis(self, query: str, section: ReportSection, relevance_score: float) -> SectionAnalysis:
#         """Fallback section analysis"""
#         section_info = self.section_mapping[section]
        
#         # Use primary APIs as fallback
#         primary_apis = section_info["primary_globaldata_apis"]
        
#         primary_query = f"What are the key {section.value.replace('_', ' ')} aspects for: {query[:100]}..."
#         comprehensive_query = f"Provide comprehensive analysis of all {section.value.replace('_', ' ')} factors, including detailed information, supporting data, and contextual insights related to the query."
        
#         return SectionAnalysis(
#             section=section,
#             relevance_score=relevance_score,
#             sub_queries=[primary_query, comprehensive_query],
#             keywords=section_info["keywords"][:5],
#             api_endpoints=section_info["api_endpoints"],
#             relevant_globaldata_apis=primary_apis,
#             rationale=f"This section is relevant based on keyword matching and query context."
#         )

#     def generate_research_plan(self, analysis_result: QueryAnalysisResult) -> str:
#         """Generate a structured research plan based on the analysis"""
        
#         plan = """## Detailed Section Breakdown"""
        
#         for i, section_analysis in enumerate(analysis_result.detected_sections, 1):
#             plan += f"""
# ### {i}. {section_analysis.section.value.replace('_', ' ').title()}
# **Relevance Score**: {section_analysis.relevance_score:.2f}
# **Rationale**: {section_analysis.rationale}

# **Sub-Queries**:
# 1. **Primary Query**: {section_analysis.sub_queries[0]}
# 2. **Comprehensive Query**: {section_analysis.sub_queries[1]}"""
            
#             plan += f"""
# **Keywords**: {', '.join(section_analysis.keywords)}
# **External Sources**: {', '.join(section_analysis.api_endpoints)}
# **Relevant GlobalData APIs**:
# """
#             for api in section_analysis.relevant_globaldata_apis:
#                 plan += f"- {api}\n"
            
#             plan += "\n"
        
#         return plan

#     def export_for_api_calls(self, analysis_result: QueryAnalysisResult) -> Dict:
#         """Export structured data for API integration"""
        
#         api_structure = {
#             "query_id": hash(analysis_result.original_query),
#             "original_query": analysis_result.original_query,
#             "complexity": analysis_result.overall_complexity,
#             "sections": {}
#         }
        
#         for analysis in analysis_result.detected_sections:
#             api_structure["sections"][analysis.section.value] = {
#                 "relevance_score": analysis.relevance_score,
#                 "sub_queries": analysis.sub_queries,
#                 "search_keywords": analysis.keywords,
#                 "external_api_endpoints": analysis.api_endpoints,
#                 "globaldata_apis": analysis.relevant_globaldata_apis,
#                 "rationale": analysis.rationale
#             }
        
#         return api_structure


import os
import openai
from typing import Dict, List, Optional, Tuple
import json
import re
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

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
    relevant_globaldata_apis: List[str]
    user_insights: Dict[str, str]  # New field for user-provided insights
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
        
        # Define GlobalData API endpoints with detailed descriptions
        self.globaldata_apis = {
            "biomarker": {
                "/api/Biomarker/GetBiomarkersDetails": "Provides biomarkers data based on from date and to date. Use for biomarker research, diagnostic markers, and therapeutic targets.",
                "/api/Biomarker/GetBiomarkersDailyUpdates": "Provides daily updates for biomarkers data based on from date and to date. Use for recent biomarker developments."
            },
            "clinical_trials": {
                "/api/ClinicalTrials/GetClinicalTrialsDetails": "Provides clinical trial data based on keyword search, Clinical ID, from date and to date. Essential for pipeline analysis, competitive landscape, and development timelines.",
                "/api/ClinicalTrials/GetClinicalTrialsLocationsandcontactDetails": "Provides clinical trial locations and contact details based on keyword search, Clinical ID, from date and to date. Use for site selection and operational planning.",
                "/api/ClinicalTrials/GetClinicalTrialsDailyUpdates": "Provides daily updates for clinical trials data based on from date and to date. Use for recent trial developments and status changes."
            },
            "company": {
                "/api/Company/GetCompanyDetails": "Provides company details data based on from date and to date. Essential for competitive landscape, company profiling, and partnership analysis.",
                "/api/Company/GetDailyDeletedCompanies": "Provides daily deleted companies data based on from date and to date. Use for database maintenance and recent company changes."
            },
            "deals": {
                "/api/Deals/GetDealsDetails": "Provides deal data based on keyword search or Deal ID. Critical for deal landscape analysis, partnership trends, and market activity.",
                "/api/Deals/GetDealsDailyUpdates": "Provides daily updates for deals data based on from date and to date. Use for recent deal activity and market movements.",
                "/api/Deals/GetDailyDeletedDeals": "Provides daily deleted deals data based on from date and to date. Use for database maintenance."
            },
            "drugs": {
                "/api/Drugs/GetPipelineDrugDetails": "Provides pipeline drug data based on keyword search or Drug ID. Essential for competitive landscape and pipeline analysis.",
                "/api/Drugs/GetMarketedDrugDetails": "Provides marketed drug data based on keyword search or Drug ID. Use for market analysis and competitive benchmarking.",
                "/api/Drugs/GetDrugsDailyUpdates": "Provides daily updates for drugs data based on from date and to date. Use for recent drug developments.",
                "/api/Drugs/GetHistoryofEvents": "Provides drug history events based on DrugID. Use for timeline analysis and development milestones.",
                "/api/Drugs/GetStubDrugs": "Provides stub drugs data based on from date and to date. Use for incomplete drug records."
            },
            "drug_sales": {
                "/api/DrugSales/GetDrugSalesDetails": "Provides drug sales data based on keyword search or DrugID. Essential for market model, revenue analysis, and commercial performance.",
                "/api/DrugSales/GetDrugSalesDailyUpdates": "Provides daily updates for drug sales data based on from date and to date. Use for recent sales performance."
            },
            "epidemiology": {
                "/api/Epidemiology/GetEpidemiologyDetails": "Provides epidemiology data based on keyword search or IndicationID. Essential for patient population analysis, disease prevalence, and market sizing."
            },
            "filings": {
                "/api/Filings/GetCompanyFilingListing": "Get company filing records based on published date. Use for regulatory analysis and company financial information.",
                "/api/Filings/GetCompanyFilingDetails": "Get company filing records based on Company ID. Use for detailed company regulatory and financial analysis."
            },
            "investigators": {
                "/api/Investigators/GetInvestigatorsDetails": "Get investigator records based on published date. Essential for KOL identification and clinical trial planning.",
                "/api/Investigators/GetInvestigatorsDailyUpdates": "Provides daily updates for investigators data based on from date and to date. Use for recent investigator activities."
            },
            "loa": {
                "/api/LOA/GetLOADetails": "Provides LOA (Letter of Authorization) details based on DrugName and DrugID. Use for regulatory pathway analysis."
            },
            "news": {
                "/api/News/GetNewsDetails": "Provides news data based on keyword search or NewsArticle ID. Use for market intelligence, recent developments, and industry trends.",
                "/api/News/GetNewsDailyUpdates": "Provides daily updates for news data based on from date and to date. Use for recent news and market developments.",
                "/api/News/GetDailyDeletedNews": "Provides daily deleted news data based on from date and to date. Use for database maintenance."
            },
            "npv": {
                "/api/NPV/GetNPVDetails": "Provides NPV (Net Present Value) data based on DrugName search or DrugID. Essential for market model and valuation analysis."
            },
            "patents": {
                "/api/Patents/GetPatentsListing": "Get patent records based on PublishedDate. Use for intellectual property analysis and competitive intelligence.",
                "/api/Content/GetPatentsDescriptionandClaims": "Get patent descriptions and claims based on ID. Use for detailed patent analysis and IP landscape."
            },
            "poli": {
                "/api/Poli/GetPoliDrugs": "Get PoliDrugs records based on PoliID. Use for policy and regulatory drug information.",
                "/api/Poli/GetPoliTherapyDetails": "Get PoliTherapies records based on TherapyViewID. Essential for therapy area analysis and treatment landscape.",
                "/api/Poli/GetHTAAssesmentDetails": "Get Poli Assessment records based on TokenId. Use for health technology assessment and reimbursement analysis.",
                "/api/Poli/GETIRPDetails": "Get IRP (International Reference Pricing) details. Use for pricing analysis and market access.",
                "/api/Poli/GetDeletedPoliDrugsDetails": "Get deleted PoliDrugs. Use for database maintenance.",
                "/api/Poli/GetDrugs": "Get drugs data. Use for general drug information and therapy mapping.",
                "/api/Poli/GetTherapyAreas": "Get therapy areas. Essential for disease classification and therapeutic area analysis.",
                "/api/Poli/GetTherapyLines": "Get therapy lines. Use for treatment sequence and positioning analysis.",
                "/api/Poli/GetTherapyTypes": "Get therapy types. Use for treatment classification and competitive analysis.",
                "/api/Poli/GetDiseaseStage": "Get disease stages. Essential for patient segmentation and staging analysis.",
                "/api/Poli/GetForexCurrencies": "Get forex currencies. Use for international market analysis and currency conversion.",
                "/api/Poli/GetCurrencyConverter": "Get currency converter. Use for financial analysis across different markets."
            },
            "rmt": {
                "/api/RMT/GetRMTDetails": "Provides RMT (Risk Management Tool) data based on keyword search or Drug ID. Use for safety and risk analysis.",
                "/api/RMT/GetRMTDailyUpdates": "Provides daily updates for RMT data based on from date and to date. Use for recent safety updates."
            },
            "sites": {
                "/api/Sites/GetTrialSitesDetails": "Provides trial site data based on keyword search or Site ID. Essential for clinical development planning and site selection.",
                "/api/Sites/GetTrialSiteDailyUpdates": "Provides daily updates for trial sites data based on from date and to date. Use for recent site developments.",
                "/api/Sites/GetSiteCoordinatorDetails": "Provides site coordinator data based on SiteCoordinatorName or SiteCoordinatorId. Use for operational planning and site management."
            }
        }
        
        # User-provided insights for API mappings based on their experience
        self.user_api_insights = {
            "pipeline_analysis": {
                "primary_apis": ["/api/Drugs/GetPipelineDrugDetails"],
                "insights": "Use Drugs Intelligence (Slide 6 & 7) for pipeline programs. Can sort by Molecule Type under Drug Details. Get MoA and Targets information.",
                "filters": "Focus on antibody-based therapeutics (mAbs, ADCs, bispecific antibodies)",
                "additional_data": "Include current assets, discontinued/terminated programs, and preclinical collaborations"
            },
            "partnership_analysis": {
                "primary_apis": ["/api/Deals/GetDealsDetails"],
                "insights": "Use Fundamental Intelligence > Deals > Company ID Search for partnership details. Search affiliated drugs for comprehensive view.",
                "scope": "Include acquisitions, in-licensing agreements, option agreements, and collaborations",
                "details": "Get licensing terms, scope, exercised options, and remaining rights information"
            },
            "target_identification": {
                "primary_apis": ["/api/Drugs/GetPipelineDrugDetails", "/api/Deals/GetDealsDetails"],
                "insights": "Get targets from MoA or Targets fields in Drugs Intelligence. Use Deals data for access rights via acquisitions and licensing.",
                "classification": "Determine full rights, partial/limited rights, or optioned/future rights",
                "limitations": "Check for restrictions (ADCs only, geographic limitations, co-development obligations)"
            },
            "competitive_landscape": {
                "primary_apis": ["/api/Drugs/GetPipelineDrugDetails", "/api/Drugs/GetMarketedDrugDetails"],
                "insights": "Search by target in Drugs Intelligence section to understand competitive landscape",
                "analysis": "Evaluate how crowded or differentiated each target is",
                "benchmarking": "Compare against existing pipeline and marketed assets"
            },
            "epidemiology_analysis": {
                "primary_apis": ["/api/Epidemiology/GetEpidemiologyDetails"],
                "insights": "Use Therapeutic Analysis > Epidemiology (slide 27) for BMI categories and patient segmentation",
                "segmentation": "Analyze by BMI categories (Class I: 30-35, Class II: 35-40, Class III: ≥40)",
                "subgroups": "Segment by diabetes status, prior bariatric surgery, treatment response"
            },
            "market_analysis": {
                "primary_apis": ["/api/DrugSales/GetDrugSalesDetails", "/api/NPV/GetNPVDetails"],
                "insights": "Use Drugs Intelligence Pipeline (Slide 10) for drug sales and consensus forecasts",
                "forecasting": "Focus on therapies with long-term administration profiles (≥12 months)",
                "pricing": "Use Pricing Intelligence for commercial segmentation and payer differentiation"
            },
            "clinical_trials": {
                "primary_apis": ["/api/ClinicalTrials/GetClinicalTrialsDetails", "/api/Sites/GetTrialSitesDetails"],
                "insights": "Use Drugs Intelligence Pipeline + Trials Intelligence for trial design characteristics",
                "analysis": "Focus on time to intervention post-MI, target populations, primary endpoints",
                "geographic": "Consider differences in standards of care across US, EU, China"
            },
            "deal_landscape": {
                "primary_apis": ["/api/Deals/GetDealsDetails"],
                "insights": "Use Fundamental Intelligence > Deals (slide 30) for commercial benchmarks",
                "scope": "Include recent deal terms, partnerships, exits for relevant assets",
                "analysis": "Evaluate deal activity trends and market movements"
            }
        }
        
        # Define section characteristics and keywords with enhanced user insights
        self.section_mapping = {
            ReportSection.DISEASE_OVERVIEW: {
                "keywords": ["disease", "symptoms", "diagnosis", "etiology", "pathology", "treatment paradigm", "unmet needs", "patient segments"],
                "api_endpoints": ["Local", "pubmed_central", "tavily"],
                "persona": "MD, PhD with specialization in relevant disease",
                "primary_globaldata_apis": ["/api/Poli/GetTherapyAreas", "/api/Poli/GetDiseaseStage"],
                "user_insights": {
                    "focus": "Disease classification and staging analysis",
                    "key_apis": "Therapy areas and disease stage APIs for comprehensive disease mapping"
                }
            },
            ReportSection.EPIDEMIOLOGY: {
                "keywords": ["prevalence", "incidence", "epidemiology", "patient population", "demographics", "geography", "forecast"],
                "api_endpoints": ["tavily", "pubmed_central", "Local"],
                "persona": "PhD epidemiologist",
                "primary_globaldata_apis": ["/api/Epidemiology/GetEpidemiologyDetails"],
                "user_insights": self.user_api_insights["epidemiology_analysis"]
            },
            ReportSection.COMPETITIVE_LANDSCAPE: {
                "keywords": ["pipeline", "competitors", "drugs", "clinical trials", "market share", "pricing", "reimbursement", "assets"],
                "api_endpoints": ["tavily", "Local", "pubmed_central"],
                "persona": "Wall street analyst with biotech focus",
                "primary_globaldata_apis": ["/api/Drugs/GetPipelineDrugDetails", "/api/Drugs/GetMarketedDrugDetails"],
                "user_insights": self.user_api_insights["competitive_landscape"]
            },
            ReportSection.DEAL_LANDSCAPE: {
                "keywords": ["deals", "licensing", "partnerships", "acquisitions", "M&A", "collaborations", "investment", "financing"],
                "api_endpoints": ["tavily", "Local", "pubmed_central"],
                "persona": "Wall street analyst with biotech focus",
                "primary_globaldata_apis": ["/api/Deals/GetDealsDetails"],
                "user_insights": self.user_api_insights["deal_landscape"]
            },
            ReportSection.TARGET_PRODUCT_PROFILE: {
                "keywords": ["target product profile", "TPP", "differentiation", "endpoints", "dosing", "route of administration", "comparator"],
                "api_endpoints": ["tavily", "Local", "pubmed_central"],
                "persona": "Chief medical officer of pharmaceutical company",
                "primary_globaldata_apis": ["/api/Drugs/GetPipelineDrugDetails", "/api/Biomarker/GetBiomarkersDetails"],
                "user_insights": self.user_api_insights["target_identification"]
            },
            ReportSection.MARKET_MODEL: {
                "keywords": ["market size", "revenue forecast", "sales", "pricing", "market penetration", "addressable market"],
                "api_endpoints": ["tavily", "Local", "pubmed_central"],
                "persona": "Wall street analyst with biotech focus",
                "primary_globaldata_apis": ["/api/DrugSales/GetDrugSalesDetails", "/api/NPV/GetNPVDetails"],
                "user_insights": self.user_api_insights["market_analysis"]
            },
            ReportSection.CLINICAL_DEVELOPMENT: {
                "keywords": ["clinical trial design", "endpoints", "biomarkers", "enrollment", "PoS", "budget", "recruitment"],
                "api_endpoints": ["tavily", "Local", "pubmed_central"],
                "persona": "Chief medical officer with clinical trial experience",
                "primary_globaldata_apis": ["/api/ClinicalTrials/GetClinicalTrialsDetails", "/api/Sites/GetTrialSitesDetails"],
                "user_insights": self.user_api_insights["clinical_trials"]
            },
            ReportSection.KOLS: {
                "keywords": ["key opinion leaders", "KOLs", "investigators", "experts", "consultants", "clinical trial experience"],
                "api_endpoints": ["tavily", "Local", "pubmed_central"],
                "persona": "Business development associate",
                "primary_globaldata_apis": ["/api/Investigators/GetInvestigatorsDetails"],
                "user_insights": {
                    "focus": "KOL identification and clinical trial planning",
                    "key_apis": "Investigators API for expert identification and clinical experience mapping"
                }
            }
        }

    def _get_llm_selected_apis(self, query: str, section: ReportSection, keywords: List[str]) -> List[str]:
        """Use LLM to intelligently select the most relevant GlobalData APIs with user insights integration"""
        
        # Get primary APIs and user insights for this section
        section_info = self.section_mapping[section]
        primary_apis = section_info["primary_globaldata_apis"]
        user_insights = section_info.get("user_insights", {})
        
        # Create comprehensive API catalog with descriptions
        api_catalog = ""
        for category, apis in self.globaldata_apis.items():
            api_catalog += f"\n## {category.upper()} APIs:\n"
            for endpoint, description in apis.items():
                api_catalog += f"- {endpoint}: {description}\n"
        
        # Format user insights for the prompt
        insights_text = ""
        if isinstance(user_insights, dict):
            for key, value in user_insights.items():
                insights_text += f"- {key.replace('_', ' ').title()}: {value}\n"
        
        prompt = f"""
        As an expert pharmaceutical data analyst, select the most relevant GlobalData APIs for this specific research query and report section.

        **Original Query**: "{query}"
        **Report Section**: {section.value.replace('_', ' ').title()}
        **Section Keywords**: {', '.join(keywords)}
        **Primary APIs for this section**: {', '.join(primary_apis)}

        **USER INSIGHTS FOR THIS SECTION:**
        {insights_text}

        **Available GlobalData APIs:**
        {api_catalog}

        **Instructions:**
        1. ALWAYS include the primary APIs for this section: {', '.join(primary_apis)}
        2. Consider the user insights provided above - they contain valuable experience-based recommendations
        3. Add ONLY the additional APIs that are specifically needed for this exact query
        4. Be selective - only add APIs that directly contribute to answering the query
        5. Consider the specific disease/indication, therapy area, and research focus
        6. Maximum 5 APIs total (including primary APIs)

        **Enhanced Selection Criteria (based on user insights):**
        - Does this API provide data that directly answers the query?
        - Is this API essential for the specific section analysis?
        - Does this API align with the user's proven successful approaches?
        - Does this API complement the primary APIs without redundancy?
        - Can this API provide the specific filtering/sorting capabilities mentioned in user insights?

        Respond in JSON format with ONLY the selected API endpoints:
        {{
            "selected_apis": [
                "/api/endpoint1",
                "/api/endpoint2",
                ...
            ],
            "rationale": "Brief explanation of why these specific APIs were selected, referencing user insights where applicable"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            selected_apis = result.get("selected_apis", primary_apis)
            
            # Ensure primary APIs are always included
            final_apis = list(set(primary_apis + selected_apis))
            
            # Limit to maximum 5 APIs
            return final_apis[:5]
            
        except Exception as e:
            print(f"Error in LLM API selection: {e}")
            # Fallback to primary APIs only
            return primary_apis

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
            if relevance_score > 0.1:  # Only include sections with significant relevance
                analysis = self._analyze_section(user_query, section, relevance_score)
                print("-"*50)
                print(analysis)
                print("-"*50)
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
        """Generate detailed analysis for a specific section with enhanced user insights"""
        
        section_info = self.section_mapping[section]
        user_insights = section_info.get("user_insights", {})
        
        # Format user insights for the prompt
        insights_text = ""
        if isinstance(user_insights, dict):
            for key, value in user_insights.items():
                insights_text += f"- {key.replace('_', ' ').title()}: {value}\n"
        
        prompt = f"""
        As a {section_info['persona']}, analyze the following query for the {section.value.replace('_', ' ').title()} section.
        
        Original Query: "{query}"
        Section Focus: {section.value.replace('_', ' ').title()}
        Section Keywords: {', '.join(section_info['keywords'])}
        
        **USER INSIGHTS FOR THIS SECTION:**
        {insights_text}
        
        **IMPORTANT:** Incorporate the user insights above into your analysis. These represent proven successful approaches and should guide your sub-query generation.
        
        Generate:
        1. ONE primary sub-query that captures the main research question for this section (incorporating user insights)
        2. ONE comprehensive sub-query that covers all remaining aspects and details needed for this section (leveraging user insights)
        3. Maximum of 3-5 relevant keywords for GlobalData search/API calls
           Out of these 5 keywords, 1 to 2 keywords should be pointing to relevant disease like "non-small cell lung cancer", "small cell lung cancer", "cancer"
        4. Rationale for why this section is relevant (2-3 sentences, mentioning how user insights apply)
        
        Focus on the aspects of the original query that relate to this specific section.
        Make the primary sub-query direct and actionable, and the comprehensive sub-query should cover all additional details, nuances, and supporting information needed.
        
        **Consider user insights for:**
        - Specific data filtering and sorting capabilities
        - Proven successful data sources and approaches
        - Key limitations and considerations to address
        - Integration points with other data sources
        
        Respond in JSON format:
        {{
            "primary_query": "main research question incorporating user insights",
            "comprehensive_query": "detailed query covering all remaining aspects leveraging user insights",
            "keywords": ["keyword1", "keyword2", ...],
            "rationale": "explanation of relevance and how user insights apply"
        }}
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        
        try:
            analysis = json.loads(response.choices[0].message.content)
            sub_queries = [analysis["primary_query"], analysis["comprehensive_query"]]
            
            # Use LLM to select the most relevant APIs
            selected_apis = self._get_llm_selected_apis(query, section, analysis["keywords"])
            
            return SectionAnalysis(
                section=section,
                relevance_score=relevance_score,
                sub_queries=sub_queries,
                keywords=analysis["keywords"],
                api_endpoints=section_info["api_endpoints"],
                relevant_globaldata_apis=selected_apis,
                user_insights=user_insights,
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
        """Fallback section analysis with user insights"""
        section_info = self.section_mapping[section]
        user_insights = section_info.get("user_insights", {})
        
        # Use primary APIs as fallback
        primary_apis = section_info["primary_globaldata_apis"]
        
        primary_query = f"What are the key {section.value.replace('_', ' ')} aspects for: {query[:100]}..."
        comprehensive_query = f"Provide comprehensive analysis of all {section.value.replace('_', ' ')} factors, including detailed information, supporting data, and contextual insights related to the query."
        
        return SectionAnalysis(
            section=section,
            relevance_score=relevance_score,
            sub_queries=[primary_query, comprehensive_query],
            keywords=section_info["keywords"][:5],
            api_endpoints=section_info["api_endpoints"],
            relevant_globaldata_apis=primary_apis,
            user_insights=user_insights,
            rationale=f"This section is relevant based on keyword matching and query context."
        )

    def generate_research_plan(self, analysis_result: QueryAnalysisResult) -> str:
        """Generate a structured research plan based on the analysis"""
        
        plan = """## Detailed Section Breakdown"""
        
        for i, section_analysis in enumerate(analysis_result.detected_sections, 1):
            plan += f"""
### {i}. {section_analysis.section.value.replace('_', ' ').title()}
**Relevance Score**: {section_analysis.relevance_score:.2f}
**Rationale**: {section_analysis.rationale}

**Sub-Queries**:
1. **Primary Query**: {section_analysis.sub_queries[0]}
2. **Comprehensive Query**: {section_analysis.sub_queries[1]}"""
            
            plan += f"""
**Keywords**: {', '.join(section_analysis.keywords)}
**External Sources**: {', '.join(section_analysis.api_endpoints)}
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

# # Example usage and testing
# def main():
#     # Initialize pipeline (you would use your actual OpenAI API key)
#     pipeline = AIAgentQueryPipeline(api_key)
    
#     # Test with the provided prompts
#     test_queries = [
#         """I am working on a project focused on proposing and validating cancer targets for an in-situ CAR-T platform. We are especially interested in cell surface targets relevant to non-small cell lung cancer (NSCLC), small cell lung cancer (SCLC), and colorectal cancer (CRC).
#             AbbVie is our company of interest. Please help with the following research and analysis:
#             1. Pipeline Review: AbbVie (Oncology focus)
#                 • List all AbbVie pipeline programs from the past 3–5 years in NSCLC, SCLC, and CRC.
#                 • Include current assets, discontinued/terminated programs, and announced preclinical collaborations.
#                 • Focus on programs involving antibody-based therapeutics (e.g., monoclonal antibodies, ADCs, bispecific antibodies).

#             2. Target Identification
#                 • For each pipeline asset, identify the associated antigen/target (e.g., DLL3, CEACAM5, TROP2).
#                 • Expand to include targets AbbVie may have access to via:
#                 • Acquisitions (e.g., full rights as with full M&A deals),
#                 • In-licensing agreements (include the licensing terms and scope if available), or
#                 • Option agreements or collaborations (include any known status of exercised options or remaining rights).

#             3.  Target Rights Classification
#                 • For each target, clearly indicate AbbVie’s ownership status:
#                     ◦ Full rights (via acquisition or full internal development)
#                     ◦ Partial/limited rights (e.g., for a specific indication, territory, or therapeutic modality)
#                     ◦ Optioned/future rights (if AbbVie retains the right to pursue the target under certain conditions)
#                 • Describe the limitations of each access type in practical terms, e.g.:
#                     ◦ Restrictions to ADCs only
#                     ◦ Limited geographic commercialization
#                     ◦ Co-development obligations

#             4. In-Situ CAR-T Suitability & Prioritization
#             Prioritize identified targets for their potential use in our in-situ CAR-T platform based on:
#                 • Tumor specificity and overexpression in NSCLC, SCLC, or CRC
#                 • Cell surface stability/internalization behavior
#                 • Prior evidence in CAR-T or ADC platforms
#                 • Expression in normal tissues (i.e., toxicity concerns)
#                 • Competitive landscape (how crowded or differentiated the target is)

#             5. Structured Output Format
#             Please return results in a table with these columns:
#                 • Target 
#                 • Tumor Type(s) 
#                 • AbbVie Source (Pipeline/Partner) 
#                 • Partner/Company 
#                 • Rights Type (Acquisition/In-License/Option) 
#                 • Rights Details 
#                 • Platform Type (ADC, mAb, etc.) 
#                 • CAR-T Suitability Score (1-5) 
#                 • Other Notes

#             Highlight any underexplored or emerging targets in AbbVie’s ecosystem that might be especially attractive or differentiated for in-situ CAR-T development, particularly those not widely used in current CAR-T pipelines.
#             """,
                    
#                     """My company is evaluating the opportunity for a high dose once monthly injectable GLP-1/GIP/Glucagon receptor triple agonist for long-term weight loss maintenance therapy for obesity. Evaluate the market opportunity and unmet need for long-term obesity maintenance therapies. Focus on segmentation across the following axes:
#                 • BMI categories: Class I (30–35), Class II (35–40), Class III (≥40)
#                 • Patient subgroups: with vs. without Type 2 diabetes, prior bariatric surgery, responders vs. non-responders to induction therapy
#                 • Current standard of care and limitations (e.g., semaglutide, tirzepatide, lifestyle adherence, drop-off rates after weight loss plateau)
#                 • Pipeline therapies explicitly being developed or positioned for maintenance (vs. induction), including mechanisms (e.g., amylin analogs, GLP-1/GIP modulators, FGF21 analogs, etc.)
#                 • Real-world adherence data and discontinuation drivers post-weight loss
#                 • Expected commercial segmentation: e.g., how payers and physicians differentiate between induction and maintenance use (pricing, access hurdles)
#                 • Sales forecasts for therapies with long-term administration profiles (≥12 months)
#                 • Competitive positioning of novel candidates offering less frequent dosing, improved tolerability, or weight regain prevention efficacy
#             """,
                    
#                     """Conduct a comprehensive analysis of the therapeutic landscape for post-myocardial infarction (MI) treatment, with a focus on agents targeting cardioprotective or remodeling-prevention mechanisms. Include:
#                 • List of active clinical-stage programs (Ph1–Ph3) in post-MI or ischemia-reperfusion settings, segmented by MOA (e.g., mitochondrial protection, anti-inflammatory, anti-fibrotic, stem cell-derived, YAP activators, etc.)
#                 • Trial design characteristics (e.g., time to intervention post-MI, target patient population, primary endpoints)
#                 • Unmet needs in early-phase or subacute cardioprotection, especially in the context of modern PCI and dual antiplatelet therapy (DAPT)
#                 • Commercial benchmarks (recent deal terms, partnerships, or exits for post-MI assets)
#                 • Any examples of prior trial failures in this space and why they failed 
#                 • Geographic considerations (e.g., differences in standards of care or trial feasibility across US, EU, China)
#             """
#                 ]
    
#     for i, query in enumerate(test_queries, 1):
#         print(f"\n{'='*60}")
#         print(f"ANALYSIS {i}")
#         print(f"{'='*60}")
        
#         try:
#             result = pipeline.analyze_query(query)
#             # research_plan = pipeline.generate_research_plan(result)
#             # print(research_plan)
            
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