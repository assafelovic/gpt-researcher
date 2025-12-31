#!/usr/bin/env python3
"""
Test script for LOGICAL_LLM configuration.
This script tests the logical_llm model independently to verify it works correctly.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gpt_researcher.utils.llm import create_chat_completion
from gpt_researcher.config.config import Config
import json
import json_repair


async def test_logical_llm():
    """Test the LOGICAL_LLM configuration."""
    print("=" * 80)
    print("Testing LOGICAL_LLM Configuration")
    print("=" * 80)
    
    # Load config
    config = Config()
    
    # Check if LOGICAL_LLM is configured
    logical_llm = getattr(config, 'logical_llm', None)
    logical_llm_provider = getattr(config, 'logical_llm_provider', None)
    logical_llm_model = getattr(config, 'logical_llm_model', None)
    
    print(f"\nLOGICAL_LLM configuration:")
    print(f"  - logical_llm: {logical_llm}")
    print(f"  - logical_llm_provider: {logical_llm_provider}")
    print(f"  - logical_llm_model: {logical_llm_model}")
    
    # Check Azure OpenAI endpoint configuration
    print(f"\nAzure OpenAI Configuration:")
    print(f"  - AZURE_OPENAI_ENDPOINT: {os.environ.get('AZURE_OPENAI_ENDPOINT', 'Not set')}")
    print(f"  - AZURE_OPENAI_API_KEY: {'Set' if os.environ.get('AZURE_OPENAI_API_KEY') else 'Not set'}")
    
    # Check if deployment-specific endpoint is configured
    # Code uses: deployment_name.replace('-', '_') which converts "gpt-5.2-chat" to "gpt_5.2_chat"
    # But .env might use "gpt_5_2_chat" (replacing both - and .)
    if logical_llm_model:
        # Try both formats
        deployment_name_underscore = logical_llm_model.replace('-', '_')  # gpt_5.2_chat
        deployment_name_all_underscore = logical_llm_model.replace('-', '_').replace('.', '_')  # gpt_5_2_chat
        
        # Check with underscore format (as code does)
        endpoint_key1 = f"AZURE_OPENAI_ENDPOINT_{deployment_name_underscore}"
        endpoint_key2 = f"AZURE_OPENAI_ENDPOINT_{deployment_name_all_underscore}"
        endpoint = os.environ.get(endpoint_key1) or os.environ.get(endpoint_key2)
        
        if endpoint:
            print(f"  - Found endpoint: {endpoint_key1 if os.environ.get(endpoint_key1) else endpoint_key2}")
            print(f"    Value: {endpoint}")
        else:
            print(f"  - {endpoint_key1}: Not set")
            print(f"  - {endpoint_key2}: Not set")
            print(f"    Will use default endpoint")
        
        # Check API version
        api_version_key1 = f"AZURE_OPENAI_API_VERSION_{deployment_name_underscore}"
        api_version_key2 = f"AZURE_OPENAI_API_VERSION_{deployment_name_all_underscore}"
        api_version = os.environ.get(api_version_key1) or os.environ.get(api_version_key2)
        
        if api_version:
            print(f"  - Found API version: {api_version_key1 if os.environ.get(api_version_key1) else api_version_key2}")
            print(f"    Value: {api_version}")
        else:
            print(f"  - {api_version_key1}: Not set")
            print(f"  - {api_version_key2}: Not set")
            print(f"    Will use default version")
        
        # Check API key
        api_key_key1 = f"AZURE_OPENAI_API_KEY_{deployment_name_underscore}"
        api_key_key2 = f"AZURE_OPENAI_API_KEY_{deployment_name_all_underscore}"
        api_key = os.environ.get(api_key_key1) or os.environ.get(api_key_key2)
        
        if api_key:
            print(f"  - Found API key: {api_key_key1 if os.environ.get(api_key_key1) else api_key_key2}")
            print(f"    Value: {'Set' if api_key else 'Not set'}")
        else:
            print(f"  - {api_key_key1}: Not set")
            print(f"  - {api_key_key2}: Not set")
            print(f"    Will use default API key")
    
    # Check fallback to SMART_LLM
    if not logical_llm or not logical_llm.strip():
        print("\n⚠️  LOGICAL_LLM not configured, using SMART_LLM as fallback")
        logical_llm_provider = config.smart_llm_provider
        logical_llm_model = config.smart_llm_model
        print(f"  - Using: {logical_llm_provider}:{logical_llm_model}")
    
    # Test prompt (similar to reorganize subtopics)
    test_prompt = """
