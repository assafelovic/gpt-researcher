from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from gpt_researcher.utils.logger import get_formatted_logger

if TYPE_CHECKING:
    import logging

logger: logging.Logger = get_formatted_logger(__name__)

app: FastAPI = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
