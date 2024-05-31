#validators.py
import logging

from enum import Enum
from typing import List, Optional, Dict, Union
# from pydantic import BaseModel, Field
from langchain_core.pydantic_v1 import BaseModel, Field, validator
from datetime import date, datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Subtopic(BaseModel):
    task: str = Field(description="Task name", min_length=1)

class Subtopics(BaseModel):
    subtopics: List[Subtopic] = []

class SalutationEnum(str, Enum):
    none = "--None--"
    mr = "Mr."
    ms = "Ms."
    mrs = "Mrs."
    dr = "Dr."
    prof = "Prof."
    mx = "Mx."

class LeadSourceEnum(str, Enum):
    none = "--None--"
    web = "Web"
    phone_inquiry = "Phone Inquiry"
    partner_referral = "Partner Referral"
    purchased_list = "Purchased List"
    other = "Other"
    trade_show = "Trade Show"

class RiskAssessmentEnum(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class Contact(BaseModel):
    """Full name of the of the individual mentioned in the research data who holds title such as director, officer, company owner, partner, executive, or manager related to the company name."""
    first_name: str = Field(..., description="first name")
    last_name: str = Field(..., description="last name")

class Contacts(BaseModel):
    """List of contact names"""
    contacts: List[Contact] = []

class ContactSobject(BaseModel):
    """Full list of details of the contact"""
    salutation: SalutationEnum = Field(..., description="Salutation that you think best fits contact")
    lead_source: LeadSourceEnum = Field(..., description="Lead source of the contact")
    firstname: str = Field(..., description="First name of the contact")
    lastname: str = Field(..., description="Last name of the contact")
    related_companies: str = Field(default="", description="List of related companies")
    email: str = Field(default="", description="Email address of the contact")
    mobile_phone: str = Field(default="", description="Mobile phone number of the contact")
    job_title: str = Field(..., description="Job title of the contact")
    primary_source_url: str = Field(..., description="The primary source URL used in collecting data")

class ComplianceCompanySobject(BaseModel):
    """Company Details"""
    company_name: str = Field(..., description="Full legal company name")
    registration_number: str = Field(default="", description="Company registration number")
    incorporation_date: str = Field(default="", description="Incorporation date in yyyy-mm-dd format (e.g. 2023-02-13)")
    jurisdiction: str = Field(default="", description="Jurisdiction of incorporation")
    registered_address: str = Field(default="", description="Registered office address")
    licenses: str = Field(default="", description="Regulatory licenses and registrations held")
    regulatory_actions: str = Field(default="", description="Past regulatory actions, fines or investigations")
    adverse_media: str = Field(default="", description="Adverse media or reports of financial crime, fraud or unethical practices")
    risk_assessment: RiskAssessmentEnum = Field(..., description="Overall risk assessment for the company")
    primary_source_url: str = Field(..., description="The primary source URL used in collecting data")

    @validator("incorporation_date", pre=True)
    def parse_incorporation_date(cls, value):
        if not value:
            return ""
        try:
            parsed_date = datetime.strptime(value, "%Y-%m-%d").date()
            formatted_date = parsed_date.strftime("%Y-%m-%d")  # Convert date to string
            logger.info(f"Successfully parsed incorporation date: {formatted_date}")
            return formatted_date
        except ValueError:
            logger.error(f"Invalid incorporation date format. Expected YYYY-MM-DD, but got: {value}")
            return ""

class SalesCompanySobject(BaseModel):
    """Company Sales Details"""
    company_name: str = Field(..., description="Full legal company name")
    annual_revenue: float = Field(default=0.0, description="Annual revenue of the company")
    num_employees: int = Field(default=0, description="Number of employees in the company")
    industry: str = Field(default="", description="Industry sector of the company")
    website: str = Field(default="", description="Company website URL")
    phone: str = Field(default="", description="Company phone number")
    address: str = Field(default="", description="Company address")
    city: str = Field(default="", description="City where the company is located")
    state: str = Field(default="", description="State where the company is located")
    zip_code: str = Field(default="", description="ZIP code of the company's location")
    country: str = Field(default="", description="Country where the company is located")
    primary_source_url: str = Field(..., description="The primary source URL used in collecting data")

class ReportResponse(BaseModel):
    report: str = Field(description="Company report")
    company: Union[ComplianceCompanySobject, SalesCompanySobject] = Field(description="Company details")
    contacts: List[Dict] = Field(description="List of contacts")
    source_urls: List[str] = Field(description="List of source URLs")

class ReportRequest(BaseModel):
    query: str
    salesforce_id: str
    contacts: Optional[List[str]] = []
    include_domains: Optional[List[str]] = []
    exclude_domains: Optional[List[str]] = []
    parent_sub_queries: Optional[List[str]] = []
    child_sub_queries: Optional[List[str]] = []