You are an expert academic editor reorganizing a literature review report.

Main Topic: Relationship between graduate depression and supervisor management

Research Context:
Graduate students face significant mental health challenges, particularly depression, which is often influenced by their relationship with supervisors and management styles.

Current Subtopics with Headers:
Subtopic 1: Supervisor management styles
Headers:
- Authoritative vs. Supportive Styles
- Impact on Student Wellbeing

Subtopic 2: Relationship quality
Headers:
- Communication Patterns
- Trust and Support

Your task is to reorganize these subtopics and their headers into a logical structure for the final report.

Guidelines:
1. **Logical ordering**: Ensure subtopics follow a logical flow
2. **Merge related concepts**: If multiple subtopics cover similar themes, merge them
3. **Avoid fragmentation**: Group related concepts together
4. **Headers in different subtopics shouldn't overlap and keep concise**: Ensure headers across different subtopics are distinct and non-overlapping.

Output format (JSON):
{
  "reorganized_subtopics": [
    {
      "task": "Final subtopic task (may be merged or refined)",
      "headers": [
        {"text": "Header 1", "level": 3},
        {"text": "Header 2", "level": 3}
      ],
      "order": 1
    }
  ]
}

Important:
- Return ONLY the final subtopics list that the writer will use
- Ensure the 'headers' list contains dictionaries with 'text' and 'level' keys.
- The 'level' for headers should typically be 3 (###).
"""
    
    messages = [
        {"role": "user", "content": test_prompt}
    ]
    
    print("\n" + "=" * 80)
    print("Sending test request to LOGICAL_LLM...")
    print("=" * 80)
    
    try:
        # Some models (e.g., gpt-5.2-chat) don't support custom temperature
        # Remove temperature from llm_kwargs if present
        llm_kwargs = config.llm_kwargs.copy() if config.llm_kwargs else {}
        if "gpt-5.2" in logical_llm_model.lower():
            # Remove temperature from kwargs for gpt-5.2-chat (only supports default value 1)
            llm_kwargs.pop("temperature", None)
        
        completion_kwargs = {
            "model": logical_llm_model,
            "messages": messages,
            "max_tokens": config.smart_token_limit,
            "llm_provider": logical_llm_provider,
            "llm_kwargs": llm_kwargs,
        }
        
        # Only add temperature if model supports it (gpt-5.2-chat doesn't)
        if "gpt-5.2" not in logical_llm_model.lower():
            completion_kwargs["temperature"] = 0.3
        
        response = await create_chat_completion(**completion_kwargs)
        
        print("\n✅ Response received!")
        print(f"\nResponse type: {type(response)}")
        print(f"Response length: {len(response) if isinstance(response, str) else 'N/A'}")
        print("\n" + "-" * 80)
        print("Raw Response:")
        print("-" * 80)
        print(response[:500] + "..." if len(response) > 500 else response)
        
        # Try to parse JSON
        print("\n" + "-" * 80)
        print("Parsing JSON response...")
        print("-" * 80)
        
        try:
            # Try direct parsing
            result = json_repair.loads(response)
            print("✅ JSON parsed successfully!")
            print(f"\nParsed result type: {type(result)}")
            
            if isinstance(result, dict):
                reorganized_subtopics = result.get("reorganized_subtopics", [])
                print(f"\nFound {len(reorganized_subtopics)} reorganized subtopics:")
                for idx, subtopic in enumerate(reorganized_subtopics, 1):
                    task = subtopic.get("task", "")
                    headers = subtopic.get("headers", [])
                    order = subtopic.get("order", "N/A")
                    print(f"\n  {idx}. Order: {order}")
                    print(f"     Task: {task[:60]}...")
                    print(f"     Headers: {len(headers)}")
                    for h in headers[:3]:
                        print(f"       - {h.get('text', '')} (level: {h.get('level', 'N/A')})")
            
            print("\n" + "=" * 80)
            print("✅ Test completed successfully!")
            print("=" * 80)
            
        except Exception as parse_error:
            print(f"❌ Failed to parse JSON: {parse_error}")
            print("\nTrying to extract JSON block...")
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    result = json_repair.loads(json_match.group())
                    print("✅ Extracted and parsed JSON block successfully!")
                    print(f"Result: {result}")
                except Exception as e2:
                    print(f"❌ Failed to parse extracted JSON: {e2}")
            else:
                print("❌ No JSON block found in response")
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_logical_llm())
    sys.exit(0 if success else 1)

