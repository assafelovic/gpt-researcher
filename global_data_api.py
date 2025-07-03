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
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling GlobalData API: {e}")
        raise Exception(f"GlobalData API error: {str(e)}")

# ===== BIOMARKER FUNCTIONS =====

def GetBiomarkersDetails(api_category: str,  user_query: str, keywords: str) -> dict:
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

def GetBiomarkersDailyUpdates(api_category: str,  user_query: str, keywords: str) -> dict:
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

def GetClinicalTrialsDetails(api_category: str,  user_query: str, keywords: str) -> dict:
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

def GetClinicalTrialsLocationsandcontactDetails(api_category: str,  user_query: str, keywords: str) -> dict:
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

def GetClinicalTrialsDailyUpdates(api_category: str,  user_query: str, keywords: str) -> dict:
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

def GetCompanyDetails(api_category: str,  user_query: str, keywords: str) -> dict:
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

def GetDealsDetails(api_category: str,  user_query: str, keywords: str) -> dict:
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

def GetDealsDailyUpdates(api_category: str,  user_query: str, keywords: str) -> dict:
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

def GetPipelineDrugDetails(api_category: str,  user_query: str, keywords: str) -> dict:
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

def GetMarketedDrugDetails(api_category: str,  user_query: str, keywords: str) -> dict:
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

def GetStubDrugs(api_category: str,  user_query: str, keywords: str) -> dict:
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

def GetDrugsDailyUpdates(api_category: str,  user_query: str, keywords: str) -> dict:
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

def GetCompanyFilingListing(api_category: str,  user_query: str, keywords: str) -> dict:
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

def GetInvestigatorsDetails(api_category: str,  user_query: str, keywords: str) -> dict:
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

def GetInvestigatorsDailyUpdates(api_category: str,  user_query: str, keywords: str) -> dict:
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

def GetLOADetails(api_category: str,  user_query: str, keywords: str) -> dict:
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

def GetNewsDetails(api_category: str,  user_query: str, keywords: str) -> dict:
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

def GetNewsDailyUpdates(api_category: str,  user_query: str, keywords: str) -> dict:
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

def GetNPVDetails(api_category: str,  user_query: str, keywords: str) -> dict:
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

def GetPatentsListing(api_category: str,  user_query: str, keywords: str) -> dict:
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

def GetRMTDetails(api_category: str,  user_query: str, keywords: str) -> dict:
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

def GetRMTDailyUpdates(api_category: str,  user_query: str, keywords: str) -> dict:
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

def GetTrialSitesDetails(api_category: str,  user_query: str, keywords: str) -> dict:
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

def GetSiteCoordinatorDetails(api_category: str,  user_query: str, keywords: str) -> dict:
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

def GetTrialSiteDailyUpdates(api_category: str,  user_query: str, keywords: str) -> dict:
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
def GetEpidemiologyDetails(api_category: str,  user_query: str, keywords: str) -> dict:
    """Get epidemiology data based on keyword search or IndicationID."""
    try:
        params = {}
        params["Indication"] = keywords if keywords else None
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
def GetPoliDrugs(api_category: str,  user_query: str, keywords: str) -> dict:
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

def GetPoliTherapyDetails(api_category: str,  user_query: str, keywords: str) -> dict:
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

def GetHTAAssesmentDetails(api_category: str,  user_query: str, keywords: str) -> dict:
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
    
def GetIRPDetails(api_category: str,  user_query: str, keywords: str) -> dict:
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

def GetDrugs(api_category: str,  user_query: str, keywords: str) -> dict:
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

def GetTherapyAreas(api_category: str,  user_query: str, keywords: str) -> dict:
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

def GetTherapyLines(api_category: str,  user_query: str, keywords: str) -> dict:
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

def GetTherapyTypes(api_category: str,  user_query: str, keywords: str) -> dict:
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
def GetDiseaseStage(api_category: str,  user_query: str, keywords: str) -> dict:
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

def GetForexCurrencies(api_category: str,  user_query: str, keywords: str) -> dict:
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

def GetCurrencyConverter(api_category: str,  user_query: str, keywords: str) -> dict:
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
FUNCTION_MAP = {
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

def call_api_function(function_name: str, api_category: str, user_query: str, keywords: str) -> dict:
    """Call the appropriate API function based on function name."""
    keywords = " ".join(keywords)
    if function_name in FUNCTION_MAP:
        return FUNCTION_MAP[function_name](api_category, user_query, keywords)
    else:
        raise Exception(f"Function {function_name} not found in successful endpoints")
