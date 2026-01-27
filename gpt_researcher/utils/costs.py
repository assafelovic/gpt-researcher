"""Cost estimation utilities for LLM API usage.

This module provides functions to estimate the cost of LLM API calls
based on token counts. Cost estimates are based on OpenAI pricing
and may vary for other model providers.
"""

import tiktoken

# Per OpenAI Pricing Page: https://openai.com/api/pricing/
ENCODING_MODEL = "o200k_base"
INPUT_COST_PER_TOKEN = 0.000005
OUTPUT_COST_PER_TOKEN = 0.000015
IMAGE_INFERENCE_COST = 0.003825
EMBEDDING_COST = 0.02 / 1000000  # Assumes new ada-3-small


def estimate_llm_cost(input_content: str, output_content: str) -> float:
    """Estimate the cost of an LLM API call based on input and output content.

    Cost estimation is based on OpenAI pricing and may vary for other models.

    Args:
        input_content: The input text sent to the LLM.
        output_content: The output text received from the LLM.

    Returns:
        The estimated cost in USD.
    """
    encoding = tiktoken.get_encoding(ENCODING_MODEL)
    input_tokens = encoding.encode(input_content)
    output_tokens = encoding.encode(output_content)
    input_costs = len(input_tokens) * INPUT_COST_PER_TOKEN
    output_costs = len(output_tokens) * OUTPUT_COST_PER_TOKEN
    return input_costs + output_costs


def estimate_embedding_cost(model: str, docs: list) -> float:
    """Estimate the cost of embedding documents.

    Args:
        model: The embedding model name.
        docs: List of documents to embed.

    Returns:
        The estimated embedding cost in USD.
    """
    encoding = tiktoken.encoding_for_model(model)
    total_tokens = sum(len(encoding.encode(str(doc))) for doc in docs)
    return total_tokens * EMBEDDING_COST

