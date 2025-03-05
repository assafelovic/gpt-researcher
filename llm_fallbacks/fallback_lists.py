from __future__ import annotations

import json

ONLINE_REASONING_CHAT_LLM_PRIORITY_ORDER = [
    "o1",
    "o1-preview",
    "gemini-2.0-flash-thinking-exp",
    "deepseek-r1",
    "o1-mini",
]

ONLINE_CHAT_LLM_PRIORITY_ORDER = [
    "gemini-exp-1206",
    "chatgpt-4o-latest",
    "gemini-exp-1121",
    "gemini-2.0-flash-thinking-exp",
    "gemini-2.0-flash-exp",
    "o1",
    "gemini-exp-1114",
    "o1-preview",
    "deepseek-v3",
    "step-2-16k-exp",
    "o1-mini",
    "gemini-1.5-pro-002",
    "gemini-1.5-pro-exp-0827",
    "gemini-1.5-pro-exp-0801",
    "grok-2",
    "yi-lightning",
    "gpt-4o",
    "claude-3.5-sonnet",
    "qwen2.5-plus-1127",
    "deepseek-v2.5-1210",
    "athene-v2-chat-72b",
    "glm-4-plus",
    "gpt-4o-mini",
    "gemini-1.5-flash-002",
    "gemini-1.5-flash-exp-0827",
    "llama-3.1-nemotron-70b-instruct",
    "meta-llama-3.1-405b-instruct-bf16",
    "meta-llama-3.1-405b-instruct-fp8",
    "gemini-advanced-app",
    "grok-2-mini",
    "yi-lightning-lite",
    "qwen-max-0919",
    "gemini-1.5-pro-001",
    "deepseek-v2.5",
    "gemini-1.5-pro-preview-0409",
    "qwen2.5-72b-instruct",
    "llama-3.3-70b-instruct",
    "gpt-4-turbo",
    "mistral-large-2407",
    "gpt-4-1106-preview",
    "athene-70b",
    "meta-llama-3.1-70b-instruct",
    "llama-3.1-community",
    "claude-3-opus",
    "gpt-4-0125-preview",
    "amazon-nova-pro-1.0",
    "llama-3.1-tulu-3-70b",
    "llama-3.1",
    "mistral-large-2411",
    "yi-large-preview",
    "claude-3.5-haiku",
    "gemini-1.5-flash-001",
    "qwen-plus-0828",
    "jamba-1.5-large",
    "jamba-open",
    "gemma-2-27b-it",
    "deepseek-v2-api-0628",
    "amazon-nova-lite-1.0",
    "qwen2.5-coder-32b-instruct",
    "gemma-2-9b-it-simpo",
    "command-r+",
    "deepseek-coder",
    "yi-large",
]

ONLINE_EMBEDDING_MODELS = [
    "text-embedding-ada-002",
    "BAAI/bge-large-en-v1.5",
    "text-similarity-davinci-001",
]


# GPU-Rich Device Models
LOCAL_GPU_RICH_RERANKING_MODELS = [
    "gte-qwen2-7b-instruct",
    "stella_en_1.5b_v5",
    "gme-qwen2-vl-7b-instruct-q5_k_s-gguf",
    "gme-qwen2-vl-7b-instruct",
    "jasper_en_vision_language_v1",
    "lens-d8000",
    "lens-d4000",
    "speed-embedding-7b-instruct",
    "nv-embed-v2",
    "sfr-embedding-mistral",
]

LOCAL_GPU_RICH_RETRIEVAL_MODELS = [
    "nv-embed-v2",
    "bge-en-icl",
    "lens-d8000",
    "stella_en_1.5b_v5",
    "nv-retriever-v1",
    "lens-d4000",
    "gte-qwen2-7b-instruct",
    "linq-embed-mistral",
    "sfr-embedding-2_r",
    "zeta-alpha-e5-mistral",
    "nv-embed-v1",
]

