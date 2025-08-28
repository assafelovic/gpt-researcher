import tiktoken

# Per OpenAI Pricing Page: https://openai.com/api/pricing/
ENCODING_MODEL = "o200k_base"
INPUT_COST_PER_TOKEN = 0.000005
OUTPUT_COST_PER_TOKEN = 0.000015
IMAGE_INFERENCE_COST = 0.003825
EMBEDDING_COST = 0.02 / 1000000 # Assumes new ada-3-small


# Cost estimation is via OpenAI libraries and models. May vary for other models
def get_llm_token_counts(input_content: str, output_content: str) -> tuple[int, int]:
    encoding = tiktoken.get_encoding(ENCODING_MODEL)
    input_tokens = len(encoding.encode(input_content))
    output_tokens = len(encoding.encode(output_content))
    return input_tokens, output_tokens


def estimate_llm_cost(input_content: str, output_content: str) -> float:
    input_tokens, output_tokens = get_llm_token_counts(input_content, output_content)
    input_costs = input_tokens * INPUT_COST_PER_TOKEN
    output_costs = output_tokens * OUTPUT_COST_PER_TOKEN
    return input_costs + output_costs


def estimate_embedding_cost(model, docs):
    encoding = tiktoken.encoding_for_model(model)
    total_tokens = sum(len(encoding.encode(str(doc))) for doc in docs)
    return total_tokens * EMBEDDING_COST

