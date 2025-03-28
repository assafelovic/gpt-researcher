from gpt_researcher.config.config import Config
from gpt_researcher.memory.embeddings import Memory
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

async def main():
    cfg = Config()
    
    print("Current embedding configuration:")
    print(f"EMBEDDING env var: {os.getenv('EMBEDDING', 'Not set')}")
    print(f"EMBEDDING_PROVIDER env var: {os.getenv('EMBEDDING_PROVIDER', 'Not set')}")
    
    try:
        # Check if embedding attributes are set
        print(f"cfg.embedding: {getattr(cfg, 'embedding', 'Not set')}")
        print(f"cfg.embedding_provider: {getattr(cfg, 'embedding_provider', 'Not set')}")
        print(f"cfg.embedding_model: {getattr(cfg, 'embedding_model', 'Not set')}")
        
        # If embedding_provider and embedding_model are not set, use defaults
        if not hasattr(cfg, 'embedding_provider') or not cfg.embedding_provider:
            print("Setting default embedding provider: openai")
            cfg.embedding_provider = "openai"
            
        if not hasattr(cfg, 'embedding_model') or not cfg.embedding_model:
            print("Setting default embedding model: text-embedding-3-small")
            cfg.embedding_model = "text-embedding-3-small"
        
        # Create a Memory instance using the configuration
        # Note: We're not passing embedding_kwargs since it's not properly initialized
        memory = Memory(
            embedding_provider=cfg.embedding_provider,
            model=cfg.embedding_model
        )
        
        # Get the embeddings object
        embeddings = memory.get_embeddings()
        
        # Test the embeddings with a simple text
        test_text = "This is a test sentence to verify embeddings are working correctly."
        embedding_vector = embeddings.embed_query(test_text)
        
        # Print information about the embedding
        print(f"\nSuccess! Generated embeddings using provider: {cfg.embedding_provider}")
        print(f"Model: {cfg.embedding_model}")
        print(f"Embedding vector length: {len(embedding_vector)}")
        print(f"First few values: {embedding_vector[:5]}")
        
    except Exception as e:
        print(f"Error testing embeddings: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())