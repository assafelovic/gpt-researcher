"""
Script to run GPT-Researcher queries and evaluate them for hallucination.
"""
import json
import logging
import random
import asyncio
import argparse
import os
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv

from gpt_researcher.agent import GPTResearcher
from gpt_researcher.utils.enum import ReportType, ReportSource, Tone
from gpt_researcher.utils.logging_config import get_json_handler

from .evaluate import HallucinationEvaluator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Default paths
DEFAULT_OUTPUT_DIR = "evals/hallucination_eval/results"
DEFAULT_QUERIES_FILE = "evals/hallucination_eval/inputs/search_queries.jsonl"

class ResearchEvaluator:
    """Runs GPT-Researcher queries and evaluates responses for hallucination."""
    
    def __init__(self, queries_file: str = DEFAULT_QUERIES_FILE):
        """
        Initialize the research evaluator.
        
        Args:
            queries_file: Path to JSONL file containing search queries
        """

        self.queries_file = Path(queries_file)
        self.hallucination_evaluator = HallucinationEvaluator()
        
    def load_queries(self, num_queries: Optional[int] = None) -> List[str]:
        """
        Load and optionally sample queries from the JSONL file.
        
        Args:
            num_queries: Optional number of queries to randomly sample
            
        Returns:
            List of query strings
        """
        queries = []
        with open(self.queries_file) as f:
            for line in f:
                data = json.loads(line.strip())
                queries.append(data["question"])
            
        if num_queries and num_queries < len(queries):
            return random.sample(queries, num_queries)
        return queries
        
    async def run_research(self, query: str) -> Dict:
        """
        Run a single query through GPT-Researcher.
        
        Args:
            query: The search query to research
            
        Returns:
            Dict containing research results and context
        """
        researcher = GPTResearcher(
            query=query,
            report_type=ReportType.ResearchReport.value,
            report_format="markdown",
            report_source=ReportSource.Web.value,
            tone=Tone.Objective,
            verbose=True
        )
        
        # Run research and get results
        research_result = await researcher.conduct_research()
        report = await researcher.write_report()
        
        return {
            "query": query,
            "report": report,
            "context": research_result,
        }
        
    def evaluate_research(
        self,
        research_data: Dict,
        output_dir: Optional[str] = None
    ) -> Dict:
        """
        Evaluate research results for hallucination.
        
        Args:
            research_data: Dict containing research results and context
            output_dir: Optional directory to save evaluation results
            
        Returns:
            Dict containing evaluation results
        """
        # Use default output directory if none provided
        if output_dir is None:
            output_dir = DEFAULT_OUTPUT_DIR
            
        # Use the final combined context as source text
        source_text = research_data.get("context", "")
        
        if not source_text:
            logger.warning("No source text found in research results - skipping evaluation")
            eval_result = {
                "input": research_data["query"],
                "output": research_data["report"],
                "source": "No source text available",
                "is_hallucination": None,
                "confidence_score": None,
                "reasoning": "Evaluation skipped - no source text available for verification"
            }
        else:
            # Evaluate the research report for hallucination
            eval_result = self.hallucination_evaluator.evaluate_response(
                model_output=research_data["report"],
                source_text=source_text
            )
        
        # Save to output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Append to evaluation records
        records_file = Path(output_dir) / "evaluation_records.jsonl"
        with open(records_file, "a") as f:
            f.write(json.dumps(eval_result) + "\n")
            
        return eval_result

async def main(num_queries: int = 5, output_dir: str = DEFAULT_OUTPUT_DIR):
    """
    Run evaluation on a sample of queries.
    
    Args:
        num_queries: Number of queries to evaluate
        output_dir: Directory to save results
    """
    evaluator = ResearchEvaluator()
    
    # Load and sample queries
    queries = evaluator.load_queries(num_queries)
    logger.info(f"Selected {len(queries)} queries for evaluation")
    
    # Run research and evaluation for each query
    all_results = []
    total_hallucinated = 0
    total_responses = 0
    total_evaluated = 0
    
    for query in queries:
        try:
            logger.info(f"Processing query: {query}")
            
            # Run research
            research_data = await evaluator.run_research(query)
            
            # Evaluate results
            eval_results = evaluator.evaluate_research(
                research_data,
                output_dir=output_dir
            )
            
            all_results.append(eval_results)
            
            # Update counters
            total_responses += 1
            if eval_results["is_hallucination"] is not None:
                total_evaluated += 1
                if eval_results["is_hallucination"]:
                    total_hallucinated += 1
                    
        except Exception as e:
            logger.error(f"Error processing query '{query}': {str(e)}")
            continue
            
    # Calculate hallucination rate
    hallucination_rate = (total_hallucinated / total_evaluated) if total_evaluated > 0 else None
    
    # Save aggregate results
    aggregate_results = {
        "total_queries": len(queries),
        "successful_queries": len(all_results),
        "total_responses": total_responses,
        "total_evaluated": total_evaluated,
        "total_hallucinated": total_hallucinated,
        "hallucination_rate": hallucination_rate,
        "results": all_results
    }
    
    aggregate_file = Path(output_dir) / "aggregate_results.json"
    with open(aggregate_file, "w") as f:
        json.dump(aggregate_results, f, indent=2)
    logger.info(f"Saved aggregate results to {aggregate_file}")
    
    # Print summary
    print("\n=== Evaluation Summary ===")
    print(f"Queries processed: {len(queries)}")
    print(f"Responses evaluated: {total_evaluated}")
    print(f"Responses skipped (no source text): {total_responses - total_evaluated}")
    if hallucination_rate is not None:
        print(f"Hallucination rate: {hallucination_rate * 100:.1f}%")
    else:
        print("No responses could be evaluated due to missing source text")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run GPT-Researcher evaluation")
    parser.add_argument("-n", "--num-queries", type=int, default=5,
                      help="Number of queries to evaluate")
    parser.add_argument("-o", "--output-dir", type=str, default=DEFAULT_OUTPUT_DIR,
                      help="Directory to save results")
    args = parser.parse_args()
    
    asyncio.run(main(args.num_queries, args.output_dir)) 