LOCAL_GPU_RICH_STS_MODELS = [
    "bilingual-embedding-large",
    "jina-embeddings-v3",
    "jina-embeddings-v3",
    "voyage-lite-02-instruct",
    "speed-embedding-7b-instruct",
    "text-embedding-004",
    "sfr-embedding-mistral",
    "multilingual-e5-large-instruct",
    "linq-embed-mistral",
    "text-embedding-004-256",
    "lens-d8000",
    "e5-mistral-7b-instruct",
]

LOCAL_GPU_RICH_SUMMARIZATION_MODELS = [
    "sgpt-bloom-7b1-msmarco",
    "mxbai-embed-large-v1",
    "mxbai-embed-large-v1-q4_k_m-gguf",
    "text-embedding-004",
    "stella-base-en-v2",
    "yiyouliao",
    "text-embedding-004-256",
    "instructor-xl",
    "arabic-labse-matryoshka",
    "mug-b-1.6",
    "udever-bloom-560m",
]

# Edge Device Models
LOCAL_EDGE_DEVICE_RERANKING_MODELS = [
    "stella-base-en-v2",
    "gist-small-embedding-v0",
    "all-minilm-l12-v2",
    "all-minilm-l6-v2",
    "gist-all-minilm-l6-v2",
    "gte-small",
    "bge-small-en-v1.5",
    "medembed-small-v0.1",
    "noinstruct-small-embedding-v0",
]

LOCAL_CONSUMER_EMBEDDING_MODELS = [
    "cde-small-v2",
    "cde-small-v1",
    "gte-base-en-v1.5",
    "gist-embedding-v0",
    "gist-small-embedding-v0",
    "gte-base",
    "nomic-embed-text-v1.5",
    "nomic-embed-text-v1.0",
    "nomic-embed-text-v1.5-512",
    "e5-base-v2",
    "nomic-embed-text-v1-ablated",
    "gte-small",
    "nomic-embed-text-v1.5-256",
]

LOCAL_EDGE_DEVICE_RETRIEVAL_MODELS = [
    "medembed-small-v0.1",
    "noinstruct-small-embedding-v0",
    "snowflake-arctic-embed-s",
    "bge-small-en-v1.5",
    "gist-small-embedding-v0",
    "snowflake-arctic-embed-xs",
    "stella-base-en-v2",
    "gte-small",
    "granite-embedding-30m-english",
    "e5-small-v2",
]

LOCAL_EDGE_DEVICE_STS_MODELS = [
    "gist-small-embedding-v0",
    "stella-base-en-v2",
    "noinstruct-small-embedding-v0",
    "gte-small",
    "bge-small-en-v1.5",
    "medembed-small-v0.1",
    "e5-small",
    "gist-all-minilm-l6-v2",
    "gte-tiny",
    "e5-small-v2",
]

LOCAL_EDGE_DEVICE_SUMMARIZATION_MODELS = []

# Consumer Grade Models
LOCAL_CONSUMER_GRADE_RERANKING_MODELS = [
    "granite-embedding-125m-english",
    "stella_en_400m_v5",
    "mxbai-embed-large-v1",
    "gist-large-embedding-v0",
    "ember-v1",
    "bge-large-en-v1.5",
    "b1ade-embed",
    "mug-b-1.6",
    "uae-large-v1",
    "sf_model_e5",
    "gist-embedding-v0",
]

LOCAL_CONSUMER_GRADE_RETRIEVAL_MODELS = [
    "snowflake-arctic-embed-m-v1.5",
    "snowflake-arctic-embed-m",
    "snowflake-arctic-embed-m-long",
    "stella_en_400m_v5",
    "gte-large-en-v1.5",
    "snowflake-arctic-embed-l",
    "snowflake-arctic-embed-m-v2.0",
    "uae-large-v1",
    "mxbai-embed-large-v1",
    "modernbert-embed-large",
    "bge-large-en-v1.5",
]

LOCAL_CONSUMER_GRADE_STS_MODELS = [
    "b1ade-embed",
    "mxbai-embed-large-v1",
    "mug-b-1.6",
    "mxbai-embed-2d-large-v1",
    "gist-large-embedding-v0",
    "uae-large-v1",
    "stella_en_400m_v5",
    "sf_model_e5",
    "modernbert-embed-large",
    "gist-embedding-v0",
    "jina-embeddings-v2-base-es",
]

