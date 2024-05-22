#validators.py

from enum import Enum
from typing import List, Optional, Dict
# from pydantic import BaseModel, Field
from langchain_core.pydantic_v1 import BaseModel, Field, validator

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

class DirectorSobject(BaseModel):
    """Full list of details of the director"""
    salutation: SalutationEnum = Field(description="Salutation that you think best fits director")
    lead_source: LeadSourceEnum = Field(description="Lead source of the director")
    firstname: str = Field(description="First name of the director")
    lastname: str = Field(description="Last name of the director")
    related_companies: Optional[List[str]] = Field(description="List of related companies", default=None)
    email: Optional[str] = Field(description="Email address of the director", default=None)
    mobile_phone: Optional[str] = Field(description="Mobile phone number of the director", default=None)
    job_title: str = Field(description="Job title of the director")
    source_url: str = Field(description="The primary source URL used in collecting data")

class Director(BaseModel):
    """Full name of the of the individual mentioned in the research data who holds title such as director, officer, company owner, partner, executive, or manager related to the company name."""
    first_name: str = Field(description="first name")
    last_name: str = Field(description="last name")


class Directors(BaseModel):
    """List of director names"""
    directors: List[Director] = []

class CompanySobject(BaseModel):
    company_name: str = Field(description="Full legal company name")
    registration_number: str = Field(description="Company registration number")
    incorporation_date: str = Field(description="Incorporation date")
    jurisdiction: str = Field(description="Jurisdiction of incorporation")
    registered_address: str = Field(description="Registered office address")
    licenses: Optional[str] = Field(description="Regulatory licenses and registrations held", default=None)
    regulatory_actions: Optional[str] = Field(description="Past regulatory actions, fines or investigations", default=None)
    adverse_media: Optional[str] = Field(description="Adverse media or reports of financial crime, fraud or unethical practices", default=None)
    risk_assessment: str = Field(description="Overall assessment of compliance risk level")
    source_url: str = Field(description="The primary source URL used in collecting data")

class CompanyReport(BaseModel):
    report: str = Field(description="Company report")
    company: CompanySobject = Field(description="Company details")
    directors: List[Dict] = Field(description="List of directors")
    source_urls: List[str] = Field(description="List of source URLs")