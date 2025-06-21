"""
Evaluate model outputs for hallucination using the judges library.
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv
from judges.classifiers.hallucination import HaluEvalDocumentSummaryNonFactual

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HallucinationEvaluator:
    """Evaluates model outputs for hallucination using the judges library."""
    
    def __init__(self, model: str = "openai/gpt-4o"):
        """Initialize the hallucination evaluator."""
            
        self.summary_judge = HaluEvalDocumentSummaryNonFactual(model=model)
        
    def evaluate_response(self, input_text: str, model_output: str, source_text: str) -> Dict:
        """
        Evaluate a single model response for hallucination against source documents.
        
        Args:
            input_text: The input text/query
            model_output: The model's response to evaluate
            source_text: Source text to check summary against
            
        Returns:
            Dict containing evaluation results
        """
        try:
            # Use document summary evaluation
            judgment = self.summary_judge.judge(
                input=source_text,  # The source document
                output=model_output  # The summary to evaluate
            )
                
            return {
                "input": input_text,
                "output": model_output,
                "source": source_text,
                "is_hallucination": judgment.score > 0.5,
                "confidence_score": judgment.score,
                "reasoning": judgment.reasoning
            }
            
        except Exception as e:
            logger.error(f"Error evaluating response: {str(e)}")
            raise

def main():
    # Example test case
    input_text = "What is the capital of France?"
    model_output = "The capital of France is Paris, a city known for its rich history and culture."
    source_text = "Paris is the capital and largest city of France, located in the northern part of the country."
    
    evaluator = HallucinationEvaluator()
    result = evaluator.evaluate_response(
        input_text=input_text,
        model_output=model_output,
        source_text=source_text
    )
    
    # Print results
    print("\nEvaluation Results:")
    print(f"Input: {result['input']}")
    print(f"Output: {result['output']}")
    print(f"Source: {result['source']}")
    print(f"Hallucination: {'Yes' if result['is_hallucination'] else 'No'}")
    print(f"Confidence: {result['confidence_score']:.2f}")
    print(f"Reasoning: {result['reasoning']}")

if __name__ == "__main__":
    main() 