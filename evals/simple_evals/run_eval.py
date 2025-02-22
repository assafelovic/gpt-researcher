import asyncio
import os
import argparse
from typing import Callable, List, TypeVar
from tqdm import tqdm
from dotenv import load_dotenv
from gpt_researcher.agent import GPTResearcher
from gpt_researcher.utils.enum import ReportType, ReportSource, Tone
from evals.simple_evals.simpleqa_eval import SimpleQAEval
from langchain_openai import ChatOpenAI
import json

# Type variables for generic function
T = TypeVar('T')
R = TypeVar('R')

def map_with_progress(fn: Callable[[T], R], items: List[T]) -> List[R]:
    """Map function over items with progress bar."""
    return [fn(item) for item in tqdm(items)]

# Load environment variables from .env file
load_dotenv()

# Verify all required environment variables
required_env_vars = ["OPENAI_API_KEY", "TAVILY_API_KEY", "LANGCHAIN_API_KEY"]
for var in required_env_vars:
    if not os.getenv(var):
        raise ValueError(f"{var} not found in environment variables")

async def evaluate_single_query(query: str, evaluator: SimpleQAEval) -> dict:
    """Run a single evaluation query and return results"""
    print(f"\nEvaluating query: {query}")
    
    # Run the researcher and get report
    researcher = GPTResearcher(
        query=query,
        report_type=ReportType.ResearchReport.value,
        report_format="markdown",
        report_source=ReportSource.Web.value,
        tone=Tone.Objective,
        verbose=True
    )
    context = await researcher.conduct_research()
    report = await researcher.write_report()
    
    # Get the correct answer and evaluate
    example = next(ex for ex in evaluator.examples if ex['problem'] == query)
    correct_answer = example['answer']
    
    eval_result = evaluator.evaluate_example({
        "problem": query,
        "answer": correct_answer,
        "predicted": report
    })
    
    result = {
        'query': query,
        'context_length': len(context),
        'report_length': len(report),
        'cost': researcher.get_costs(),
        'sources': researcher.get_source_urls(),
        'evaluation_score': eval_result["score"],
        'evaluation_grade': eval_result["metrics"]["grade"]
    }
    
    # Print just the essential info
    print(f"✓ Completed research and evaluation")
    print(f"  - Sources found: {len(result['sources'])}")
    print(f"  - Evaluation grade: {result['evaluation_grade']}")
    print(f"  - Cost: ${result['cost']:.4f}")
    
    return result

async def main(num_examples: int):
    if num_examples < 1:
        raise ValueError("num_examples must be at least 1")
        
    try:
        # Initialize the evaluator with specified number of examples
        grader_model = ChatOpenAI(
            temperature=0, 
            model_name="gpt-4-turbo",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        evaluator = SimpleQAEval(grader_model=grader_model, num_examples=num_examples)
        
        if not evaluator.examples:
            raise ValueError("No examples loaded in evaluator")
        
        print(f"Starting GPT-Researcher evaluation with {num_examples} test queries...")
        
        results = []
        for example in evaluator.examples:
            if 'problem' not in example:
                print(f"Warning: Skipping example without 'problem' key: {example}")
                continue
                
            query = example['problem']
            print(f"\nEvaluating query: {query}")
            try:
                result = await evaluate_single_query(query, evaluator)
                results.append(result)
                
                print(f"✓ Completed research and evaluation")
                print(f"  - Sources found: {len(result['sources'])}")
                print(f"  - Context length: {result['context_length']}")
                print(f"  - Report length: {result['report_length']}")
                print(f"  - Evaluation score: {result['evaluation_score']}")
                print(f"  - Evaluation grade: {result['evaluation_grade']}")
                print(f"  - Cost: ${result['cost']:.4f}")
                
            except Exception as e:
                print(f"✗ Error evaluating query: {str(e)}")
                results.append({
                    'query': query,
                    'error': str(e)
                })
        
        if not results:
            raise ValueError("No results generated")
            
        # Print summary for any number of examples
        if num_examples > 0:  # Changed from > 1
            print("\n=== Evaluation Summary ===")
            print(f"Total queries tested: {len(evaluator.examples)}")
            successful = len([r for r in results if 'error' not in r])
            print(f"Successful queries: {successful}")
            print(f"Failed queries: {len(evaluator.examples) - successful}")
            
            if successful > 0:
                # Count the different grades
                correct = sum(1 for r in results if r.get('evaluation_grade') == "CORRECT")
                incorrect = sum(1 for r in results if r.get('evaluation_grade') == "INCORRECT")
                not_attempted = sum(1 for r in results if r.get('evaluation_grade') == "NOT_ATTEMPTED")
                
                print("\n=== AGGREGATE METRICS ===")
                metrics = {
                    "correct_rate": correct / successful,
                    "incorrect_rate": incorrect / successful,
                    "not_attempted_rate": not_attempted / successful,
                    "answer_rate": (correct + incorrect) / successful,
                }
                
                # Debug output
                print("\nDebug counts:")
                print(f"Total successful: {successful}")
                print(f"CORRECT: {correct}")
                print(f"INCORRECT: {incorrect}")
                print(f"NOT_ATTEMPTED: {not_attempted}")
                
                # Calculate accuracy and F1
                metrics["accuracy"] = (
                    correct / (correct + incorrect)  # Accuracy among attempted answers
                    if (correct + incorrect) > 0
                    else 0
                )
                
                # Precision = correct / attempted
                precision = correct / (correct + incorrect) if (correct + incorrect) > 0 else 0
                
                # Recall = correct / total
                recall = correct / successful if successful > 0 else 0
                
                # F1 = 2 * (precision * recall) / (precision + recall)
                metrics["f1"] = (
                    2 * (precision * recall) / (precision + recall)
                    if (precision + recall) > 0
                    else 0
                )
                
                print(json.dumps(metrics, indent=2))
                print("========================")
                print(f"Accuracy: {metrics['accuracy']:.3f}")
                print(f"F1 Score: {metrics['f1']:.3f}")
                
                # Print cost metrics
                total_cost = sum(r['cost'] for r in results if 'error' not in r)
                print(f"\nTotal cost: ${total_cost:.4f}")
                print(f"Average cost per query: ${total_cost/successful:.4f}")
                
    except Exception as e:
        print(f"Fatal error in main: {str(e)}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run GPT-Researcher evaluation')
    parser.add_argument('--num_examples', type=int, default=1,
                      help='Number of examples to evaluate. Default is 1 example.')
    args = parser.parse_args()
    
    try:
        asyncio.run(main(args.num_examples))
    except KeyboardInterrupt:
        print("\nEvaluation interrupted by user")
    except Exception as e:
        print(f"Fatal error: {str(e)}")