import json
import sys
import pickle
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
from fromat_file_search_tool_results import extract_and_format_data
import requests
from openai import OpenAI
from dotenv import load_dotenv
from typing import Dict, Any, List


load_dotenv()
vector_id = os.getenv("vector_id")
api_key = os.getenv("OPENAI_API_KEY")
globaldata_api_key = os.getenv("GLOBALDATA_API_KEY")  # Add this to your .env file
globaldata_base_url = "https://api.globaldata.com"  # Replace with actual base URL

client = OpenAI(api_key=api_key)

# GlobalData API Tools Definition
globaldata_tools = [
    {
        "type": "function",
        "name": "GetBiomarkersDetails",
        "description": "Get biomarkers data based on from date and to date. Use for biomarker research, diagnostic markers, and therapeutic targets.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "User's original query or request"
                },
                "keywords": {
                    "type": "string",
                    "description": "Search keywords for biomarkers"
                }
            },
            "required": ["user_query", "keywords"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "GetBiomarkersDailyUpdates",
        "description": "Get daily updates for biomarkers data based on from date and to date. Use for recent biomarker developments.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "User's original query or request"
                },
                "keywords": {
                    "type": "string",
                    "description": "Search keywords for biomarkers"
                }
            },
            "required": ["user_query", "keywords"],
            "additionalProperties": False
        }
    },
    
    # ===== CLINICAL TRIALS TOOLS =====
    {
        "type": "function",
        "name": "GetClinicalTrialsDetails",
        "description": "Get clinical trial data based on keyword search, Clinical ID, from date and to date. Essential for pipeline analysis, competitive landscape, and development timelines.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "User's original query or request"
                },
                "keywords": {
                    "type": "string",
                    "description": "Search keywords for clinical trials"
                }
            },
            "required": ["user_query", "keywords"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "GetClinicalTrialsLocationsandcontactDetails",
        "description": "Get clinical trial locations and contact details based on keyword search, Clinical ID, from date and to date. Use for site selection and operational planning.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "User's original query or request"
                },
                "keywords": {
                    "type": "string",
                    "description": "Search keywords for clinical trials"
                }
            },
            "required": ["user_query", "keywords"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "GetClinicalTrialsDailyUpdates",
        "description": "Get daily updates for clinical trials data based on from date and to date. Use for recent trial developments and status changes.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "User's original query or request"
                },
                "keywords": {
                    "type": "string",
                    "description": "Search keywords for clinical trials"
                }
            },
            "required": ["user_query", "keywords"],
            "additionalProperties": False
        }
    },
    
    # ===== COMPANY TOOLS =====
    {
        "type": "function",
        "name": "GetCompanyDetails",
        "description": "Get company details data based on from date and to date. Essential for competitive landscape, company profiling, and partnership analysis.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "User's original query or request"
                },
                "keywords": {
                    "type": "string",
                    "description": "Search keywords for companies"
                }
            },
            "required": ["user_query", "keywords"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "GetDailyDeletedCompanies",
        "description": "Get daily deleted companies data based on from date and to date. Use for database maintenance and recent company changes.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "User's original query or request"
                },
                "keywords": {
                    "type": "string",
                    "description": "Search keywords for companies"
                }
            },
            "required": ["user_query", "keywords"],
            "additionalProperties": False
        }
    },
    
    # ===== DEALS TOOLS =====
    {
        "type": "function",
        "name": "GetDealsDetails",
        "description": "Get deal data based on keyword search or Deal ID. Critical for deal landscape analysis, partnership trends, and market activity.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "User's original query or request"
                },
                "keywords": {
                    "type": "string",
                    "description": "Search keywords for deals or Deal ID"
                }
            },
            "required": ["user_query", "keywords"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "GetDealsDailyUpdates",
        "description": "Get daily updates for deals data based on from date and to date. Use for recent deal activity and market movements.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "User's original query or request"
                },
                "keywords": {
                    "type": "string",
                    "description": "Search keywords for deals"
                }
            },
            "required": ["user_query", "keywords"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "GetDailyDeletedDeals",
        "description": "Get daily updates for deals data based on from date and to date. Use for database maintenance.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "User's original query or request"
                },
                "keywords": {
                    "type": "string",
                    "description": "Search keywords for deals"
                }
            },
            "required": ["user_query", "keywords"],
            "additionalProperties": False
        }
    },
    
    # ===== DRUGS TOOLS =====
    {
        "type": "function",
        "name": "GetPipelineDrugDetails",
        "description": "Get pipeline drug data based on keyword search or Drug ID. Essential for competitive landscape and pipeline analysis.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "User's original query or request"
                },
                "keywords": {
                    "type": "string",
                    "description": "Search keywords for drugs or Drug ID"
                }
            },
            "required": ["user_query", "keywords"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "GetMarketedDrugDetails",
        "description": "Get marketed drug data based on keyword search or Drug ID. Use for market analysis and competitive benchmarking.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "User's original query or request"
                },
                "keywords": {
                    "type": "string",
                    "description": "Search keywords for drugs or Drug ID"
                }
            },
            "required": ["user_query", "keywords"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "GetDrugsDailyUpdates",
        "description": "Get daily updates for drugs data based on from date and to date. Use for recent drug developments.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "User's original query or request"
                },
                "keywords": {
                    "type": "string",
                    "description": "Search keywords for drugs"
                }
            },
            "required": ["user_query", "keywords"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "GetHistoryofEvents",
        "description": "Get drug history events based on DrugID. Use for timeline analysis and development milestones.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "User's original query or request"
                },
                "keywords": {
                    "type": "string",
                    "description": "DrugID for history events"
                }
            },
            "required": ["user_query", "keywords"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "GetStubDrugs",
        "description": "Get stub drugs data based on from date and to date. Use for incomplete drug records.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "User's original query or request"
                },
                "keywords": {
                    "type": "string",
                    "description": "Search keywords for stub drugs"
                }
            },
            "required": ["user_query", "keywords"],
            "additionalProperties": False
        }
    },
    
    # ===== DRUG SALES TOOLS =====
    {
        "type": "function",
        "name": "GetDrugSalesDetails",
        "description": "Get drug sales data based on keyword search or DrugID. Essential for market model, revenue analysis, and commercial performance.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "User's original query or request"
                },
                "keywords": {
                    "type": "string",
                    "description": "Search keywords for drug sales or DrugID"
                }
            },
            "required": ["user_query", "keywords"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "GetDrugSalesDailyUpdates",
        "description": "Get daily updates for drug sales data based on from date and to date. Use for recent sales performance.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "User's original query or request"
                },
                "keywords": {
                    "type": "string",
                    "description": "Search keywords for drug sales"
                }
            },
            "required": ["user_query", "keywords"],
            "additionalProperties": False
        }
    },
    
    # ===== EPIDEMIOLOGY TOOLS =====
    {
        "type": "function",
        "name": "GetEpidemiologyDetails",
        "description": "Get epidemiology data based on keyword search or IndicationID. Essential for patient population analysis, disease prevalence, and market sizing.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "User's original query or request"
                },
                "Indication": {
                    "type": "string",
                    "description": "Enter Indication to search the Data ex: Pain or Pain"
                }
            },
            "required": ["user_query", "keywords"],
            "additionalProperties": False
        }
    },
    
    # ===== FILINGS TOOLS =====
    {
        "type": "function",
        "name": "GetCompanyFilingListing",
        "description": "Get company filing records based on published date. Use for regulatory analysis and company financial information.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "User's original query or request"
                },
                "keywords": {
                    "type": "string",
                    "description": "Search keywords for company filings"
                }
            },
            "required": ["user_query", "keywords"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "GetCompanyFilingDetails",
        "description": "Get company filing records based on Company ID. Use for detailed company regulatory and financial analysis.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "User's original query or request"
                },
                "keywords": {
                    "type": "string",
                    "description": "Company ID for filing details"
                }
            },
            "required": ["user_query", "keywords"],
            "additionalProperties": False
        }
    },
    
    # ===== INVESTIGATORS TOOLS =====
    {
        "type": "function",
        "name": "GetInvestigatorsDetails",
        "description": "Get investigator records based on published date. Essential for KOL identification and clinical trial planning.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "User's original query or request"
                },
                "keywords": {
                    "type": "string",
                    "description": "Search keywords for investigators"
                }
            },
            "required": ["user_query", "keywords"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "GetInvestigatorsDailyUpdates",
        "description": "Get daily updates for investigators data based on from date and to date. Use for recent investigator activities.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "User's original query or request"
                },
                "keywords": {
                    "type": "string",
                    "description": "Search keywords for investigators"
                }
            },
            "required": ["user_query", "keywords"],
            "additionalProperties": False
        }
    },
    
    # ===== NEWS TOOLS =====
    {
        "type": "function",
        "name": "GetNewsDetails",
        "description": "Get news data based on keyword search or NewsArticle ID. Use for market intelligence, recent developments, and industry trends.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "User's original query or request"
                },
                "keywords": {
                    "type": "string",
                    "description": "Search keywords for news or NewsArticle ID"
                }
            },
            "required": ["user_query", "keywords"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "GetNewsDailyUpdates",
        "description": "Get daily updates for news data based on from date and to date. Use for recent news and market developments.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "User's original query or request"
                },
                "keywords": {
                    "type": "string",
                    "description": "Search keywords for news"
                }
            },
            "required": ["user_query", "keywords"],
            "additionalProperties": False
        }
    },
    
    # ===== TRIAL SITES TOOLS =====
    {
        "type": "function",
        "name": "GetTrialSitesDetails",
        "description": "Get trial site data based on keyword search or Site ID. Essential for clinical development planning and site selection.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "User's original query or request"
                },
                "keywords": {
                    "type": "string",
                    "description": "Search keywords for trial sites or Site ID"
                }
            },
            "required": ["user_query", "keywords"],
            "additionalProperties": False
        }
    }
]

