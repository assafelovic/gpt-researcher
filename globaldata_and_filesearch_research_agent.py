import os
import json
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
        "function": {
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
        }
    },
    {
        "type": "function",
        "function": {
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
        }
    },
    
    # ===== CLINICAL TRIALS TOOLS =====
    {
        "type": "function",
        "function": {
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
        }
    },
    {
        "type": "function",
        "function": {
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
        }
    },
    {
        "type": "function",
        "function": {
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
        }
    },
    
    # ===== COMPANY TOOLS =====
    {
        "type": "function",
        "function": {
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
        }
    },
    {
        "type": "function",
        "function": {
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
        }
    },
    
    # ===== DEALS TOOLS =====
    {
        "type": "function",
        "function": {
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
        }
    },
    {
        "type": "function",
        "function": {
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
        }
    },
    {
        "type": "function",
        "function": {
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
        }
    },
    
    # ===== DRUGS TOOLS =====
    {
        "type": "function",
        "function": {
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
        }
    },
    {
        "type": "function",
        "function": {
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
        }
    },
    {
        "type": "function",
        "function": {
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
        }
    },
    {
        "type": "function",
        "function": {
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
        }
    },
    {
        "type": "function",
        "function": {
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
        }
    },
    
    # ===== DRUG SALES TOOLS =====
    {
        "type": "function",
        "function": {
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
        }
    },
    {
        "type": "function",
        "function": {
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
        }
    },
    
    # ===== EPIDEMIOLOGY TOOLS =====
    {
        "type": "function",
        "function": {
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
        }
    },
    
    # ===== FILINGS TOOLS =====
    {
        "type": "function",
        "function": {
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
        }
    },
    {
        "type": "function",
        "function": {
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
        }
    },
    
    # ===== INVESTIGATORS TOOLS =====
    {
        "type": "function",
        "function": {
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
        }
    },
    {
        "type": "function",
        "function": {
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
        }
    },
    
    # ===== NEWS TOOLS =====
    {
        "type": "function",
        "function": {
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
        }
    },
    {
        "type": "function",
        "function": {
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
        }
    },
    
    # ===== TRIAL SITES TOOLS =====
    {
        "type": "function",
        "function": {
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
# Dictionary to map function names to actual functions
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

def call_globaldata_api(content: str, vector_id: str = None):
    """
    Process tool calls in batches to avoid token limits
    Now supports both function tools and file search
    """
    original_data = {}
    ai_summaries = {}
    
    try:
        # Prepare tools array - separate function tools from file search
        tools_to_use = []
        
        # Add your existing globaldata function tools
        tools_to_use.extend(globaldata_tools)
        
        # Add file search tool if vector_id is provided
        if vector_id:
            file_search_tool = {
                "type": "file_search"
            }
            tools_to_use.append(file_search_tool)
        
        # Prepare the assistant configuration
        assistant_config = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": "You are a pharmaceutical data analyst with access to GlobalData APIs and file search capabilities. Use the appropriate tools to answer user queries about drugs, clinical trials, companies, deals, and market data. When you need to search internal files or documents, use the file_search tool."},
                {"role": "user", "content": content}
            ],
            "tools": tools_to_use,
            "tool_choice": "auto"
        }
        
        # Add tool_resources if file search is enabled
        if vector_id:
            assistant_config["tool_resources"] = {
                "file_search": {
                    "vector_store_ids": [vector_id],
                    "max_num_results": 10
                }
            }
        
        # Initial API call
        response = client.chat.completions.create(**assistant_config)
        
        if response.choices[0].message.tool_calls:
            tool_calls = response.choices[0].message.tool_calls
            
            # Separate function calls from file search calls
            function_calls = []
            file_search_calls = []
            
            for tool_call in tool_calls:
                if hasattr(tool_call, 'type') and tool_call.type == 'file_search':
                    file_search_calls.append(tool_call)
                else:
                    function_calls.append(tool_call)
            
            batch_size = 2  # Process 2 tool calls at a time
            all_summaries = []
            
            # Process function calls in batches
            if function_calls:
                for i in range(0, len(function_calls), batch_size):
                    batch = function_calls[i:i + batch_size]
                    batch_summaries = process_tool_call_batch(batch, original_data)
                    all_summaries.extend(batch_summaries)
            
            # Process file search calls
            if file_search_calls:
                file_search_summaries = process_file_search_calls(file_search_calls, original_data)
                all_summaries.extend(file_search_summaries)
            
            # Generate AI summaries for each tool's data
            for function_name, data in original_data.items():
                if not function_name.startswith("file_search_"):
                    ai_summary = generate_ai_summary(function_name, data)
                    ai_summaries[function_name] = ai_summary
                else:
                    ai_summaries[function_name] = "File search completed - results integrated into analysis"
            
            # Display results for each tool/function used
            print("\n" + "="*60)
            print("API RESULTS SUMMARY")
            print("="*60)
            
            for i, (function_name, data) in enumerate(original_data.items(), 1):
                print(f"\nSource: {function_name}")
                
                # Show AI-generated summary
                ai_summary = ai_summaries.get(function_name, "Summary not available")
                print(f"Summary: {ai_summary}")
                
                print("API Original Data:")
                print("_" * 50)
                
                # Display original data in a readable format
                display_original_data(data)
                
                # Add separator between different tools
                if i < len(original_data):
                    print("\n" + "-"*50)
                    print(f"END OF TOOL {i} OUTPUT")
                    print("-"*50)
            
            # Create final synthesis
            final_response = synthesize_results(content, all_summaries)
            
            print("\n" + "="*60)
            print("FINAL SYNTHESIS")
            print("="*60)
            
            return final_response, None, original_data
        else:
            return response, None, {}
            
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return None, None, original_data

