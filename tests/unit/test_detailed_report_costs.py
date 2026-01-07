import pytest
import sys
import os
from unittest.mock import MagicMock, AsyncMock, patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from gpt_researcher.agent import GPTResearcher
from backend.report_type.detailed_report.detailed_report import DetailedReport
from gpt_researcher.utils.costs import calculate_llm_cost

@pytest.fixture
def mock_env_pricing():
    # Set fixed pricing for test predictability
    env = {
        "MODEL_PRICING_PER_1M_JSON": '{"gpt-4": {"input": 10.0, "output": 30.0}}',
        "OPENAI_API_KEY": "sk-mock" 
    }
    with patch.dict(os.environ, env):
        yield

@patch("gpt_researcher.agent.Memory")
@patch("gpt_researcher.agent.VectorStoreWrapper")
@patch("gpt_researcher.agent.ContextManager")
@patch("gpt_researcher.utils.llm.create_chat_completion", new_callable=AsyncMock)
@patch("gpt_researcher.actions.query_processing.create_chat_completion", new_callable=AsyncMock)
@patch("gpt_researcher.actions.report_generation.create_chat_completion", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_detailed_report_full_cost_simulation(
    mock_create_chat_report, mock_create_chat_query, mock_create_chat_utils, 
    mock_context_manager, mock_vector_store, mock_memory, mock_env_pricing
):
    """
    Simulate a full Detailed Report workflow and verify cost accumulation.
    We mock create_chat_completion to return fixed responses and trigger cost callbacks.
    """
    # 1. Setup Data
    INPUT_TOKENS = 1000
    OUTPUT_TOKENS = 500
    COST_PER_CALL = (1000/1e6 * 10.0) + (500/1e6 * 30.0) # $0.01 + $0.015 = $0.025
    
    # Configure mock LLM to call the cost_callback
    async def side_effect(messages, *args, cost_callback=None, **kwargs):
        if cost_callback:
            # Simulate usage
            token_usage = {
                "prompt_tokens": INPUT_TOKENS,
                "completion_tokens": OUTPUT_TOKENS,
                "total_tokens": INPUT_TOKENS + OUTPUT_TOKENS
            }
            # Manually calculate mock cost (since create_chat_completion does this internally)
            # In a real run, create_chat_completion calls calculate_llm_cost.
            # Here we simulate the callback invocation.
            cost = calculate_llm_cost(INPUT_TOKENS, OUTPUT_TOKENS, "gpt-4")
            
            # Using the signature expected by cost_callback (supports token_usage kwarg)
            try:
                cost_callback(cost, token_usage=token_usage)
            except TypeError:
                cost_callback(cost)
                
        return "Mocked LLM Response"

    # Apply side effect to all mocks
    mock_create_chat_report.side_effect = side_effect
    mock_create_chat_query.side_effect = side_effect
    mock_create_chat_utils.side_effect = side_effect
    
    # 2. Initialize Researcher
    researcher = GPTResearcher(query="Simulated Task", report_type="detailed_report")
    # Mock specific internals to avoid network calls
    researcher.cfg.smart_llm_model = "gpt-4"
    researcher.cfg.strategic_llm_model = "gpt-4"
    researcher.scraper_manager = AsyncMock()
    researcher.scraper_manager.browse_urls = AsyncMock(return_value=[])
    
    # Mock internal methods that might make network calls
    researcher.get_subtopics = AsyncMock(return_value={
        "subtopics": [
            {"task": "subtopic 1", "web_search": True},
            {"task": "subtopic 2", "web_search": True}
        ]
    })
    # Simulating simple retrieval results
    mock_context_manager.return_value.get_context_by_search.return_value = "Mock Context"
    
    # 3. Initialize DetailedReport
    # DetailedReport instantiates GPTResearcher internally.
    report_engine = DetailedReport(
        query="Simulated Task",
        report_type="detailed_report",
        report_source="web",
        tone="Formal"
    )
    
    # Get the researcher instance created by DetailedReport
    researcher = report_engine.gpt_researcher
    
    # Configure the internal researcher instance with mocks to prevent network calls
    researcher.cfg.smart_llm_model = "gpt-4"
    researcher.cfg.strategic_llm_model = "gpt-4"
    researcher.scraper_manager = AsyncMock()
    researcher.scraper_manager.browse_urls = AsyncMock(return_value=[])
    
    # Mock aggregation methods to avoid complex logic/network
    researcher.get_subtopics = AsyncMock(return_value={
        "subtopics": [
            {"task": "subtopic 1", "web_search": True},
            {"task": "subtopic 2", "web_search": True}
        ]
    })
    
    # Mock ContextManager on the instance if it wasn't replaced by global patch
    # (Global patch replaces the class, so new instances depend on the mock class)
    # Ensure get_context_by_search returns something
    researcher.context_manager.get_context_by_search = AsyncMock(return_value="Mock Context")

    from gpt_researcher.actions.query_processing import plan_research_outline

    # 4. Mock the workflow steps of DetailedReport to control execution count
    # Since DetailedReport.run() is complex, we will invoke the researcher methods directly
    # that DetailedReport WOULD call, to verify aggregation.
    
    # 4a. Plan Research (Strategic Agent)
    # create_chat_completion called 1 time
    # Note: plan_research_outline is an action, not a method of GPTResearcher
    await plan_research_outline(
        query=researcher.query,
        search_results=[],
        agent_role_prompt=researcher.role,
        cfg=researcher.cfg,
        parent_query=researcher.parent_query,
        report_type=researcher.report_type,
        cost_callback=researcher.add_costs
    )
    
    # 4b. Conduct Research on Subtopics
    # If we have 2 subtopics, each conducts research (context generation)
    # For each subtopic: get_context -> multiple LLM calls? 
    # Let's simplify: Mock conduct_research to just make 1 LLM call per subtopic
    # by mocking the underlying context aggregation if possible.
    # Instead, we'll verify that direct calls to methods used in DetailedReport accumulate.
    
    # Reset costs (just in case init caused some)
    # researcher.research_costs = 0.0
    # researcher.token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    
    # Simulate: Introduction Generation
    await researcher.write_introduction()
    # Expected: 1 call. Cost = 0.025
    
    # Simulate: 2 Subtopic Reports
    # Subtopic 1
    await researcher.write_report(existing_headers=[], relevant_written_contents=[]) 
    # Subtopic 2
    await researcher.write_report(existing_headers=[], relevant_written_contents=[])
    # Expected: +2 calls. Total 3 calls. Cost = 0.075
    
    # Simulate: Conclusion Generation
    await researcher.write_report_conclusion(report_body="...")
    # Expected: +1 call. Total 4 calls. Cost = 0.10
    
    # 5. Assertions
    expected_calls = 5 # 1 plan + 1 intro + 2 subtopics + 1 conclusion
    expected_cost = expected_calls * COST_PER_CALL
    
    # print(f"Final Costs: {researcher.get_costs()}")
    
    total_calls = (
        mock_create_chat_report.call_count + 
        mock_create_chat_query.call_count + 
        mock_create_chat_utils.call_count
    )
    assert total_calls >= expected_calls
    # Use approximate equality for floating point
    assert abs(researcher.get_costs() - expected_cost) < 1e-6
    assert researcher.token_usage["total_tokens"] == expected_calls * (INPUT_TOKENS + OUTPUT_TOKENS)