LOCAL_CONSUMER_GRADE_SUMMARIZATION_MODELS = [
    "mxbai-embed-large-v1",
    "stella-base-en-v2",
    "arabic-labse-matryoshka",
    "mug-b-1.6",
    "granite-embedding-278m-multilingual",
    "uae-large-v1",
    "b1ade-embed",
    "granite-embedding-125m-english",
    "instructor-large",
    "stella_en_400m_v5",
    "gte-large",
    "bge-large-en-v1.5",
    "sf_model_e5",
    "cde-small-v2",
    "jina-embeddings-v2-base-e",
]


LOCAL_EDGE_DEVICE_RERANKING_LLM_PRIORITY_ORDER = [
    "stella-base-en-v2",
    "gist-small-embedding-v0",
    "all-minilm-l12-v2",
    "all-minilm-l6-v2",
    "gist-all-minilm-l6-v2",
    "gte-small",
    "bge-small-en-v1.5",
    "medembed-small-v0.1",
    "noinstruct-small-embedding-v0",
]

LOCAL_CONSUMER_GRADE_RERANKING_LLM_PRIORITY_ORDER = [
    "granite-embedding-125m-english",
    "stella_en_400m_v5",
    "mxbai-embed-large-v1",
    "gist-large-embedding-v0",
    "ember-v1",
    "bge-large-en-v1.5",
    "b1ade-embed",
    "mug-b-1.6",
    "uae-large-v1",
    "sf_model_e5",
    "gist-embedding-v0",
]

LOCAL_GPU_RICH_RERANKING_LLM_PRIORITY_ORDER = [
    "gte-qwen2-7b-instruct",
    "stella_en_1.5b_v5",
    "gme-qwen2-vl-7b-instruct-q5_k_s-gguf",
    "gme-qwen2-vl-7b-instruct",
    "jasper_en_vision_language_v1",
    "lens-d8000",
    "lens-d4000",
    "speed-embedding-7b-instruct",
    "nv-embed-v2",
    "sfr-embedding-mistral",
]


# For the low-cost consumer devices, such as raspberry pi or an old tablet.
LOCAL_OFFICIAL_EDGE_DEVICE_LLM_PRIORITY_ORDER = [
    "ibm-granite/granite-3.1-2b-instruct",
    "ibm-granite/granite-3.0-2b-instruct",
    "google/gemma-2-2b-it",
    "microsoft/phi-2",
    "tiiuae/falcon3-1b-instruct",
    "qwen/qwen2.5-1.5b-instruct",
    "huggingfacetb/smollm2-1.7b-instruct",
    "ibm-granite/granite-3.0-2b-base",
    "qwen/qwen2-1.5b-instruct",
    "meta-llama/llama-3.2-1b-instruct",
    "qwen/qwen2.5-1.5b",
    "nvidia/hymba-1.5b-instruct",
    "ibm-granite/granite-3.1-2b-base",
    "stabilityai/stablelm-zephyr-3b",
    "internlm/internlm2_5-1_8b-chat",
    "google/flan-t5-xl",
    "internlm/internlm2-chat-1_8b",
    "qwen/qwen2-1.5b",
    "google/gemma-2-2b",
    "ibm-granite/granite-3.1-1b-a400m-instruct",
    "tiiuae/falcon3-1b-base",
    "cognitivecomputations/dolphin-2.9.4-gemma2-2b",
    "huggingfacetb/smollm2-1.7b",
]