def generate_ai_summary(function_name, data):
    """Generate AI summary of the original data"""
    try:
        # Prepare the data for analysis
        if isinstance(data, dict) and 'data' in data:
            api_data = data['data']
            endpoint = data.get('endpoint', function_name)
            
            # Create a structured prompt for analysis
            analysis_prompt = f"""
            Analyze the following pharmaceutical data from {endpoint}:
            
            Data Structure: {type(api_data).__name__}
            
            """
            
            # Add data sample for analysis
            if isinstance(api_data, dict) and 'data' in api_data and isinstance(api_data['data'], list):
                records = api_data['data']
                analysis_prompt += f"""
                Total Records: {len(records)}
                
                Sample Data (first 3 records):
                {json.dumps(records[:3], indent=2, default=str)}
                
                Please provide a concise analysis of this data including:
                1. Key insights from the data
                2. Notable patterns or trends
                3. Important findings relevant to pharmaceutical research
                4. Data quality and completeness assessment
                
                Keep the summary under 200 words and focus on actionable insights.
                """
            else:
                analysis_prompt += f"""
                Data Content:
                {json.dumps(api_data, indent=2, default=str)[:1000]}...
                
                Please provide a concise analysis of this pharmaceutical data including key insights and findings.
                Keep the summary under 200 words.
                """
        else:
            analysis_prompt = f"""
            Analyze the following data from {function_name}:
            {json.dumps(data, indent=2, default=str)[:1000]}...
            
            Provide a brief analysis under 200 words.
            """
        
        # Generate AI summary
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a pharmaceutical data analyst. Provide concise, insightful analysis of pharmaceutical data."},
                {"role": "user", "content": analysis_prompt}
            ],
            max_tokens=300,
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"Error generating AI summary for {function_name}: {e}")
        return f"AI summary generation failed for {function_name}"
    """Process file search tool calls"""
    summaries = []
    
    for tool_call in file_search_calls:
        function_name = f"file_search_{tool_call.id}"
        
        # File search results are typically in the tool_call response
        # You might need to extract the actual search results based on your implementation
        search_results = {
            "tool_call_id": tool_call.id,
            "type": "file_search",
            "results": "File search completed"  # This would contain actual search results
        }
        
        original_data[function_name] = search_results
        
        summary = {
            "status": "success",
            "function": function_name,
            "summary": f"File search completed with tool call ID: {tool_call.id}"
        }
        summaries.append(summary)
    
    return summaries

