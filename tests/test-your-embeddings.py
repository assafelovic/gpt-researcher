from __future__ import annotations

import asyncio
import os

from dotenv import load_dotenv
from gpt_researcher.config.config import Config
from gpt_researcher.memory.embeddings import Memory

load_dotenv()

async def main():
    cfg = Config()

    print("Current embedding configuration:")
    print(f"EMBEDDING env var: {os.getenv('EMBEDDING', 'Not set')}")
    print(f"EMBEDDING_PROVIDER env var: {os.getenv('EMBEDDING_PROVIDER', 'Not set')}")

    try:
        # Check if embedding attributes are set
        print(f"cfg.EMBEDDING: {getattr(cfg, 'EMBEDDING', 'Not set')}")
        print(f"cfg.EMBEDDING_PROVIDER: {getattr(cfg, 'EMBEDDING_PROVIDER', 'Not set')}")
        print(f"cfg.EMBEDDING_MODEL: {getattr(cfg, 'EMBEDDING_MODEL', 'Not set')}")

        # If embedding_provider and embedding_model are not set, use defaults
        if not hasattr(cfg, "EMBEDDING_PROVIDER") or not cfg.EMBEDDING_PROVIDER:
            print("Setting default embedding provider: openai")
            cfg.EMBEDDING_PROVIDER = "openai"

        if not hasattr(cfg, "EMBEDDING_MODEL") or not cfg.EMBEDDING_MODEL:
            print("Setting default embedding model: text-embedding-3-small")
            cfg.EMBEDDING_MODEL = "text-embedding-3-small"

        # Create a Memory instance using the configuration
        # Note: We're not passing embedding_kwargs since it's not properly initialized
        memory = Memory(
            embedding_provider=cfg.EMBEDDING_PROVIDER,
            model=cfg.EMBEDDING_MODEL
        )

        # Get the embeddings object
        embeddings = memory.get_embeddings()

        # Test the embeddings with a simple text
        test_text: str = "This is a test sentence to verify embeddings are working correctly."
        embedding_vector: list[float] = embeddings.embed_query(test_text)

        # Print information about the embedding
        print(f"\nSuccess! Generated embeddings using provider: {cfg.EMBEDDING_PROVIDER}")
        print(f"Model: {cfg.EMBEDDING_MODEL}")
        print(f"Embedding vector length: {len(embedding_vector)}")
        print(f"First few values: {embedding_vector[:5]}")

    except Exception as e:
        print(f"Error testing embeddings: {e.__class__.__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())