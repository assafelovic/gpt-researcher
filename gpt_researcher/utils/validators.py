#validators.py

from typing import List, Optional, Dict
# from pydantic import BaseModel, Field
from langchain_core.pydantic_v1 import BaseModel, Field, validator

class Subtopic(BaseModel):
    task: str = Field(description="Task name", min_length=1)

class Subtopics(BaseModel):
    subtopics: List[Subtopic] = []

class DirectorSobject(BaseModel):
    firstname: str = Field(description="First name of the director")
    lastname: str = Field(description="Last name of the director")
    company_name: str = Field(description="Company name of the director")
    email: Optional[str] = Field(description="Email address of the director", default=None)
    mobile_phone: Optional[str] = Field(description="Mobile phone number of the director", default=None)
    job_title: str = Field(description="Job title of the director")
    source_url: str = Field(description="The primary source URL used in collecting data")

class Director(BaseModel):
    """Name of the director"""
    fullname: str = Field(description="full names of the individual mentioned in the research data who holds title such as director, officer, company owner, partner, executive, or manager related to the company name.")

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