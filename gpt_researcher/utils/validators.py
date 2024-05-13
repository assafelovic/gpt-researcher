from typing import List

from pydantic import BaseModel, Field

class Subtopic(BaseModel):
    task: str = Field(description="Task name", min_length=1)

class Subtopics(BaseModel):
    subtopics: List[Subtopic] = []

class DirectorSobject(BaseModel):
    FirstName: str = Field(description="First name of the director")
    LastName: str = Field(description="Last name of the director")
    Company: str = Field(description="Company name associated with the director")
    Email: str = Field(description="Email address of the director")
    MobilePhone: str = Field(description="Mobile phone number of the director")
    Title: str = Field(description="Job title of the director")
    LeadSource: str = Field(description="Source URL from which the director info was obtained")

class DirectorsSobject(BaseModel):
    directors: List[DirectorSobject] = []

class Director(BaseModel):
    FullName: str = Field(description="First name of the director")

class Directors(BaseModel):
    directors: List[Director] = []