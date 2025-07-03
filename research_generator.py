import json
import os
import asyncio
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import pandas as pd
from datetime import datetime

# GPT Researcher imports
from gpt_researcher import GPTResearcher
from gpt_researcher.config import Config
from global_data_api import call_api_function
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.environ["RETRIEVER"] = "tavily, pubmed_central"
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")

class AbbVieResearchPipeline:
    """Main research pipeline for AbbVie cancer target analysis"""
    
    def __init__(self, config_path: str = None):
        self.config = Config() if not config_path else Config(config_path)
        self.doc_path = "./my-docs"
        self.prompts_path = "./prompts"
        self.research_results = {}
        
        # Ensure proper environment variables for hybrid research
        self.setup_environment()
        
    def setup_environment(self):
        """Setup environment variables for GPT Researcher"""
        # Required for hybrid research
        os.environ["DOC_PATH"] = self.doc_path
        
        # Ensure REPORT_SOURCE is set correctly
        if "REPORT_SOURCE" not in os.environ:
            os.environ["REPORT_SOURCE"] = ""  # Empty string for hybrid mode
        
        # Log current environment
        logger.info(f"🔧 Environment Setup:")
        logger.info(f"  - DOC_PATH: {os.environ.get('DOC_PATH')}")
        logger.info(f"  - REPORT_SOURCE: '{os.environ.get('REPORT_SOURCE')}'")
        logger.info(f"  - RETRIEVER: {os.environ.get('RETRIEVER')}")
        logger.info(f"  - OPENAI_API_KEY: {'✓ Set' if os.environ.get('OPENAI_API_KEY') else '❌ Missing'}")
        logger.info(f"  - TAVILY_API_KEY: {'✓ Set' if os.environ.get('TAVILY_API_KEY') else '❌ Missing'}")
        
    def load_research_plan(self, plan_file: str) -> Dict[str, Any]:
        """Load research plan from JSON file"""
        try:
            with open(plan_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Research plan file not found: {plan_file}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing research plan: {str(e)}")
            return {}
    
    def load_section_prompt(self, section_name: str) -> str:
        """Load custom prompt for specific section"""
        prompt_file = Path(self.prompts_path) / f"{section_name}.txt"
        
        try:
            with open(prompt_file, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            logger.warning(f"Prompt file not found for section: {section_name}")
            return self.get_default_prompt(section_name)
    
    def get_default_prompt(self, section_name: str) -> str:
        """Get default prompt if section-specific prompt is not found"""
        default_prompts = {
            'disease_overview': """
            Provide a comprehensive overview of the specified diseases including:
            - Etiology and pathophysiology
            - Current treatment paradigms
            - Unmet medical needs
            - Role of cell surface targets
            Focus on factual, evidence-based information. Do not include introduction or conclusion.
            """,
            'epidemiology': """
            Analyze epidemiological data including:
            - Prevalence and incidence rates
            - Patient demographics and geographical distribution
            - Forecasted trends
            - Potential patient population for targeted therapies
            Present data in a structured format with relevant statistics.
            """,
            'competitive_landscape': """
            Analyze the competitive landscape focusing on:
            - Key competitors and their pipeline programs
            - Market positioning and differentiation
            - Target overlap and competitive advantages
            - Emerging opportunities and threats
            Provide strategic insights without editorial commentary.
            """,
            'deal_landscape': """
            Review deal activities including:
            - Acquisitions, licensing agreements, and collaborations
            - Terms, scope, and limitations of deals
            - Rights and ownership status
            - Strategic implications for target access
            Focus on factual deal information and implications.
            """,
            'target_product_profile': """
            Analyze target product profiles including:
            - Associated antigens and targets
            - Rights classification and limitations
            - Suitability for CAR-T platforms
            - Differentiation opportunities
            Provide technical assessment without subjective opinions.
            """,
            'market_model': """
            Analyze market dynamics including:
            - Market size and revenue forecasts
            - Pricing and reimbursement considerations
            - Market penetration potential
            - Commercial viability
            Present financial and market data objectively.
            """,
            'clinical_development': """
            Review clinical development aspects including:
            - Trial design and endpoints
            - Biomarker strategies
            - Enrollment criteria and recruitment
            - Development risks and opportunities
            Focus on clinical and regulatory information.
            """,
            'kols': """
            Identify key opinion leaders including:
            - Principal investigators and experts
            - Their roles and contributions
            - Expertise in relevant therapeutic areas
            - Potential collaboration opportunities
            Provide factual information about KOL involvement.
            """
        }
        
        return default_prompts.get(section_name, "Conduct comprehensive research on the specified topic.")
    
    async def fetch_api_data(self, section_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch data from GlobalData APIs for a section with robust error handling"""
        api_data = {}
        successful_calls = 0
        total_calls = 0
        
        if 'globaldata_apis' in section_data:
            for api_endpoint in section_data['globaldata_apis']:
                total_calls += 1
                parts = api_endpoint.strip("/").split("/")
                api_category = parts[1] if len(parts) > 1 else 'unknown'
                function_name = parts[2] if len(parts) > 2 else 'unknown'
                
                # Get query and keywords from section data
                query = section_data.get('sub_queries', [''])[0] if section_data.get('sub_queries') else ''
                keywords = section_data.get('search_keywords', [])
                
                try: 
                    logger.info(f"Calling API: {api_endpoint}")
                    data = call_api_function(function_name, api_category, query, keywords)
                    
                    # Check if data is valid and not empty
                    if data and data != {} and data is not None:
                        api_data[function_name] = data
                        successful_calls += 1
                        logger.info(f"✓ Successfully fetched {function_name} data")
                    else:
                        logger.warning(f"⚠ API {function_name} returned empty/null data")
                        api_data[function_name] = {'status': 'no_data', 'message': 'API returned empty response'}
                        
                except Exception as e:
                    logger.error(f"✗ Failed to fetch {function_name} data: {str(e)}")
                    api_data[function_name] = {'status': 'error', 'error': str(e)}
        
        # Log API call summary
        logger.info(f"API calls summary: {successful_calls}/{total_calls} successful")
        
        return {
            'data': api_data,
            'summary': {
                'total_calls': total_calls,
                'successful_calls': successful_calls,
                'success_rate': (successful_calls / total_calls * 100) if total_calls > 0 else 0
            }
        }
    
    async def conduct_section_research(self, section_name: str, section_data: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct research for a specific section with fallback to GPT Researcher"""
        logger.info(f"🔍 Starting research for section: {section_name}")
        
        # Check if local documents directory exists
        doc_path = Path(self.doc_path)
        if not doc_path.exists():
            logger.warning(f"⚠ Local documents directory not found: {self.doc_path}")
            doc_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 Created local documents directory: {self.doc_path}")
        
        # Check for documents in the directory
        doc_files = list(doc_path.glob("**/*"))
        doc_files = [f for f in doc_files if f.is_file() and f.suffix.lower() in ['.pdf', '.txt', '.docx', '.md', '.xlsx', 'csv']]
        
        if doc_files:
            logger.info(f"📄 Found {len(doc_files)} local documents in {self.doc_path}")
            for doc in doc_files[:5]:  # Show first 5 files
                logger.info(f"  - {doc.name}")
        else:
            logger.warning(f"⚠ No supported documents found in {self.doc_path}")
        
        # Load section-specific prompt
        custom_prompt = self.load_section_prompt(section_name)
        
        # Prepare research query
        main_query = section_data.get('sub_queries', [''])[0] if section_data.get('sub_queries') else ''
        keywords = section_data.get('search_keywords', [])
        
        # Fetch API data (with robust error handling)
        api_result = await self.fetch_api_data(section_data)
        api_data = api_result['data']
        api_summary = api_result['summary']
        
        # Determine if we have sufficient API data
        has_useful_api_data = api_summary['successful_calls'] > 0
        
        if has_useful_api_data:
            logger.info(f"✓ API data available for {section_name}, proceeding with hybrid research")
        else:
            logger.warning(f"⚠ No API data available for {section_name}, proceeding with GPT Researcher only")
        
        # Determine report source based on available documents
        if doc_files:
            report_source = "hybrid"  # Use both local docs and web
            logger.info(f"🔗 Using hybrid research mode (local + web) for {section_name}")
        else:
            report_source = "web"  # Use only web research
            logger.info(f"🌐 Using web-only research mode for {section_name}")
        
        # Configure GPT Researcher with proper settings
        researcher = GPTResearcher(
            query=main_query,
            report_type="research_report",
            source_urls=None,
            config_path=None,
            websocket=None,
            agent=None,
            role=None,
            parent_query=main_query,
            subtopics=[],
            visited_urls=set(),
            verbose=True,
            context=[]
        )
        
        # CRITICAL: Set configuration properly
        researcher.cfg.doc_path = str(doc_path.absolute())  # Use absolute path
        researcher.cfg.report_source = report_source
        
        # Additional configuration for local documents
        if doc_files:
            # Set retriever to include local documents
            researcher.cfg.retriever = "tavily,local"  # Hybrid retrieval
            logger.info(f"📚 Configured retriever for local documents: {researcher.cfg.retriever}")
        
        logger.info(f"⚙️ GPT Researcher Config:")
        logger.info(f"  - doc_path: {researcher.cfg.doc_path}")
        logger.info(f"  - report_source: {researcher.cfg.report_source}")
        logger.info(f"  - retriever: {getattr(researcher.cfg, 'retriever', 'default')}")
        
        try:
            # Conduct research (this will always proceed regardless of API status)
            logger.info(f"🔬 Conducting GPT Researcher analysis for {section_name}")
            research_result = await researcher.conduct_research()
            
            # Create enhanced prompt that incorporates API data if available
            enhanced_prompt = self.create_enhanced_prompt(custom_prompt, api_data, has_useful_api_data)
            
            # Generate report
            logger.info(f"📝 Generating research report for {section_name}")
            report = await researcher.write_report(custom_prompt=enhanced_prompt)
            
            # Combine research result with API data
            combined_data = {
                'section': section_name,
                'status': 'success',
                'research_report': report,
                'api_data': api_data,
                'api_summary': api_summary,
                'has_api_data': has_useful_api_data,
                'keywords_used': keywords,
                'sources': list(researcher.visited_urls) if hasattr(researcher, 'visited_urls') else [],
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Successfully completed research for section: {section_name}")
            return combined_data
            
        except Exception as e:
            logger.error(f"❌ Error conducting research for {section_name}: {str(e)}")
            
            # Even if research fails, return what we have
            return {
                'section': section_name,
                'status': 'error',
                'error': str(e),
                'api_data': api_data,
                'api_summary': api_summary,
                'has_api_data': has_useful_api_data,
                'keywords_used': keywords,
                'timestamp': datetime.now().isoformat()
            }
    
    def create_enhanced_prompt(self, base_prompt: str, api_data: Dict[str, Any], has_api_data: bool) -> str:
        """Create enhanced prompt that incorporates API data context"""
        if not has_api_data:
            return base_prompt
        
        # Create context from successful API calls
        api_context = "\n\nAdditional Context from API Data:\n"
        for endpoint, data in api_data.items():
            if isinstance(data, dict) and data.get('status') != 'error' and data.get('status') != 'no_data':
                api_context += f"- {endpoint}: Data available for analysis\n"
        
        enhanced_prompt = f"{base_prompt}\n{api_context}\nPlease incorporate relevant information from the API data where applicable."
        
        return enhanced_prompt
    
    async def run_complete_research(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run complete research pipeline for all sections"""
        logger.info("🚀 Starting complete research pipeline")
        
        sections = plan_data.get('sections', {})
        results = {}
        
        # Sort sections by relevance score (highest first)
        sorted_sections = sorted(
            sections.items(), 
            key=lambda x: x[1].get('relevance_score', 0), 
            reverse=True
        )
        
        total_sections = len(sorted_sections)
        successful_sections = 0
        
        for i, (section_name, section_data) in enumerate(sorted_sections, 1):
            logger.info(f"📊 Processing section {i}/{total_sections}: {section_name} (relevance: {section_data.get('relevance_score', 0)})")
            
            try:
                section_result = await self.conduct_section_research(section_name, section_data)
                results[section_name] = section_result
                
                if section_result.get('status') == 'success':
                    successful_sections += 1
                    
            except Exception as e:
                logger.error(f"❌ Critical error processing section {section_name}: {str(e)}")
                results[section_name] = {
                    'section': section_name,
                    'status': 'critical_error',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
        
        # Create final summary
        pipeline_summary = {
            'query_id': plan_data.get('query_id'),
            'original_query': plan_data.get('original_query'),
            'total_sections': total_sections,
            'successful_sections': successful_sections,
            'success_rate': (successful_sections / total_sections * 100) if total_sections > 0 else 0,
            'timestamp': datetime.now().isoformat()
        }
        
        final_results = {
            'pipeline_summary': pipeline_summary,
            'section_results': results
        }
        
        logger.info(f"🎯 Research pipeline completed: {successful_sections}/{total_sections} sections successful")
        
        return final_results
    
    
# async def main():
#     """Main execution function"""
#     # Initialize the research pipeline
#     pipeline = AbbVieResearchPipeline()
    
#     # Load research plan from the provided data
#     plan_data = {
#         "query_id": -5482243310298615493,
#         "original_query": "I am working on a project focused on proposing and validating cancer targets for an in-situ CAR-T platform. We are especially interested in cell surface targets relevant to non-small cell lung cancer (NSCLC), small cell lung cancer (SCLC), and colorectal cancer (CRC). AbbVie is our company of interest.",
#         "complexity": "High - Comprehensive multi-section analysis required",
#         "sections": {
#             "disease_overview": {
#                 "relevance_score": 0.5,
#                 "sub_queries": [
#                     "Provide an overview of non-small cell lung cancer (NSCLC), small cell lung cancer (SCLC), and colorectal cancer (CRC), including their etiology, pathology, and current treatment paradigms."
#                 ],
#                 "search_keywords": [
#                     "non-small cell lung cancer", "small cell lung cancer", "colorectal cancer",
#                     "etiology", "pathology", "treatment paradigm", "unmet needs", "cell surface targets"
#                 ],
#                 "globaldata_apis": [
#                     "/api/Poli/GetTherapyAreas",
#                     "/api/News/GetNewsDetails",
#                     "/api/Poli/GetDiseaseStage"
#                 ]
#             },
#             "competitive_landscape": {
#                 "relevance_score": 1.0,
#                 "sub_queries": [
#                     "What is the competitive landscape for in-situ CAR-T platforms in NSCLC, SCLC, and CRC, and how does AbbVie's pipeline compare?"
#                 ],
#                 "search_keywords": [
#                     "AbbVie", "pipeline", "competitors", "in-situ CAR-T", "NSCLC", "SCLC", "CRC",
#                     "antibody-based therapeutics", "market share", "clinical trials"
#                 ],
#                 "globaldata_apis": [
#                     "/api/Drugs/GetPipelineDrugDetails",
#                     "/api/ClinicalTrials/GetClinicalTrialsDetails",
#                     "/api/Company/GetCompanyDetails"
#                 ]
#             },
#             "deal_landscape": {
#                 "relevance_score": 1.0,
#                 "sub_queries": [
#                     "What are the acquisitions, licensing agreements, and collaborations AbbVie has made in the past 3-5 years related to NSCLC, SCLC, and CRC?"
#                 ],
#                 "search_keywords": [
#                     "AbbVie", "deals", "acquisitions", "licensing agreements", "collaborations",
#                     "NSCLC", "SCLC", "CRC", "rights", "terms", "CAR-T", "targets"
#                 ],
#                 "globaldata_apis": [
#                     "/api/Deals/GetDealsDetails",
#                     "/api/Company/GetCompanyDetails"
#                 ]
#             },
#             "target_product_profile": {
#                 "relevance_score": 1.0,
#                 "sub_queries": [
#                     "What are the key characteristics of the target product profile for AbbVie's oncology pipeline programs in NSCLC, SCLC, and CRC?"
#                 ],
#                 "search_keywords": [
#                     "AbbVie", "oncology", "pipeline", "NSCLC", "SCLC", "CRC", "antigen", "target",
#                     "rights", "CAR-T", "differentiation", "endpoints"
#                 ],
#                 "globaldata_apis": [
#                     "/api/Drugs/GetPipelineDrugDetails",
#                     "/api/Biomarker/GetBiomarkersDetails",
#                     "/api/ClinicalTrials/GetClinicalTrialsDetails"
#                 ]
#             }
#         }
#     }
    
#     # Run the complete research pipeline
#     results = await pipeline.run_complete_research(plan_data)
#     print(results)

# if __name__ == "__main__":
#     asyncio.run(main())