def display_original_data(data):
    """Display original data in a readable format"""
    if isinstance(data, dict):
        # Check if this is a file search result
        if data.get('type') == 'file_search':
            print("File Search Results:")
            print(f"Tool Call ID: {data.get('tool_call_id', 'Unknown')}")
            print(f"Status: {data.get('status', 'Unknown')}")
            
            if 'results' in data:
                results = data['results']
                if isinstance(results, list):
                    print(f"Number of results found: {len(results)}")
                    for i, result in enumerate(results[:3]):  # Show first 3 results
                        print(f"  Result {i+1}: {result}")
                else:
                    print(f"Results: {results}")
            
            if 'ranking_options' in data:
                print(f"Ranking Options: {data['ranking_options']}")
            
            if 'error' in data:
                print(f"Error: {data['error']}")
        
        # Check if this is your API response format with 'data' key
        elif 'data' in data:
            api_data = data['data']
            
            # Show metadata first
            print(f"Endpoint: {data.get('endpoint', 'Unknown')}")
            print(f"Timestamp: {data.get('timestamp', 'Unknown')}")
            print(f"Parameters Used: {data.get('params_used', {})}")
            print()
            
            # Now show the actual data content
            if isinstance(api_data, dict):
                if 'data' in api_data and isinstance(api_data['data'], list):
                    # Handle nested data structure
                    actual_records = api_data['data']
                    print(f"Total Records: {len(actual_records)}")
                    
                    if actual_records:
                        print(f"Sample Record Fields: {list(actual_records[0].keys())}")
                        print("\nFirst 3 Records:")
                        for j, record in enumerate(actual_records[:3]):
                            print(f"  Record {j+1}:")
                            for key, value in record.items():
                                # Truncate long values for readability
                                if isinstance(value, str) and len(value) > 100:
                                    value = value[:100] + "..."
                                print(f"    {key}: {value}")
                            print()
                        
                        if len(actual_records) > 3:
                            print(f"... and {len(actual_records) - 3} more records")
                    else:
                        print("No data records found")
                else:
                    # Handle other data structures within 'data'
                    print("Data Content:")
                    for key, value in api_data.items():
                        if isinstance(value, list):
                            print(f"  {key}: List with {len(value)} items")
                            if value and len(value) > 0:
                                print(f"    Sample items: {value[:2]}")
                        elif isinstance(value, dict):
                            print(f"  {key}: Dict with {len(value)} keys")
                            print(f"    Keys: {list(value.keys())}")
                        else:
                            print(f"  {key}: {value}")
            else:
                print(f"Data Content: {api_data}")
        else:
            # Display other dict structures
            print("Data Structure:")
            for key, value in data.items():
                if isinstance(value, (list, dict)):
                    print(f"  {key}: {type(value).__name__} with {len(value) if hasattr(value, '__len__') else 'N/A'} items")
                    if isinstance(value, list) and value:
                        print(f"    Sample: {value[0]}")
                    elif isinstance(value, dict) and value:
                        print(f"    Keys: {list(value.keys())}")
                else:
                    print(f"  {key}: {value}")
    else:
        print(f"Data Type: {type(data).__name__}")
        print(f"Data: {data}")

def create_data_summary(data, function_name):
    """Create a concise summary of API data for OpenAI processing"""
    if isinstance(data, dict):
        # Handle your API response format
        if 'data' in data:
            api_data = data['data']
            endpoint = data.get('endpoint', function_name)
            
            if isinstance(api_data, dict) and 'data' in api_data and isinstance(api_data['data'], list):
                # Nested data structure
                records = api_data['data']
                return {
                    "status": "success",
                    "function": function_name,
                    "endpoint": endpoint,
                    "total_records": len(records),
                    "sample_fields": list(records[0].keys()) if records else [],
                    "summary": f"Retrieved {len(records)} records from {endpoint} via {function_name}"
                }
            elif isinstance(api_data, dict):
                # Other data structures
                return {
                    "status": "success",
                    "function": function_name,
                    "endpoint": endpoint,
                    "data_keys": list(api_data.keys()),
                    "summary": f"Retrieved structured data from {endpoint} via {function_name}"
                }
            else:
                return {
                    "status": "success",
                    "function": function_name,
                    "endpoint": endpoint,
                    "summary": f"Retrieved data from {endpoint} via {function_name}"
                }
        else:
            # Standard dict structure
            return {
                "status": "success",
                "function": function_name,
                "keys": list(data.keys()),
                "summary": f"Data retrieved from {function_name}"
            }
    else:
        return {
            "status": "success",
            "function": function_name,
            "summary": f"Data retrieved from {function_name} - {type(data).__name__}"
        }
    
def process_tool_call_batch(tool_calls, original_data):
    """Process a batch of function tool calls"""
    summaries = []
    
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)
        
        if function_name in FUNCTION_MAPPING:
            function_result = FUNCTION_MAPPING[function_name](**function_args)
            original_data[function_name] = function_result
            
            summary = create_data_summary(function_result, function_name)
            summaries.append(summary)
    
    return summaries

