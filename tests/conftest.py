"""Shared pytest fixtures for GPT-Researcher tests."""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Any, Generator

import pytest

# Add current directory to path for imports
sys.path.insert(0, ".")


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, Any, None]:
    """Create an instance of the default event loop for the test session."""
    loop: asyncio.AbstractEventLoop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment() -> Generator[None, Any, None]:
    """Set up the test environment with necessary configurations."""
    # Store original environment
    original_env: dict[str, str] = os.environ.copy()

    # Set test environment variables
    test_env: dict[str, str] = {
        "FAST_LLM": "auto",
        "SMART_LLM": "auto",
        "STRATEGIC_LLM": "auto",
        "LOG_LEVEL": "INFO",
    }

    for key, value in test_env.items():
        os.environ[key] = value

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(scope="session")
def test_config() -> dict[str, Any] | None:
    """Provide test configuration settings."""
    return {
        "timeout": 30,
        "max_retries": 3,
        "test_queries": [
            "What is artificial intelligence?",
            "Explain machine learning basics",
            "What are the benefits of renewable energy?",
        ],
        "test_contexts": {
            "short": "AI is a field of computer science.",
            "medium": "Artificial intelligence (AI) is a branch of computer science that aims to create intelligent machines."
            * 10,
            "large": "This is a test sentence for large context processing. " * 1000,
        },
    }


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest with custom settings."""
    # Add custom markers
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line(
        "markers",
        "requires_api: mark test as requiring API access",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add slow marker to tests that might be slow
        if "large_context" in item.name or "report_generation" in item.name:
            item.add_marker(pytest.mark.slow)

        # Add integration marker to tests that test multiple components
        if "fallback_mechanism" in item.name or "report_generation" in item.name:
            item.add_marker(pytest.mark.integration)

        # Add unit marker to isolated tests
        if "import" in item.name or "loading" in item.name:
            item.add_marker(pytest.mark.unit)

        # Add requires_api marker to tests that need API access
        if "fallback" in item.name or "report" in item.name:
            item.add_marker(pytest.mark.requires_api)


def pytest_runtest_setup(item: pytest.Item) -> None:
    """Setup function called before each test."""
    # Skip slow tests unless explicitly requested
    if "slow" in item.keywords and not item.config.getoption(
        "--runslow",
        default=False,
    ):
        pytest.skip("need --runslow option to run slow tests")


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command line options for pytest."""
    parser.addoption(
        "--runslow",
        action="store_true",
        default=False,
        help="run slow tests",
    )
    parser.addoption(
        "--runapi",
        action="store_true",
        default=False,
        help="run tests that require API access",
    )


@pytest.fixture
def mock_llm_response() -> dict[str, str]:
    """Provide mock LLM responses for testing."""
    return {
        "simple": "Hello, this is a test response!",
        "ai_query": "Artificial Intelligence (AI) is a branch of computer science that aims to create intelligent machines capable of performing tasks that typically require human intelligence.",
        "summary": "This is a comprehensive summary of the provided context.",
        "error": "I apologize, but I cannot process this request at the moment.",
    }


@pytest.fixture
def sample_contexts() -> dict[str, str]:
    """Provide sample contexts for testing."""
    return {
        "ai_context": "Artificial intelligence (AI) is a branch of computer science that aims to create intelligent machines that can perform tasks that typically require human intelligence. AI systems can learn, reason, and make decisions.",
        "renewable_energy": "Renewable energy comes from natural sources that are constantly replenished, such as solar, wind, hydro, and geothermal power. These sources are sustainable and environmentally friendly alternatives to fossil fuels.",
        "large_context": "This is a test sentence for large context processing. "
        * 1000,
    }


@pytest.fixture
def test_queries() -> list[str]:
    """Provide test queries for various scenarios."""
    return [
        "What is artificial intelligence?",
        "Explain the benefits of renewable energy",
        "How does machine learning work?",
        "What are the challenges in climate change?",
        "Describe the evolution of web technologies",
    ]