LOCAL_EDGE_LLM_PRIORITY_ORDER = [
    "lgai-exaone/exaone-3.5-2.4b-instruct",
    "darkc0de/buddyglass_v0.3_xortron7methedupswitchedup",
    "allknowingroger/gemma2slerp2-2.6b",
    "lil-r/2_prymmal-ece-2b-slerp-v1",
    "lil-r/2_prymmal-ece-2b-slerp-v2",
    "allknowingroger/gemma2slerp1-2.6b",
]
LOCAL_OFFICIAL_CONSUMER_GRADE_LLM_PRIORITY_ORDER = [
    "microsoft/phi-3.5-mini-instruct",
    "microsoft/phi-3-mini-4k-instruct",
    "tiiuae/falcon3-3b-instruct",
    "microsoft/phi-3-mini-128k-instruct",
    "meta-llama/llama-3.2-3b-instruct",
    "qwen/qwen2.5-3b-instruct",
    "01-ai/yi-1.5-6b-chat",
    "nvidia/nemotron-mini-4b-instruct",
    "qwen/qwen2.5-3b",
    "en2.5-3b-instruct",
    "01-ai/yi-1.5-6b-chat",
]

LOCAL_CONSUMER_GRADE_LLM_PRIORITY_ORDER = [
    "dreadpoor/here_we_go_again-8b-slerp",
    "dreadpoor/asymmetric_linearity-8b-model_stock",
    "pjmixers-dev/llama-3.1-rombotiestest-8b",
    "pjmixers-dev/llama-3.1-rombotiestest2-8b",
    "dreadpoor/venn_1.2-8b-model_stock",
    "dreadpoor/elusive_dragon_heart-8b-linear",
    "jpacifico/chocolatine-3b-instruct-dpo-revised",
    "t145/zeus-8b-v2-orpo",
    "shreyash2010/uma-4x4b-instruct-v0.1",
    "meditsolutions/medit-mesh-3b-instruct",
    "maziyarpanahi/calme-2.1-phi3.5-4b",
    "unsloth/phi-3-mini-4k-instruct",
    "pjmixers-dev/qwen2.5-rombotiestest-7b",
    "jpacifico/chocolatine-3b-instruct-dpo-v1.2",
    "vonjack/phi-3-mini-4k-instruct-llamafied",
    "bamec66557/vicious_mesh-12b-union",
]

LOCAL_OFFICIAL_MID_RANGE_LLM_PRIORITY_ORDER = [
    "mlabonne/bigqwen2.5-echo-47b-instruct",
    "mistralai/mistral-small-instruct-2409",
    "qwen/qwen2-57b-a14b-instruct",
    "microsoft/phi-3-small-8k-instruct",
    "microsoft/phi-4",
    "cohereforai/aya-expanse-32b",
    "01-ai/yi-1.5-34b-chat-16k",
    "google/gemma-2-9b-it",
    "microsoft/phi-3-small-128k-instruct",
    "rhymes-ai/aria",
    "meta-llama/meta-llama-3.1-8b-instruct",
    "cognitivecomputations/dolphin-2.9.1-yi-1.5-34b",
    "01-ai/yi-1.5-9b-chat",
    "tiiuae/falcon3-mamba-7b-instruct",
    "tiiuae/falcon3-10b-base",
    "nousresearch/nous-hermes-2-mixtral-8x7b-dpo",
    "qwen/qwen1.5-32b-chat",
    "mlabonne/neuraldaredevil-8b-abliterated",
    "cognitivecomputations/dolphin-2.9.3-yi-1.5-34b-32k",
    "qwen/qwen1.5-32b",
    "qwen/qwen2.5-7b-instruct",
    "01-ai/yi-1.5-34b-32k",
]

# for the low-cost consumer devices, such as raspberry pi or an old tablet.
# for the mid-range devices, such as a high-end laptop or a high-end desktop.
LOCAL_MID_RANGE_LLM_PRIORITY_ORDER = [
    "rombodawg/rombos-llm-v2.5-qwen-32b",
    "sakalti/ultiima-32b",
    "maldv/qwentile2.5-32b-instruct",
    "saxo/linkbricks-horizon-ai-avengers-v5-32b",
    "fblgit/thebeagle-v2beta-32b-mgs",
    "hotmailuser/rombosbeagle-v2beta-mgs-32b",
    "sometimesanotion/lamarck-14b-v0.7-rc4",
    "sakalti/oxyge1-33b",
    "sakaltcommunity/novablast-preview",
    "sometimesanotion/lamarck-14b-v0.6",
    "hotmailuser/qwenslerp2-14b",
    "pankajmathur/orca_mini_v9_2_14b",
    "daemontatox/pathfinderai3.0",
    "sometimesanotion/qwen2.5-14b-vimarckoso-v3",
    "sthenno-com/miscii-14b-1225",
    "bunnycore/phi-4-model-stock",
]