def synthesize_results(original_query, summaries):
    """Create final synthesis from summaries"""
    synthesis_prompt = f"""
    Original query: {original_query}
    
    Data summaries from API calls:
    {json.dumps(summaries, indent=2)}
    
    Please provide a comprehensive analysis based on the data summaries above.
    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a pharmaceutical data analyst. Synthesize the API data summaries into a comprehensive response."},
            {"role": "user", "content": synthesis_prompt}
        ],
        max_tokens=4000
    )
    
    return response


# Test the implementation
if __name__ == "__main__":
    query = """My company is evaluating the opportunity for a high dose once monthly injectable GLP-1/GIP/Glucagon receptor triple agonist for long-term weight loss maintenance therapy for obesity. Evaluate the market opportunity and unmet need for long-term obesity maintenance therapies. Focus on segmentation across the following axes:
                • BMI categories: Class I (30–35), Class II (35–40), Class III (≥40)
                • Patient subgroups: with vs. without Type 2 diabetes, prior bariatric surgery, responders vs. non-responders to induction therapy
                • Current standard of care and limitations (e.g., semaglutide, tirzepatide, lifestyle adherence, drop-off rates after weight loss plateau)
                • Pipeline therapies explicitly being developed or positioned for maintenance (vs. induction), including mechanisms (e.g., amylin analogs, GLP-1/GIP modulators, FGF21 analogs, etc.)
                • Real-world adherence data and discontinuation drivers post-weight loss
                • Expected commercial segmentation: e.g., how payers and physicians differentiate between induction and maintenance use (pricing, access hurdles)
                • Sales forecasts for therapies with long-term administration profiles (≥12 months)
                • Competitive positioning of novel candidates offering less frequent dosing, improved tolerability, or weight regain prevention efficacy
    """
    research_plan = """
        {
    "ResearchObjectiveAndScope": {
        "PrimaryResearchQuestion": "What is the market opportunity and unmet need for long-term obesity maintenance therapies, specifically for a high dose once monthly injectable GLP-1/GIP/Glucagon receptor triple agonist, across varied patient subgroups and BMI categories?",
        "SuccessCriteriaAndDeliverables": "• A comprehensive segmentation analysis by BMI, diabetes status, prior bariatric surgery, and response to induction therapy.  • Identification of current standard of care limitations and a detailed mapping of pipeline therapies positioned for maintenance.  • Validated sales forecasts and competitive positioning data from internal and GlobalData sources.  • A final report with integrated data insights, charts, and documented cross-validations among multiple datasets.",
        "TimelineAndResourceNeeds": "The research is estimated to span 4–6 weeks, requiring access to internal knowledge bases, GlobalData pharmaceutical, deals, clinical trials, patent, and competitive intelligence APIs, and a team including a research strategist, data analyst, and subject matter experts in obesity and metabolic therapies."
    },
    "PhaseByPhaseResearchStrategy": {
        "Phase1_KnowledgeBaseAnalysis": {
        "Objective": "Leverage internal documents and previous research files to collect baseline data on long-term obesity maintenance strategies, patient segmentation, and competitive therapies.",
        "FileSearchStrategy": {
            "ExactSearchTerms": [
            "long-term weight loss maintenance",
            "obesity BMI segmentation",
            "GLP-1/GIP/Glucagon receptor triple agonist",
            "obesity maintenance therapy",
            "real-world adherence weight loss"
            ],
            "QueryPatterns": "Combine key phrases with Boolean operators (AND/OR) to locate relevant slides and documents (e.g., 'pipeline AND obesity maintenance', 'semaglutide OR tirzepatide AND weight loss plateau')"
        },
        "KeywordsAndQueryPatterns": {
            "PrimarySubQuery": "What is the current market opportunity and unmet need for long-term obesity maintenance therapies across BMI categories and patient subsegments?",
            "ComprehensiveSubQuery": "How do patient segmentation (by BMI class, diabetes presence, prior bariatric surgery, and response to induction therapy), current standard of care limitations (including dropout rates and lifestyle adherence challenges), and competitive pipeline asset profiles (mechanisms, dosing frequency, tolerability) collectively determine the commercial prospects for a once monthly injectable triple agonist therapy for obesity maintenance?",
            "KeywordsForGlobalDataAPICalls": [
            "obesity",
            "Type 2 diabetes",
            "GLP-1/GIP/Glucagon",
            "BMI segmentation",
            "weight loss maintenance"
            ]
        },
        "Rationale": "This phase ensures that all internal data, historical research, and previously identified insights are gathered to form a baseline understanding. It aligns with user insights by covering multiple segmentation axes and clinical endpoints relevant to the market and competitive landscape of obesity maintenance therapies."
        },
        "Phase2_GlobalDataIntelligenceCollection": {
        "Overview": "Utilize GlobalData APIs to extract, filter, and analyze data on pipeline therapies, clinical trials, deals, patents, and competitive positioning in the obesity treatment space with a focus on long-term maintenance.",
        "APICollectionStrategy": {
            "PipelineIntelligence": {
            "APIEndpoint": "Pharma Intelligence API",
            "Filters": {
                "Indication": "obesity / weight loss",
                "MoleculeType": "triple agonist, GLP-1/GIP/Glucagon",
                "TherapyProfile": "maintenance vs induction",
                "TimeFrame": "latest 5–10 years"
            },
            "FileSearchQueries": "Search internal files for tables/graphs on pipeline programs and slide references (e.g., Slide 6 & 7) to extract MoA and target details."
            },
            "DealIntelligence": {
            "APIEndpoint": "Deals Intelligence API",
            "Filters": {
                "DealType": "acquisitions, in-licensing, option agreements, collaborations",
                "AssetFocus": "obesity, weight loss, metabolic therapies",
                "DataPoints": "licensing terms, exercised options, remaining rights"
            },
            "FileSearchQueries": "Use internal documents (referenced in Fundamental Intelligence > Deals) to cross-check partnership and deal details."
            },
            "ClinicalIntelligence": {
            "APIEndpoint": "Clinical Trials Intelligence API",
            "Filters": {
                "Indication": "obesity, weight management",
                "StudyDuration": "long-term (≥12 months)",
                "PatientSubgroups": "BMI classes, diabetes status, prior bariatric surgery"
            },
            "FileSearchQueries": "Identify slides detailing trial designs, endpoints, and patient population characteristics (e.g., Slide 10 and trial design documents)."
            },
            "PatentIntelligence": {
            "APIEndpoint": "Patent Intelligence API",
            "Filters": {
                "Keywords": "GLP-1, triple agonist, obesity maintenance",
                "Jurisdictions": "global, with focus on major markets (US, EU, China)",
                "Status": "active patents and expiry dates"
            }
            },
            "CompetitiveIntelligence": {
            "APIEndpoint": "Competitive Intelligence API",
            "Filters": {
                "SearchParameter": "target-based search using MoA details",
                "MarketComparison": "pipeline and marketed assets for obesity and weight loss",
                "Differentiators": "dosing frequency, tolerability, weight regain prevention efficacy"
            }
            }
        }
        },
        "Phase3_DataIntegrationAndCrossValidation": {
        "Objective": "Integrate internal file findings with GlobalData API outputs to validate trends, identify data gaps, and ensure consistency across multiple data sources.",
        "CrossValidationLogic": {
            "InternalVsAPI": "Match key metrics and trends (e.g., patient segmentation breakdown, sales forecasts, and competitive differentiators) between internal documents and GlobalData API outputs.",
            "DealTermsValidation": "Confirm licensing terms and deal structures by comparing Deals Intelligence API data with internal partnership documents.",
            "ClinicalProgressValidation": "Cross-check trial designs, endpoints, and patient subgroup data from the Clinical Trials Intelligence API with internal clinical strategy documents.",
            "DataGapIdentification": "Highlight discrepancies or missing data points for additional research or follow-up queries."
        },
        "ResourceAndIntegrationApproach": "Use data integration tools (e.g., spreadsheets, data visualization software) to map API outputs with internal findings; ensure iterative review meetings with subject matter experts for decision validation."
        }
    },
    "SpecificResearchStrategies": {
        "PrimarySubQuery": "What is the current market opportunity and unmet need for long-term obesity maintenance therapies across BMI categories and patient subsegments?",
        "ComprehensiveSubQuery": "How do factors such as BMI segmentation (Class I: 30–35, Class II: 35–40, Class III: ≥40), patient subgroup differences (with vs. without Type 2 diabetes, prior bariatric surgery, responders vs. non-responders), limitations with current standard of care (e.g., semaglutide, tirzepatide, lifestyle adherence issues), and the competitive pipeline (including novel maintenance-focused mechanisms) inform the potential commercial success of a once monthly injectable GLP-1/GIP/Glucagon receptor triple agonist?",
        "GlobalDataAPICallKeywords": [
        "obesity",
        "Type 2 diabetes",
        "GLP-1/GIP/Glucagon",
        "BMI segmentation",
        "weight loss maintenance"
        ],
        "Rationale": "This research strategy is tailored to capture both the clinical and commercial nuances of long-term weight loss maintenance therapies. It aligns with user insights by integrating detailed pipeline, partnership, target, competitive, epidemiological, market, clinical trial, and deal analyses, thereby ensuring that all axes of market segmentation and pipeline dynamics are thoroughly examined."
    }
    }
"""

    user_content = f"""
    **User Query:** {query}

    **Research Plan:** {research_plan}


    Please analyze the user query and use the appropriate GlobalData API tools to gather comprehensive information about AbbVie's oncology pipeline, particularly focusing on NSCLC, SCLC, and CRC programs.
    """

    print("Making API call...")
    final_response, _, original_data = call_globaldata_api(user_content)
    
    # print(final_response)
    # print(original_data)