import os
import requests
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dotenv import load_dotenv
load_dotenv()
TOKEN_ID = os.getenv("GLOBALDATA_TOKEN_ID")
# Configuration
BASE_URL = "https://apidata.globaldata.com/GlobalDataTSRI"  # Replace with actual base URL
logger = logging.getLogger(__name__)

def fetch_from_globaldata(endpoint: str, params: dict = None) -> dict:
    """Make a GET request to GlobalData with TokenId in query params."""
    if params is None:
        params = {}
    params["TokenId"] = TOKEN_ID
    
    # Clean up None values
    params = {k: v for k, v in params.items() if v is not None}
    
    url = f"{BASE_URL}{endpoint}"
    
    try:
        logger.info(f"Calling GlobalData API: {url} with params: {params}")
        resp = requests.get(url, params=params, timeout=90)
        print(resp)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling GlobalData API: {e}")
        raise Exception(f"GlobalData API error: {str(e)}")

# ===== BIOMARKER FUNCTIONS =====

def GetBiomarkersDetails( user_query: str, keywords: str) -> dict:
    """Get biomarkers data based on from date and to date."""
    try:
        params = {}
        today = datetime.now()
        from_date = today - timedelta(days=30)
        params["fromdate"] = from_date.strftime("%d-%m-%Y")
        params["todate"] = today.strftime("%d-%m-%Y")
        
        data = fetch_from_globaldata("/api/Biomarker/GetBiomarkersDetails", params)
        
        return {
            "endpoint": "biomarker_details",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetBiomarkersDetails: {e}")
        raise Exception(str(e))

def GetBiomarkersDailyUpdates( user_query: str, keywords: str) -> dict:
    """Get biomarkers daily updates based on from date and to date."""
    try:
        params = {}
        today = datetime.now()
        from_date = today - timedelta(days=7)
        params["FromDate"] = from_date.strftime("%d-%m-%Y")
        params["ToDate"] = today.strftime("%d-%m-%Y")
        
        data = fetch_from_globaldata("/api/Biomarker/GetBiomarkersDailyUpdates", params)
        
        return {
            "endpoint": "biomarker_daily_updates",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetBiomarkersDailyUpdates: {e}")
        raise Exception(str(e))

# ===== CLINICAL TRIALS FUNCTIONS =====

def GetClinicalTrialsDetails( user_query: str, keywords: str) -> dict:
    """Get clinical trials data based on keyword search, Clinical ID, from date and to date."""
    try:
        params = {}
        if keywords:
            params["keyword"] = keywords
        
        today = datetime.now()
        from_date = today - timedelta(days=30)
        params["fromdate"] = from_date.strftime("%d-%m-%Y")
        params["todate"] = today.strftime("%d-%m-%Y")
        
        data = fetch_from_globaldata("/api/ClinicalTrials/GetClinicalTrialsDetails", params)
        
        return {
            "endpoint": "clinical_trials_details",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetClinicalTrialsDetails: {e}")
        raise Exception(str(e))

def GetClinicalTrialsLocationsandcontactDetails( user_query: str, keywords: str) -> dict:
    """Get clinical trials locations and contact details."""
    try:
        params = {}
        if keywords:
            params["keyword"] = keywords
        
        today = datetime.now()
        from_date = today - timedelta(days=30)
        params["fromdate"] = from_date.strftime("%d-%m-%Y")
        params["todate"] = today.strftime("%d-%m-%Y")
        
        data = fetch_from_globaldata("/api/ClinicalTrials/GetClinicalTrialsLocationsandcontactDetails", params)
        
        return {
            "endpoint": "clinical_trials_locations_contacts",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetClinicalTrialsLocationsandcontactDetails: {e}")
        raise Exception(str(e))

def GetClinicalTrialsDailyUpdates( user_query: str, keywords: str) -> dict:
    """Get clinical trials daily updates."""
    try:
        params = {}
        today = datetime.now()
        from_date = today - timedelta(days=7)
        params["FromDate"] = from_date.strftime("%d-%m-%Y")
        params["ToDate"] = today.strftime("%d-%m-%Y")
        
        data = fetch_from_globaldata("/api/ClinicalTrials/GetClinicalTrialsDailyUpdates", params)
        
        return {
            "endpoint": "clinical_trials_daily_updates",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetClinicalTrialsDailyUpdates: {e}")
        raise Exception(str(e))

# ===== COMPANY FUNCTIONS =====

def GetCompanyDetails( user_query: str, keywords: str) -> dict:
    """Get company details based on from date and to date."""
    try:
        params = {}
        today = datetime.now()
        from_date = today - timedelta(days=30)
        params["fromdate"] = from_date.strftime("%d-%m-%Y")
        params["todate"] = today.strftime("%d-%m-%Y")
        
        data = fetch_from_globaldata("/api/Company/GetCompanyDetails", params)
        
        return {
            "endpoint": "company_details",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetCompanyDetails: {e}")
        raise Exception(str(e))

# ===== DEALS FUNCTIONS =====

def GetDealsDetails( user_query: str, keywords: str) -> dict:
    """Get deals data based on keyword search or Deal ID."""
    try:
        params = {}
        if keywords:
            params["keyword"] = keywords
        
        data = fetch_from_globaldata("/api/Deals/GetDealsDetails", params)
        
        return {
            "endpoint": "deals_details",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetDealsDetails: {e}")
        raise Exception(str(e))

def GetDealsDailyUpdates( user_query: str, keywords: str) -> dict:
    """Get deals daily updates."""
    try:
        params = {}
        today = datetime.now()
        from_date = today - timedelta(days=7)
        params["fromdate"] = from_date.strftime("%d-%m-%Y")
        params["todate"] = today.strftime("%d-%m-%Y")
        
        data = fetch_from_globaldata("/api/Deals/GetDealsDailyUpdates", params)
        
        return {
            "endpoint": "deals_daily_updates",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetDealsDailyUpdates: {e}")
        raise Exception(str(e))

# ===== DRUGS FUNCTIONS =====

def GetPipelineDrugDetails( user_query: str, keywords: str) -> dict:
    """Get pipeline drugs data based on keyword search or Drug ID."""
    try:
        params = {}
        if keywords:
            params["keyword"] = keywords
        
        data = fetch_from_globaldata("/api/Drugs/GetPipelineDrugDetails", params)
        
        return {
            "endpoint": "drugs_pipeline",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetPipelineDrugDetails: {e}")
        raise Exception(str(e))

def GetMarketedDrugDetails( user_query: str, keywords: str) -> dict:
    """Get marketed drugs data based on keyword search or Drug ID."""
    try:
        params = {}
        if keywords:
            params["keyword"] = keywords
        
        data = fetch_from_globaldata("/api/Drugs/GetMarketedDrugDetails", params)
        
        return {
            "endpoint": "drugs_marketed",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetMarketedDrugDetails: {e}")
        raise Exception(str(e))

def GetStubDrugs( user_query: str, keywords: str) -> dict:
    """Get stub drugs data."""
    try:
        params = {}
        today = datetime.now()
        from_date = today - timedelta(days=30)
        params["fromdate"] = from_date.strftime("%d-%m-%Y")
        params["todate"] = today.strftime("%d-%m-%Y")
        
        data = fetch_from_globaldata("/api/Drugs/GetStubDrugs", params)
        
        return {
            "endpoint": "drugs_stub",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetStubDrugs: {e}")
        raise Exception(str(e))

def GetDrugsDailyUpdates( user_query: str, keywords: str) -> dict:
    """Get Drugs daily updates."""
    try:
        params = {}
        today = datetime.now()
        from_date = today - timedelta(days=7)
        params["fromdate"] = from_date.strftime("%d-%m-%Y")
        params["todate"] = today.strftime("%d-%m-%Y")
        
        data = fetch_from_globaldata("/api/Drugs/GetDrugsDailyUpdates", params)
        
        return {
            "endpoint": "news_daily_updates",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetDrugsDailyUpdates: {e}")
        raise Exception(str(e))
    
# ===== FILINGS FUNCTIONS =====

def GetCompanyFilingListing( user_query: str, keywords: str) -> dict:
    """Get company filing records based on published date."""
    try:
        params = {}
        today = datetime.now()
        params["publishedDate"] = today.strftime("%d-%m-%Y")
        
        data = fetch_from_globaldata("/api/Filings/GetCompanyFilingListing", params)
        
        return {
            "endpoint": "filings_company_listing",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetCompanyFilingListing: {e}")
        raise Exception(str(e))

# ===== INVESTIGATORS FUNCTIONS =====

def GetInvestigatorsDetails( user_query: str, keywords: str) -> dict:
    """Get investigators records based on published date."""
    try:
        params = {}
        today = datetime.now()
        params["publishedDate"] = today.strftime("%d-%m-%Y")
        
        data = fetch_from_globaldata("/api/Investigators/GetInvestigatorsDetails", params)
        
        return {
            "endpoint": "investigators_details",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetInvestigatorsDetails: {e}")
        raise Exception(str(e))

def GetInvestigatorsDailyUpdates( user_query: str, keywords: str) -> dict:
    """Get investigators daily updates based on from date and to date."""
    try:
        params = {}
        today = datetime.now()
        from_date = today - timedelta(days=7)
        params["fromdate"] = from_date.strftime("%d-%m-%Y")
        params["todate"] = today.strftime("%d-%m-%Y")
        
        data = fetch_from_globaldata("/api/Investigators/GetInvestigatorsDailyUpdates", params)
        
        return {
            "endpoint": "investigators_daily_updates",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetInvestigatorsDailyUpdates: {e}")
        raise Exception(str(e))
    
# ===== LOA FUNCTIONS =====

def GetLOADetails( user_query: str, keywords: str) -> dict:
    """Get LOA details based on DrugName and DrugID."""
    try:
        params = {}
        if keywords:
            params["DrugName"] = keywords
        
        data = fetch_from_globaldata("/api/LOA/GetLOADetails", params)
        
        return {
            "endpoint": "loa_details",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetLOADetails: {e}")
        raise Exception(str(e))

# ===== NEWS FUNCTIONS =====

def GetNewsDetails( user_query: str, keywords: str) -> dict:
    """Get news data based on keyword search or NewsArticle ID."""
    try:
        params = {}
        if keywords:
            params["keyword"] = keywords
        
        data = fetch_from_globaldata("/api/News/GetNewsDetails", params)
        
        return {
            "endpoint": "news_details",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetNewsDetails: {e}")
        raise Exception(str(e))

def GetNewsDailyUpdates( user_query: str, keywords: str) -> dict:
    """Get news daily updates."""
    try:
        params = {}
        today = datetime.now()
        from_date = today - timedelta(days=7)
        params["fromdate"] = from_date.strftime("%d-%m-%Y")
        params["todate"] = today.strftime("%d-%m-%Y")
        
        data = fetch_from_globaldata("/api/News/GetNewsDailyUpdates", params)
        
        return {
            "endpoint": "news_daily_updates",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetNewsDailyUpdates: {e}")
        raise Exception(str(e))

# ===== NPV FUNCTIONS =====

def GetNPVDetails( user_query: str, keywords: str) -> dict:
    """Get NPV data based on DrugName or DrugID."""
    try:
        params = {}
        if keywords:
            params["DrugName"] = keywords
        
        data = fetch_from_globaldata("/api/NPV/GetNPVDetails", params)
        
        return {
            "endpoint": "npv_details",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetNPVDetails: {e}")
        raise Exception(str(e))

# ===== PATENTS FUNCTIONS =====

def GetPatentsListing( user_query: str, keywords: str) -> dict:
    """Get patent records based on PublishedDate."""
    try:
        params = {}
        today = datetime.now()
        params["PublishedDate"] = today.strftime("%d-%m-%Y")
        
        data = fetch_from_globaldata("/api/Patents/GetPatentsListing", params)
        
        return {
            "endpoint": "patents_listing",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetPatentsListing: {e}")
        raise Exception(str(e))

# ===== RMT FUNCTIONS =====

def GetRMTDetails( user_query: str, keywords: str) -> dict:
    """Get RMT data based on keyword search or Drug ID."""
    try:
        params = {}
        if keywords:
            params["keyword"] = keywords
        
        data = fetch_from_globaldata("/api/RMT/GetRMTDetails", params)
        
        return {
            "endpoint": "rmt_details",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetRMTDetails: {e}")
        raise Exception(str(e))

def GetRMTDailyUpdates( user_query: str, keywords: str) -> dict:
    """Get RMT daily updates based on from date and to date."""
    try:
        params = {}
        today = datetime.now()
        from_date = today - timedelta(days=7)
        params["FromDate"] = from_date.strftime("%d-%m-%Y")
        params["ToDate"] = today.strftime("%d-%m-%Y")
        
        data = fetch_from_globaldata("/api/RMT/GetRMTDailyUpdates", params)
        
        return {
            "endpoint": "rmt_daily_updates",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetRMTDailyUpdates: {e}")
        raise Exception(str(e))
    
# ===== SITES FUNCTIONS =====

def GetTrialSitesDetails( user_query: str, keywords: str) -> dict:
    """Get trial sites data based on keyword search or Site ID."""
    try:
        params = {}
        if keywords:
            params["keyword"] = keywords
        
        data = fetch_from_globaldata("/api/Sites/GetTrialSitesDetails", params)
        
        return {
            "endpoint": "sites_trial_sites",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetTrialSitesDetails: {e}")
        raise Exception(str(e))

def GetSiteCoordinatorDetails( user_query: str, keywords: str) -> dict:
    """Get site coordinator details based on SiteCoordinatorName or SiteCoordinatorId."""
    try:
        params = {}
        if keywords:
            params["SiteCoordinatorName"] = keywords
        
        data = fetch_from_globaldata("/api/Sites/GetSiteCoordinatorDetails", params)
        
        return {
            "endpoint": "sites_coordinator_details",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetSiteCoordinatorDetails: {e}")
        raise Exception(str(e))

def GetTrialSiteDailyUpdates( user_query: str, keywords: str) -> dict:
    """Get trial site daily updates based on from date and to date."""
    try:
        params = {}
        today = datetime.now()
        from_date = today - timedelta(days=7)
        params["FromDate"] = from_date.strftime("%d-%m-%Y")
        params["ToDate"] = today.strftime("%d-%m-%Y")
        
        data = fetch_from_globaldata("/api/Sites/GetTrialSiteDailyUpdates", params)
        
        return {
            "endpoint": "sites_daily_updates",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetTrialSiteDailyUpdates: {e}")
        raise Exception(str(e))

# Epidemiology
def GetEpidemiologyDetails( user_query: str, Indication: str) -> dict:
    """Get epidemiology data based on keyword search or IndicationID."""
    try:
        params = {}
        params["Indication"] = Indication
        data = fetch_from_globaldata("/api/Epidemiology/GetEpidemiologyDetails", params)
        # Return a valid JSON-RPC response
        return {
            "endpoint": "sites_daily_updates",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error in get_epidemiology_details: {e}")
        return {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {
                "code": -32000,
                "message": str(e)
            }
        }
# Poli Drugs
def GetPoliDrugs( user_query: str, keywords: str) -> dict:
    """Get Poli drugs data based on keyword search or DrugID."""
    try:
        params = {}
        if keywords:
            params["keyword"] = keywords
        
        data = fetch_from_globaldata("/api/Poli/GetPoliDrugs", params)
        
        return {
            "endpoint": "poli_drugs",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetPoliDrugs: {e}")
        raise Exception(str(e))     

def GetPoliTherapyDetails( user_query: str, keywords: str) -> dict:
    """Get Poli therapy details based on TherapyAreaID."""
    try:
        params = {}
        if keywords:
            params["TherapyViewID"] = keywords
        
        data = fetch_from_globaldata("/api/Poli/GetPoliTherapyDetails", params)
        
        return {
            "endpoint": "poli_therapy_details",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetPoliTherapyDetails: {e}")
        raise Exception(str(e)) 

def GetHTAAssesmentDetails( user_query: str, keywords: str) -> dict:
    """Get HTA Assessment details based on TherapyAreaID."""
    try:
        params = {}      
        data = fetch_from_globaldata("/api/Poli/GetHTAAssesmentDetails", params)
        
        return {
            "endpoint": "hta_assessment_details",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetHTAAssesmentDetails: {e}")
        raise Exception(str(e))
    
def GetIRPDetails( user_query: str, keywords: str) -> dict:
    """Get IRP details based on TherapyAreaID."""
    try:
        params = {}
        if keywords:
            # Garaphy mean Country Name like Australia, Canada, etc.
            params["Geography"] = keywords 
        
        data = fetch_from_globaldata("/api/Poli/GetIRPDetails", params)
        
        return {
            "endpoint": "irp_details",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetIRPDetails: {e}")
        raise Exception(str(e)) 

def GetDrugs( user_query: str, keywords: str) -> dict:
    """Get Drugs data based on keyword search or DrugID."""
    try:
        params = {}    
        data = fetch_from_globaldata("/api/Poli/GetDrugs", params)
        
        return {
            "endpoint": "poli_drugs",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetDrugs: {e}")
        raise Exception(str(e)) 

def GetTherapyAreas( user_query: str, keywords: str) -> dict:
    """Get Therapy Areas data."""
    try:
        params = {}
        data = fetch_from_globaldata("/api/Poli/GetTherapyAreas", params)
        
        return {
            "endpoint": "poli_therapy_areas",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetTherapyAreas: {e}")
        raise Exception(str(e)) 

def GetTherapyLines( user_query: str, keywords: str) -> dict:
    """Get Therapy Lines data based on TherapyAreaID."""
    try:
        params = {}        
        data = fetch_from_globaldata("/api/Poli/GetTherapyLines", params)
        
        return {
            "endpoint": "poli_therapy_lines",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetTherapyLines: {e}")
        raise Exception(str(e)) 

def GetTherapyTypes( user_query: str, keywords: str) -> dict:
    """Get Therapy Types data based on TherapyAreaID."""
    try:
        params = {}
        data = fetch_from_globaldata("/api/Poli/GetTherapyTypes", params)
        
        return {
            "endpoint": "poli_therapy_types",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetTherapyTypes: {e}")
        raise Exception(str(e))
def GetDiseaseStage( user_query: str, keywords: str) -> dict:
    """Get Disease Stage data based on TherapyAreaID."""
    try:
        params = {}
        data = fetch_from_globaldata("/api/Poli/GetDiseaseStage", params)
        
        return {
            "endpoint": "poli_disease_stage",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetDiseaseStage: {e}")
        raise Exception(str(e))

def GetForexCurrencies( user_query: str, keywords: str) -> dict:
    """Get Forex Currencies data."""
    try:
        params = {}
        data = fetch_from_globaldata("/api/Poli/GetForexCurrencies", params)
        
        return {
            "endpoint": "forex_currencies",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetForexCurrencies: {e}")
        raise Exception(str(e)) 

def GetCurrencyConverter( user_query: str, keywords: str) -> dict:
    """Get Currency Converter data."""
    try:
        params = {}
        if keywords:
            params["Currency"] = keywords
        data = fetch_from_globaldata("/api/Poli/GetCurrencyConverter", params)
        
        return {
            "endpoint": "currency_converter",
            "params_used": params,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in GetCurrencyConverter: {e}")
        raise Exception(str(e))

# ===== FUNCTION MAPPING =====
FUNCTION_MAPPING = {
    'GetBiomarkersDetails': GetBiomarkersDetails,
    'GetBiomarkersDailyUpdates': GetBiomarkersDailyUpdates,
    'GetClinicalTrialsDetails': GetClinicalTrialsDetails,
    'GetClinicalTrialsLocationsandcontactDetails': GetClinicalTrialsLocationsandcontactDetails,
    'GetClinicalTrialsDailyUpdates': GetClinicalTrialsDailyUpdates,
    'GetCompanyDetails': GetCompanyDetails,
    'GetDealsDetails': GetDealsDetails,
    'GetDealsDailyUpdates': GetDealsDailyUpdates,
    'GetPipelineDrugDetails': GetPipelineDrugDetails,
    'GetMarketedDrugDetails': GetMarketedDrugDetails,
    'GetStubDrugs': GetStubDrugs,
    'GetCompanyFilingListing': GetCompanyFilingListing,
    'GetInvestigatorsDetails': GetInvestigatorsDetails,
    'GetLOADetails': GetLOADetails,
    'GetNewsDetails': GetNewsDetails,
    'GetNewsDailyUpdates': GetNewsDailyUpdates,
    'GetNPVDetails': GetNPVDetails,
    'GetPatentsListing': GetPatentsListing,
    'GetRMTDetails': GetRMTDetails,
    'GetTrialSitesDetails': GetTrialSitesDetails,
    'GetSiteCoordinatorDetails': GetSiteCoordinatorDetails,
    'GetTrialSiteDailyUpdates': GetTrialSiteDailyUpdates,
    'GetDrugsDailyUpdates': GetDrugsDailyUpdates,
    'GetRMTDailyUpdates': GetRMTDailyUpdates,
    'GetInvestigatorsDailyUpdates': GetInvestigatorsDailyUpdates,
    'GetEpidemiologyDetails': GetEpidemiologyDetails,
    'GetPoliDrugs': GetPoliDrugs,
    'GetPoliTherapyDetails': GetPoliTherapyDetails,
    'GetHTAAssesmentDetails': GetHTAAssesmentDetails,
    'GetIRPDetails': GetIRPDetails,
    'GetDrugs': GetDrugs,
    'GetTherapyAreas': GetTherapyAreas,
    'GetTherapyLines': GetTherapyLines,
    'GetTherapyTypes': GetTherapyTypes,
    'GetDiseaseStage': GetDiseaseStage,
    'GetForexCurrencies': GetForexCurrencies,
    'GetCurrencyConverter': GetCurrencyConverter
}

prompt = """
You are an expert pharmaceutical data analyst with access to comprehensive GlobalData APIs and internal file search capabilities. Your role is to conduct research for each given task and provide accurate, actionable insights by intelligently selecting and utilizing the appropriate tools based on user queries.

## Core Responsibilities
- Execute assigned research tasks using optimal tool selection
- Synthesize and validate findings across multiple data sources
- Present actionable insights with clear evidence and implications
- Maintain context from original query while addressing specific sub-tasks

## Core Capabilities

### Tool Selection Intelligence
Automatically identify and select the most appropriate tool based on query intent and keywords:

**Biomarker Research**
- GetBiomarkersDetails - For biomarker research, diagnostic, or therapeutic applications
- GetBiomarkersDailyUpdates - For recent biomarker developments

**Clinical Trials**
- GetClinicalTrialsDetails - For pipeline analysis, competitive landscape, development timelines
- GetClinicalTrialsLocationsandcontactDetails - For trial locations and contact information
- GetClinicalTrialsDailyUpdates - For latest trial status changes and activities

**Company Intelligence**
- GetCompanyDetails - For company profiling, partnership analysis, competitive landscape
- GetDailyDeletedCompanies - For companies removed from database

**Deals & Partnerships**
- GetDealsDetails - For deals, market activity, partnership trends
- GetDealsDailyUpdates - For recent deal activity and market movements
- GetDailyDeletedDeals - For recently deleted deals

**Drug Information**
- GetPipelineDrugDetails - For pipeline drugs, competitive landscape, pipeline analysis
- GetMarketedDrugDetails - For marketed drugs, market analysis, competitive benchmarking
- GetDrugsDailyUpdates - For recent drug developments
- GetHistoryofEvents - For drug timeline and development milestones (requires Drug ID)
- GetStubDrugs - For incomplete drug records

**Drug Sales & Commercial Performance**
- GetDrugSalesDetails - For drug sales, revenue, commercial performance analysis
- GetDrugSalesDailyUpdates - For recent sales performance updates

**Epidemiology & Market Sizing**
- GetEpidemiologyDetails - For patient populations, disease prevalence, market sizing (requires Indication keyword)

**Regulatory & Financial Filings**
- GetCompanyFilingListing - For company filings and regulatory analysis
- GetCompanyFilingDetails - For specific filing details (requires Company ID)

**Key Opinion Leaders**
- GetInvestigatorsDetails - For investigator records, KOL identification, clinical trial planning
- GetInvestigatorsDailyUpdates - For recent investigator activities

**News & Market Intelligence**
- GetNewsDetails - For news data, market intelligence, industry trends
- GetNewsDailyUpdates - For daily news and market developments

**Trial Sites**
- GetTrialSitesDetails - For trial site data, clinical development planning, site selection

**Internal File Search**
- file_search - For unstructured data, ad-hoc analyses, or detailed information beyond API capabilities

### Parameter Intelligence

**Keywords Parameter**
- Direct Usage: Extract specific terms directly from queries (e.g., "clinical trials for diabetes" → "diabetes")
- Contextual Inference: Infer relevant keywords from implied subjects (e.g., "recent cancer research updates" → "cancer research")
- ID Recognition: Use provided IDs as keywords (e.g., "Clinical ID NCT01234567" → "NCT01234567")

**Date Parameters**
- Automatic Range for Daily Updates: Set from_date to one week prior to current date (July 2, 2025) and to_date to current date (July 9, 2025)
- User-Specified Dates: Honor explicitly provided date ranges in clear, unambiguous format
- Context-Aware Dating: Interpret relative dates (e.g., "last quarter," "this year") appropriately

**User Query Preservation**
Always pass the complete original query as user_query parameter to maintain full context and intent.

## Research Methodology

### Multi-Tool Integration
- Primary Tool Selection: Choose the most relevant tool based on core query intent
- Supplementary Tools: Utilize additional tools for comprehensive analysis when beneficial
- Cross-Reference: Validate findings across multiple data sources when appropriate

### Data Synthesis
- Comprehensive Analysis: Combine data from multiple tools to provide holistic insights
- Trend Identification: Identify patterns and trends across different data sources
- Contextual Interpretation: Provide meaningful context and implications for findings

### Quality Assurance
- Data Validation: Cross-check information across multiple sources
- Completeness Check: Ensure all relevant aspects of the query are addressed
- Accuracy Verification: Validate data consistency and reliability

## Response Framework

### Structure
- Executive Summary: Brief overview of key findings
- Detailed Analysis: Comprehensive breakdown of research results
- Data Sources: Clear indication of tools and data sources used
- Implications: Business or strategic implications of findings
- Recommendations: Actionable insights based on analysis

### Output Format Requirements
- **Natural Language Summaries**: For all API data (JSON format) and Excel data, create comprehensive natural language summaries that translate structured data into readable, actionable insights
- **Data Interpretation**: Transform raw data points into meaningful narratives that highlight key trends, patterns, and implications
- **Contextual Analysis**: Provide context around numerical data, explaining significance and relevance to the original query
- **Structured Presentation**: Organize findings in clear, logical sections with appropriate headings and bullet points where beneficial


## Example Query Handling

**Query**: "What are the recent clinical trial developments for Alzheimer's disease?"
- Tool: GetClinicalTrialsDailyUpdates
- Keywords: "Alzheimer's disease"
- Date Range: Automatic (July 2-9, 2025)

**Query**: "Show me details for drug ID 54321"
- Tool: GetPipelineDrugDetails or GetMarketedDrugDetails
- Keywords: "54321"

**Query**: "Pfizer's recent company filings and partnership activity"
- Primary Tool: GetCompanyFilingListing
- Secondary Tool: GetDealsDetails
- Keywords: "Pfizer"

## Operational Excellence

### Proactive Analysis
- Anticipate follow-up questions and provide comprehensive initial responses
- Identify related areas of interest that might be valuable to explore
- Suggest additional research directions based on findings

### Continuous Learning
- Adapt tool selection based on query patterns and effectiveness
- Refine parameter optimization for better results

### User-Centric Approach
- Tailor responses to user's apparent expertise level and needs
- Provide appropriate level of detail and technical depth
- Offer clarification and additional information when beneficial

## Instructions
Process user queries by analyzing intent, selecting appropriate tools, setting optimal parameters, conducting thorough research, and providing comprehensive, actionable insights. Always maintain the highest standards of accuracy and professionalism in pharmaceutical data analysis.

"""

class DataPreservationManager:
    """
    Manages preservation of complete API data while providing truncated versions for token management
    """
    
    def __init__(self, storage_path: str = "preserved_data"):
        self.storage_path = storage_path
        self.ensure_storage_directory()
        self.session_data = {}  # In-memory storage for current session
    
    def ensure_storage_directory(self):
        """Create storage directory if it doesn't exist"""
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)
    
    def generate_data_id(self, function_name: str, function_args: dict) -> str:
        """Generate unique ID for data based on function and arguments"""
        content = f"{function_name}_{json.dumps(function_args, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def preserve_original_data(self, data_id: str, function_name: str, original_data: Any) -> Dict[str, Any]:
        """
        Preserve complete original data and return preservation metadata
        """
        preservation_info = {
            "data_id": data_id,
            "function_name": function_name,
            "timestamp": datetime.now().isoformat(),
            "original_size_bytes": sys.getsizeof(json.dumps(original_data, default=str)),
            "record_count": 0,
            "preservation_method": "in_memory_and_disk"
        }
        
        # Count records if it's API response format
        if isinstance(original_data, dict) and 'data' in original_data:
            api_data = original_data['data']
            if isinstance(api_data, dict) and 'data' in api_data:
                records = api_data['data']
                if isinstance(records, list):
                    preservation_info["record_count"] = len(records)
        
        # Store in session memory
        self.session_data[data_id] = {
            "original_data": original_data,
            "preservation_info": preservation_info
        }
        
        # Also save to disk for persistence
        try:
            file_path = os.path.join(self.storage_path, f"{data_id}.pkl")
            with open(file_path, 'wb') as f:
                pickle.dump({
                    "original_data": original_data,
                    "preservation_info": preservation_info
                }, f)
        except Exception as e:
            print(f"Warning: Could not save data to disk: {e}")
            preservation_info["preservation_method"] = "in_memory_only"
        
        return preservation_info
    
    def get_original_data(self, data_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve original data by ID"""
        # Try session memory first
        if data_id in self.session_data:
            return self.session_data[data_id]
        
        # Try disk storage
        try:
            file_path = os.path.join(self.storage_path, f"{data_id}.pkl")
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            print(f"Error loading data from disk: {e}")
        
        return None
    
    def get_all_preserved_data_ids(self) -> List[str]:
        """Get all preserved data IDs from current session"""
        return list(self.session_data.keys())

def smart_truncate_with_preservation(data: Any, max_records: int = 50, max_string_length: int = 500, 
                                   preservation_info: Dict = None) -> Dict[str, Any]:
    """
    Smart truncation that preserves data structure and includes preservation metadata
    """
    truncation_info = {
        "was_truncated": False,
        "original_record_count": 0,
        "truncated_record_count": 0,
        "truncation_details": [],
        "preservation_available": preservation_info is not None
    }
    
    # Add preservation info if available
    if preservation_info:
        truncation_info["preservation_info"] = preservation_info
    
    if isinstance(data, dict):
        if 'data' in data and isinstance(data['data'], dict) and 'data' in data['data']:
            # Handle nested API response structure
            records = data['data']['data']
            if isinstance(records, list):
                truncation_info["original_record_count"] = len(records)
                
                if len(records) > max_records:
                    # Intelligent truncation - preserve first, middle, and last records
                    truncated_records = []
                    
                    # Take first portion
                    first_portion = records[:max_records//2]
                    truncated_records.extend(first_portion)
                    
                    # Add separator record to indicate truncation
                    truncated_records.append({
                        "_truncation_marker": True,
                        "_message": f"... {len(records) - max_records} records truncated ...",
                        "_original_count": len(records),
                        "_preserved_data_id": preservation_info["data_id"] if preservation_info else None
                    })
                    
                    # Take last portion
                    last_portion = records[-(max_records//2):]
                    truncated_records.extend(last_portion)
                    
                    truncation_info["was_truncated"] = True
                    truncation_info["truncated_record_count"] = len(truncated_records) - 1  # Exclude marker
                    truncation_info["truncation_details"].append(
                        f"Records truncated from {len(records)} to {max_records} "
                        f"(showing first {max_records//2} and last {max_records//2})"
                    )
                    
                    # Update the data structure
                    data_copy = json.loads(json.dumps(data, default=str))
                    data_copy['data']['data'] = truncated_records
                    
                    # Add truncation info to the data
                    data_copy['_truncation_info'] = truncation_info
                    
                    return data_copy
                else:
                    truncation_info["truncated_record_count"] = len(records)
    
    # Truncate long strings in the data
    data_copy = json.loads(json.dumps(data, default=str))
    data_copy = _truncate_strings_recursive(data_copy, max_string_length, truncation_info)
    
    if truncation_info["was_truncated"] or truncation_info["truncation_details"]:
        data_copy['_truncation_info'] = truncation_info
    
    return data_copy

def _truncate_strings_recursive(obj: Any, max_length: int, truncation_info: Dict) -> Any:
    """Recursively truncate long strings in nested data structures"""
    if isinstance(obj, dict):
        return {k: _truncate_strings_recursive(v, max_length, truncation_info) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_truncate_strings_recursive(item, max_length, truncation_info) for item in obj]
    elif isinstance(obj, str) and len(obj) > max_length:
        truncation_info["was_truncated"] = True
        truncation_info["truncation_details"].append(f"String truncated from {len(obj)} to {max_length} characters")
        return obj[:max_length] + "... [TRUNCATED - Original preserved]"
    else:
        return obj

def prepare_data_for_context_with_preservation(data: Any, preservation_info: Dict, 
                                             max_tokens: int = 8000) -> Dict[str, Any]:
    """
    Prepare data for context while preserving original and providing preservation metadata
    """
    # Start with smart truncation that includes preservation info
    truncated_data = smart_truncate_with_preservation(
        data, max_records=50, max_string_length=500, preservation_info=preservation_info
    )
    
    # Estimate token count
    data_str = json.dumps(truncated_data, default=str)
    estimated_tokens = estimate_token_count(data_str)
    
    # Progressive truncation with preservation awareness
    if estimated_tokens > max_tokens:
        truncated_data = smart_truncate_with_preservation(
            data, max_records=20, max_string_length=200, preservation_info=preservation_info
        )
        data_str = json.dumps(truncated_data, default=str)
        estimated_tokens = estimate_token_count(data_str)
        
        if estimated_tokens > max_tokens:
            truncated_data = smart_truncate_with_preservation(
                data, max_records=10, max_string_length=100, preservation_info=preservation_info
            )
            data_str = json.dumps(truncated_data, default=str)
            estimated_tokens = estimate_token_count(data_str)
            
            # Last resort: create enhanced summary with preservation info
            if estimated_tokens > max_tokens:
                truncated_data = create_enhanced_summary_with_preservation(data, preservation_info)
    
    return truncated_data

def create_enhanced_summary_with_preservation(data: Any, preservation_info: Dict) -> Dict[str, Any]:
    """Create enhanced summary that includes preservation information"""
    summary = {
        "data_summary": True,
        "original_data_type": type(data).__name__,
        "summary_reason": "Data too large for context - enhanced summary with preservation info",
        "preservation_info": preservation_info,
        "data_access_note": f"Complete original data preserved with ID: {preservation_info['data_id']}"
    }
    
    if isinstance(data, dict):
        if 'data' in data and isinstance(data['data'], dict) and 'data' in data['data']:
            records = data['data']['data']
            if isinstance(records, list):
                summary.update({
                    "total_records": len(records),
                    "sample_fields": list(records[0].keys()) if records else [],
                    "first_record_sample": records[0] if records else None,
                    "last_record_sample": records[-1] if len(records) > 1 else None,
                    "data_structure": "API response with nested data array"
                })
                
                # Add statistical summary if numeric fields detected
                if records:
                    numeric_fields = []
                    for field, value in records[0].items():
                        if isinstance(value, (int, float)):
                            numeric_fields.append(field)
                    summary["numeric_fields"] = numeric_fields
            else:
                summary.update({
                    "data_structure": "API response with non-array data",
                    "data_type": type(records).__name__
                })
        else:
            summary.update({
                "top_level_keys": list(data.keys()),
                "data_structure": "Dictionary without standard API structure"
            })
    else:
        summary.update({
            "data_structure": "Non-dictionary data",
            "data_preview": str(data)[:200] + "..." if len(str(data)) > 200 else str(data)
        })
    
    return summary

def estimate_token_count(text: str) -> int:
    """Rough estimation of token count (approximately 4 characters per token)"""
    return len(text) // 4

def research_assistant(user_message: str, task: str, conversation_history: Optional[List] = None, 
                              vector_id: Optional[str] = None):
    """
    Enhanced research assistant with complete data preservation capabilities
    """
    if conversation_history is None:
        conversation_history = []
    
    # Initialize data preservation manager
    preservation_manager = DataPreservationManager()
    
    # Add the user's new message to the conversation
    conversation_history.append({"role": "user", "content": user_message})
    
    # Prepare tools array (assuming these are defined elsewhere)
    tools_to_use = []
    tools_to_use.extend(globaldata_tools)  # Your existing tools
    
    if vector_id:
        file_search_tool = {
            "type": "file_search",
            "vector_store_ids": [vector_id],
            "max_num_results": 10
        }
        tools_to_use.append(file_search_tool)
    
    try:
        # Get initial response
        response = client.responses.create(
            model="gpt-4o",
            instructions=prompt,
            input=conversation_history,
            tools=tools_to_use,
            parallel_tool_calls=True,
            include=["file_search_call.results"],
        )
                
        # Process tool calls with preservation
        if response.output and isinstance(response.output, list):
            tool_calls = [item for item in response.output if hasattr(item, 'type') and item.type in ['function_call', 'file_search_call']]
            
            if tool_calls:
                preserved_data_map = {}
                ai_summaries = {}
                
                # Add tool calls to conversation history
                for tool_call in tool_calls:
                    conversation_history.append(tool_call)
                
                # Execute tool calls with preservation
                for tool_call in tool_calls:
                    try:
                        if tool_call.type == 'function_call':
                            function_name = tool_call.name
                            function_args = json.loads(tool_call.arguments)
                            print(f"Calling Tool: {function_name}")
                            # Execute the function
                            original_result = FUNCTION_MAPPING[function_name](**function_args)
                            
                            # Generate unique ID for this data
                            data_id = preservation_manager.generate_data_id(function_name, function_args)
                            
                            # Preserve original data
                            preservation_info = preservation_manager.preserve_original_data(
                                data_id, function_name, original_result
                            )
                                                        
                            # Prepare truncated data for context
                            truncated_result = prepare_data_for_context_with_preservation(
                                original_result, preservation_info
                            )
                            
                            
                            # Store preservation mapping
                            preserved_data_map[function_name] = {
                                "data_id": data_id,
                                "original_data": original_result,
                                "preservation_info": preservation_info
                            }
                            
                            # Add truncated result to conversation
                            conversation_history.append({
                                "type": "function_call_output",
                                "call_id": tool_call.call_id,
                                "output": json.dumps(truncated_result, default=str)
                            })
                            
                            # Generate AI summary using original data
                            ai_summary = generate_summary(function_name, original_result, preservation_info, user_message, task)
                            ai_summaries[function_name] = ai_summary
                            
                        elif tool_call.type == 'file_search_call':
                            # Handle file search calls
                            function_name = f"file_search_{tool_call.id}"
                            print(f"Calling Tool: {function_name}")
                            search_results = {
                                "tool_call_id": tool_call.id,
                                "type": "file_search",
                                "status": tool_call.status,
                                "queries": tool_call.queries,
                                "results": tool_call.results
                            }
                            
                            # Preserve file search results too
                            data_id = preservation_manager.generate_data_id(function_name, {"query": str(tool_call.queries)})
                            preservation_info = preservation_manager.preserve_original_data(
                                data_id, function_name, search_results
                            )
                            
                            preserved_data_map[function_name] = {
                                "data_id": data_id,
                                "original_data": search_results,
                                "preservation_info": preservation_info
                            }

                            formatted_data = extract_and_format_data(tool_call.results)
                            print(formatted_data)
                            ai_summary = generate_summary(function_name, formatted_data, preservation_info, user_message, task)
                            ai_summaries[function_name] = ai_summary
                    
                    except Exception as e:
                        print(f"Error executing tool call: {e}")
                        if tool_call.type == 'function_call':
                            conversation_history.append({
                                "type": "function_call_output",
                                "call_id": tool_call.call_id,
                                "output": json.dumps({"error": str(e)})
                            })
                
                # Enhanced final response with preservation awareness
                enhanced_instructions = """
                You are a pharmaceutical data analyst with access to complete preserved data. 
                Synthesize the tool results into a comprehensive response. 
                
                Important notes:
                - All original data has been completely preserved and can be accessed if needed
                - Some data in the context may be truncated for token management
                - When you see truncation markers or preservation IDs, acknowledge that complete data is available
                - Provide analysis based on available data but mention data preservation capabilities
                
                Always mention if data was truncated and that complete analysis can be performed on the preserved data.
                """
                
                try:
                    final_response = client.responses.create(
                        model="gpt-4o",
                        instructions=enhanced_instructions,
                        input=conversation_history,
                        tools=tools_to_use,
                    )
                except Exception as e:
                    if "maximum context length" in str(e).lower() or "token" in str(e).lower():
                        print(f"Token limit exceeded, using reduced context: {e}")
                        reduced_history = conversation_history[-10:]
                        final_response = client.responses.create(
                            model="gpt-4o",
                            instructions=enhanced_instructions,
                            input=reduced_history,
                            tools=tools_to_use,
                        )
                    else:
                        raise e
                
                # Enhanced results display
                display_enhanced_results_summary(preserved_data_map, ai_summaries, user_message, preservation_manager)
                
                return final_response.output_text, conversation_history, preserved_data_map
            
            else:
                return response.output_text, conversation_history, {}
        
        else:
            return "No response output received", conversation_history, {}
            
    except Exception as e:
        print(f"Error in enhanced research assistant: {e}")
        return f"Error: {str(e)}", conversation_history, {}

def display_enhanced_results_summary(preserved_data_map: Dict, ai_summaries: Dict, 
                                   original_query: str, preservation_manager: DataPreservationManager):
    """Display enhanced results summary with preservation information"""
    print("\n" + "="*80)
    print("ENHANCED DATA PRESERVATION SUMMARY")
    print(f"Tools Used: {len(preserved_data_map)}")
    
    for i, (function_name, preservation_data) in enumerate(preserved_data_map.items(), 1):
        print(f"\n--- Tool {i}: {function_name} ---")
        
        preservation_info = preservation_data["preservation_info"]
                
        # Show AI summary
        ai_summary = ai_summaries.get(function_name, "Summary not available")
        print(f"Research Summary: {ai_summary}")
        
        print("-" * 60)
    
    print(f"Preserved Data IDs: {preservation_manager.get_all_preserved_data_ids()}")
    print("="*80)

def generate_summary(function_name: str, original_data: Any, preservation_info: Dict, user_message: str, task:str) -> str:
    """Generate enhanced AI summary with preservation awareness"""
    try:
        if isinstance(original_data, str):
            analysis_prompt = f"""
            This JSON data represents research data obtained either from the GlobalData API or from a local file, depending on the source specified as '{function_name}'. The research has been conducted to address the user-defined task, which includes a main query and may also include one or more subqueries.

            Your objective is to analyze the research data provided below and generate a comprehensive summary that answers the main query and its subqueries, using only the information present in this research data.


            User Task (Query/Subqueries):
            {task}

            Research Data Snapshot:
            {original_data}
            
            Instructions:
            - Use only the provided research data to answer the query/subqueries.
            - Clearly structure the response so it covers each query and subquery aspect.
            - Mention "{function_name}" as the source in the final summary.

            Begin your summary below:
            """
        else:
        # Use original data for comprehensive analysis
            if isinstance(original_data, dict) and 'data' in original_data:
                api_data = original_data['data']
                endpoint = original_data.get('endpoint', function_name)
                
                analysis_prompt = f"""
                This JSON data represents research data obtained either from the GlobalData API or from a local file, depending on the source specified as '{function_name}'. The research has been conducted to address the user-defined task, which includes a main query and may also include one or more subqueries.

                Your objective is to analyze the research data provided below and generate a comprehensive summary that answers the main query and its subqueries, using only the information present in this research data.

                Research Data Source: {function_name}

                User Task (Query/Subqueries):
                {task}

                Research Data Snapshot:
                {json.dumps(api_data, indent=2, default=str)[:2000]}...

                Instructions:
                - Use only the provided research data to answer the query/subqueries.
                - Clearly structure the response so it covers each query and subquery aspect.
                - Mention "{function_name}" as the source in the final summary.

                Begin your summary below:
                """

            else:
                analysis_prompt = f"""
                This JSON data represents research data obtained either from the GlobalData API or from a local file, depending on the source specified as '{function_name}'. The research has been conducted to address the user-defined task, which includes a main query and may also include one or more subqueries.

                Your objective is to analyze the research data provided below and generate a comprehensive summary that answers the main query and its subqueries, using only the information present in this research data.

                Research Data Source: {function_name}

                User Task (Query/Subqueries):
                {task}

                Research Data Snapshot:
                {json.dumps(api_data, indent=2, default=str)[:2000]}...

                Instructions:
                - Use only the provided research data to answer the query/subqueries.
                - Clearly structure the response so it covers each query and subquery aspect.
                - Mention "{function_name}" as the source in the final summary.

                Begin your summary below:
                    """
        
        # Generate comprehensive summary
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a pharmaceutical data analyst with access to complete preserved datasets. Provide comprehensive analysis."},
                {"role": "user", "content": analysis_prompt}
            ],
            max_tokens=3000,
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"Error generating enhanced AI summary: {e}")
        return f"Comprehensive analysis available for preserved data (ID: {preservation_info['data_id']})"

# Utility functions for data retrieval
def get_complete_analysis(data_id: str, preservation_manager: DataPreservationManager, user_message: str, task: str) -> str:
    """Get complete analysis of preserved data"""
    preserved_data = preservation_manager.get_original_data(data_id)
    if preserved_data:
        original_data = preserved_data["original_data"]
        preservation_info = preserved_data["preservation_info"]
        
        return generate_summary(
            preservation_info["function_name"], 
            original_data, 
            preservation_info,
            user_message,
            task
        )
    return "Data not found"

def export_preserved_data(data_id: str, preservation_manager: DataPreservationManager, 
                         export_format: str = "json") -> str:
    """Export preserved data in specified format"""
    preserved_data = preservation_manager.get_original_data(data_id)
    if not preserved_data:
        return "Data not found"
    
    original_data = preserved_data["original_data"]
    
    if export_format == "json":
        filename = f"exported_data_{data_id}.json"
        with open(filename, 'w') as f:
            json.dump(original_data, f, indent=2, default=str)
        return f"Data exported to {filename}"
    
    elif export_format == "csv":
        # Handle CSV export for tabular data
        if isinstance(original_data, dict) and 'data' in original_data:
            api_data = original_data['data']
            if isinstance(api_data, dict) and 'data' in api_data:
                records = api_data['data']
                if isinstance(records, list) and records:
                    import pandas as pd
                    df = pd.DataFrame(records)
                    filename = f"exported_data_{data_id}.csv"
                    df.to_csv(filename, index=False)
                    return f"Data exported to {filename}"
        return "Data format not suitable for CSV export"
    
    return "Unsupported export format"