"""
SimpleQA: Measuring short-form factuality in large language models
Adapted for GPT-Researcher from OpenAI's simple-evals
"""

import os
import re
import json
import pandas
import random
from typing import Dict, List, Any
from langchain_openai import ChatOpenAI

GRADER_TEMPLATE = """
Question: {question}
Gold target: {target}
Predicted answer: {predicted_answer}

Grade the predicted answer as CORRECT or INCORRECT compared to the gold target. Be strict about accuracy but allow for minor differences in formatting or phrasing.
"""

class SimpleQAEval:
    def __init__(self, grader_model, num_examples=1):
        """Initialize the evaluator with a grader model and number of examples."""
        self.grader_model = grader_model
        
        # Load all examples from CSV
        csv_url = "https://openaipublic.blob.core.windows.net/simple-evals/simple_qa_test_set.csv"
        df = pandas.read_csv(csv_url)
        all_examples = df.to_dict('records')
        
        # Randomly select num_examples without replacement
        if num_examples > len(all_examples):
            print(f"Warning: Requested {num_examples} examples but only {len(all_examples)} available")
            num_examples = len(all_examples)
            
        self.examples = random.sample(all_examples, num_examples)
        print(f"Selected {num_examples} random examples for evaluation")

    def evaluate_example(self, example: dict) -> dict:
        """Evaluate a single example."""
        problem = example.get("problem") or example.get("question")
        correct_answer = example["answer"]
        predicted_answer = example["predicted"]
        
        grade = self.grade_response(problem, correct_answer, predicted_answer)
        score = 1.0 if grade == "CORRECT" else 0.0
        
        return {
            "score": score,
            "metrics": {"grade": grade},
            "html": "",
            "convo": [{"role": "user", "content": problem},
                      {"role": "assistant", "content": predicted_answer}]
        }

    def grade_response(self, question: str, correct_answer: str, model_answer: str) -> str:
        """Grade a single response using the grader model."""
        print("\n=== Grading Details ===")
        print(f"Question: {question}")
        print(f"Gold target: {correct_answer}")
        print(f"Predicted answer: {model_answer}")
        
        prompt = GRADER_TEMPLATE.replace("{question}", question)
        prompt = prompt.replace("{target}", correct_answer)
        prompt = prompt.replace("{predicted_answer}", model_answer)
        
        messages = [{"role": "user", "content": prompt}]
        response = self.grader_model.invoke(messages)
        response_text = response.content
        
        print("\n=== Grader Response ===")
        print(response_text)
        
        # Extract CORRECT or INCORRECT
        if "CORRECT" in response_text:
            return "CORRECT"
        elif "INCORRECT" in response_text:
            return "INCORRECT"
        else:
            return "NOT_ATTEMPTED" 