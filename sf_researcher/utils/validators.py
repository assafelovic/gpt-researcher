#validators.py
import logging

from enum import Enum
from typing import List, Optional, Dict, Union
# from pydantic import BaseModel, Field
from langchain_core.pydantic_v1 import BaseModel, Field, validator
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SalutationEnum(str, Enum):
    mr = "Mr."
    ms = "Ms."
    mrs = "Mrs."
    dr = "Dr."
    prof = "Prof."
    mx = "Mx."

class RiskAssessmentEnum(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

from pydantic import BaseModel, Field, validator
from typing import List

class Contact(BaseModel):
    first_name: str = Field(..., description="first name")
    last_name: str = Field(..., description="last name")

    @validator('last_name')
    def validate_last_name(cls, value):
        null_type_values = [
            "unknown", "unidentified", "not found", "n/a", "na", "nil", "none",
            "unnamed", "undisclosed", "redacted", "withheld", "private",
            "confidential", "restricted", "classified", "secret", "top secret",
            "sensitive", "protected", "proprietary", "undetermined", "unspecified",
            "unrecognized", "unacknowledged", "unverified", "untraceable",
            "unlisted", "unregistered", "unreported", "unrecorded", "unseen",
            "hidden", "concealed", "obscured", "masked", "disguised", "anonymous"
        ]
        if value.lower() in null_type_values:
            raise ValueError(f"Invalid last name: {value}")
        return value

class Contacts(BaseModel):
    contacts: List[Contact] = []

    @validator('contacts', pre=True, each_item=True)
    def validate_contacts(cls, value):
        try:
            return Contact(**value)
        except ValueError:
            return None

    @validator('contacts')
    def remove_none_contacts(cls, value):
        return [contact for contact in value if contact is not None]

class ContactSobject(BaseModel):
    """Full list of details of the contact"""
    salutation: SalutationEnum = Field(..., description="Salutation that you think best fits contact")
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
    company_name: str = Field(..., description="Full legal company name")
    annual_revenue: int = Field(default=0, description="Annual revenue of the company")
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
    average_deal_size: int = Field(default=0, description="Average deal size")
    largest_deal_amount: int = Field(default=0, description="Largest deal amount")
    number_of_deals_closed: int = Field(default=0, description="Number of deals closed")
    quota_attainment: int = Field(default=0, description="Quota attainment in percentage")
    sales_cycle_duration: int = Field(default=0, description="Sales cycle duration in days")
    sales_forecast: int = Field(default=0, description="Sales forecast")
    sales_growth: int = Field(default=0, description="Sales growth percentage")
    top_selling_product: str = Field(default="", description="Top selling product")
    total_revenue: int = Field(default=0, description="Total revenue")
    win_rate: int = Field(default=0, description="Win rate percentage")
    report: str = Field(..., description="Detailed sales report")
    source_urls: str = Field(default="", description="Source URLs used in collecting data")
    registration_number: str = Field(default="", description="Company registration number")
    incorporation_date: str = Field(default="", description="Incorporation date of the company")


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
    parent_retreiver_queries: Optional[List[str]] = []
    child_retreiver_queries: Optional[List[str]] = []

################################################################################################

# SEARCH ANALYSIS

class SearchContentTypeEnum(str, Enum):
    """Enum class representing different kind of content represented in the search result."""
    company_information = "Company Information"
    director_information = "Director Information"
    company_news = "Company News"
    director_news = "Director News"

    # funding_details = "Funding Details"
    # executive_information = "Executive Information"
    # director_information = "Director Information"
    # competitor_analysis = "Competitor Analysis"
    # general_overview = "General Overview"
    # product_details = "Product Details"
    # market_analysis = "Market Analysis"
    # news_mentions = "News Mentions"
    # financial_performance = "Financial Performance"
    # customer_reviews = "Customer Reviews"
    # contact_information = "Contact Information"
    # legal_issues = "Legal Issues"
    # industry_trends = "Industry Trends"
    # supplier_information = "Supplier Information"
    # partnerships = "Partnerships"
    # social_media_activity = "Social Media Activity"
    # employee_reviews = "Employee Reviews"
    # patents_and_ip = "Patents and Intellectual Property"
    # company_history = "Company History"
    # investors = "Investors"
    # sustainability_practices = "Sustainability Practices"
    # market_position = "Market Position"
    # brand_reputation = "Brand Reputation"
    # business_model = "Business Model"
    # technology_stack = "Technology Stack"
    # expansion_plans = "Expansion Plans"
    # csr_activities = "Corporate Social Responsibility Activities"
    # risk_factors = "Risk Factors"
    # awards_and_recognitions = "Awards and Recognitions"
    # strategic_initiatives = "Strategic Initiatives"
    # customer_segments = "Customer Segments"
    # pricing_strategy = "Pricing Strategy"
    # operational_performance = "Operational Performance"

class SourceTypeEnum(str, Enum):
    """Enum class representing different types of sources represented in the search result."""
    official_website = "Official Website and Blog"
    government_filing = "Government Filing"
    business_director = "Business Directory"
    social_media = "Social Media"
    
    # official_blog = "Official Blog"
    # news_article = "News Article"
    # financial_report = "Financial Report"
    # industry_blog = "Industry Blog"
    # press_release = "Press Release"
    # market_research_report = "Market Research Report"
    # customer_feedback_platform = "Customer Feedback Platform"
    # employee_review_platform = "Employee Review Platform"
    # patent_database = "Patent Database"
    # trade_journal = "Trade Journal"
    # investment_analysis_report = "Investment Analysis Report"
    # company_presentation = "Company Presentation"
    # webinar = "Webinar"
    # podcast = "Podcast"
    # conference_talk = "Conference Talk"

class InitialSearchResult(BaseModel):
    """Model representing an individual search result item."""
    title: str = Field(..., description="Title of the search result")
    href: str = Field(..., description="URL of the search result")
    search_category: SearchContentTypeEnum = Field(..., description="Search content tyoe that best fits the result")
    source_type: SourceTypeEnum = Field(..., description="Source type that best fits the result")
    exclusion: bool = Field(..., description="Bool value whether the search result item should be excluded due to relevance to the overall goal")
    reason: str = Field(..., description="Reason why the search should be inlcuded or excluded - single sentence")

class InitialSearchResults(BaseModel):
    """Model representing a list of initial search result items."""
    items: List[InitialSearchResult] = Field(..., description="List of search result items")