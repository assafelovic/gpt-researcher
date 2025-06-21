"""
Script to run GPT-Researcher queries and evaluate them for hallucination.
"""
import json
import logging
import asyncio
import argparse
import os
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv

from gpt_researcher.agent import GPTResearcher
from gpt_researcher.utils.enum import ReportType, ReportSource, Tone
from gpt_researcher.utils.logging_config import get_json_handler

from evaluate import HallucinationEvaluator

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

class ResearchEvaluator:
    """Runs GPT-Researcher queries and evaluates responses for hallucination."""
    
    def __init__(self):
        """Initialize the research evaluator."""
        self.hallucination_evaluator = HallucinationEvaluator()
        
    async def run_research(self, query: str) -> Dict:
        """
        Run a single query through GPT-Researcher.
        
        Args:
            query: The search query to research
            
        Returns:
            Dict containing research results and context
        """
        logger.info(f"Starting research for query: {query}")
        
        researcher = GPTResearcher(
            query=query,
            report_type=ReportType.ResearchReport.value,
            report_format="markdown",
            report_source=ReportSource.Web.value,
            tone=Tone.Objective,
            verbose=True
        )
        
        # Run research and get results
        logger.info("Conducting research...")
        research_result = await researcher.conduct_research()
        
        logger.info("Generating report...")
        report = await researcher.write_report()
        
        logger.info("Research complete")
        return {
            "query": query,
            "report": report,
            "context": research_result,
        }
        
    def evaluate_research(
        self,
        research_data: Dict,
        output_dir: str = DEFAULT_OUTPUT_DIR
    ) -> Dict:
        """
        Evaluate research results for hallucination.
        
        Args:
            research_data: Dict containing research results and context
            output_dir: Directory to save evaluation results
            
        Returns:
            Dict containing evaluation results
        """
        logger.info("Starting hallucination evaluation")
        
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
            logger.info("Evaluating research report")
            eval_result = self.hallucination_evaluator.evaluate_response(
                input_text=research_data["query"],
                model_output=research_data["report"],
                source_text=source_text
            )
        
        # Save to output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Save evaluation record
        records_file = Path(output_dir) / "evaluation_record.json"
        with open(records_file, "w") as f:
            json.dump(eval_result, f, indent=2)
        logger.info(f"Saved evaluation results to {records_file}")
            
        return eval_result

async def main(query: str, output_dir: str = DEFAULT_OUTPUT_DIR):
    """
    Run evaluation on a single query.
    
    Args:
        query: The query to evaluate
        output_dir: Directory to save results
    """
    evaluator = ResearchEvaluator()
    
    try:
        logger.info(f"Starting evaluation process for query: {query}")
        
        # Run research
        research_data = await evaluator.run_research(query)
        
        # Evaluate results
        eval_results = evaluator.evaluate_research(
            research_data,
            output_dir=output_dir
        )
        
        # Print summary
        print("\n=== Evaluation Summary ===")
        print(f"Query: {query}")
        print(f"Hallucination: {'Yes' if eval_results['is_hallucination'] else 'No'}")
        print(f"Confidence Score: {eval_results['confidence_score']:.2f}")
        print(f"Reasoning: {eval_results['reasoning']}")
        print(f"\nDetailed results saved to: {output_dir}/evaluation_record.json")
        
        logger.info("Evaluation process complete")
        
    except Exception as e:
        logger.error(f"Error processing query '{query}': {str(e)}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run GPT-Researcher evaluation")
    parser.add_argument("query", type=str,
                      help="Query to evaluate")
    parser.add_argument("-o", "--output-dir", type=str, default=DEFAULT_OUTPUT_DIR,
                      help="Directory to save results")
    args = parser.parse_args()
    
    asyncio.run(main(args.query, args.output_dir)) 