# for the high-cost gpu-rich devices, such as a high-end laptop or a high-end desktop.
LOCAL_OFFICIAL_GPU_RICH_LLM_PRIORITY_ORDER = [
    "nousresearch/hermes-3-llama-3.1-70b",
    "meta-llama/llama-3.3-70b-instruct",
    "meta-llama/meta-llama-3-70b-instruct",
    "cognitivecomputations/dolphin-2.9.2-qwen2-72b",
    "qwen/qwen2-72b",
    "qwen/qwen2-math-72b-instruct",
    "abacusai/smaug-llama-3-70b-instruct-32k",
    "nvidia/llama-3.1-nemotron-70b-instruct-hf",
    "huggingfaceh4/zephyr-orpo-141b-a35b-v0.1",
    "mistralai/mixtral-8x22b-instruct-v0.1",
    "cohereforai/c4ai-command-r-plus-08-2024",
    "mlabonne/hermes-3-llama-3.1-70b-lorablated",
    "cohereforai/c4ai-command-r-plus",
    "qwen/qwen1.5-110b",
    "qwen/qwen2.5-math-72b-instruct",
    "abacusai/smaug-72b-v0.1",
    "qwen/qwen1.5-110b-chat",
    "deepseek-ai/deepseek-llm-67b-chat",
    "meta-llama/meta-llama-3-70b",
    "meta-llama/meta-llama-3.1-70b",
    "mistral-community/mixtral-8x22b-v0.3",
    "mistralai/mixtral-8x22b-v0.1",
    "databricks/dbrx-instruct",
    "cognitivecomputations/dolphin-2.9.1-llama-3-70b",
]

LOCAL_GPU_RICH_LLM_PRIORITY_ORDER = [
    "maziyarpanahi/calme-2.2-qwen2-72b",
    "dfurman/qwen2-72b-orpo-v0.1",
    "undi95/mg-finalmix-72b",
    "eva-unit-01/eva-qwen2.5-72b-v0.2",
    "sao10k/70b-l3.3-cirrus-x1",
    "qwen/qwen2-72b-instruct",
    "abacusai/dracarys-72b-instruct",
    "vagosolutions/llama-3.1-sauerkrautlm-70b-instruct",
    "anthracite-org/magnum-v1-72b",
    "alpindale/magnum-72b-v1",
    "daemontatox/llama3.3-70b-cognilink",
    "meta-llama/meta-llama-3.1-70b-instruct",
    "dnhkng/rys-llama3.1-large",
    "rombodawg/rombos-llm-v2.6-nemotron-70b",
    "anthracite-org/magnum-v2-72b",
    "allenai/llama-3.1-tulu-3-70b",
    "abacusai/smaug-qwen2-72b-instruct",
    "paulml/ece-ilab-q1",
    "allenai/llama-3.1-tulu-3-70b-dpo",
    "ksu-hw-sec/llama3.1-70b-sva-ft-1000",
    "nbeerbower/llama-3.1-nemotron-lorablated-70b",
    "maziyarpanahi/calme-2.3-llama3.1-70b",
]


if __name__ == "__main__":
    import litellm

    # Print all variables in the file
    model_cost = litellm.model_cost
    variables = [var for var in globals().keys() if not var.startswith("__")]
    for var_name in variables:
        this_list = globals()[var_name]
        if not isinstance(this_list, list):
            continue
        for item in this_list:
            print(item, model_cost[item])
        if isinstance(this_list, list):
            print(f"{var_name}:", json.dumps(this_list, indent=2))
        else:
            print(f"{var_name}:", this_list)
