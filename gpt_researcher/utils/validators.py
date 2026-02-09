"""Pydantic validation models for GPT Researcher."""

from typing import List

from pydantic import BaseModel, Field


class Subtopic(BaseModel):
    """Model representing a single research subtopic.

    Attributes:
        task: The name or description of the subtopic task.
    """
    task: str = Field(description="Task name", min_length=1)


class Subtopics(BaseModel):
    """Model representing a collection of research subtopics.

    Used for parsing and validating subtopic lists generated
    by the LLM during research planning.

    Attributes:
        subtopics: List of Subtopic objects.
    """
    subtopics: List[Subtopic] = []
