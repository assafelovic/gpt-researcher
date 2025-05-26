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
Your job is to look at a question, a gold target, and a predicted answer, and then assign a grade of either ["CORRECT", "INCORRECT", "NOT_ATTEMPTED"].
First, I will give examples of each grade, and then you will grade a new example.


The following are examples of CORRECT predicted answers.
```
Question: What are the names of Barack Obama's children?
Gold target: Malia Obama and Sasha Obama
Predicted answer 1: sasha and malia obama
Predicted answer 2: most people would say Malia and Sasha, but I'm not sure and would have to double check
Predicted answer 3: Barack Obama has two daughters. Their names are Malia Ann and Natasha Marian, but they are commonly referred to as Malia Obama and Sasha Obama. Malia was born on July 4, 1998, and Sasha was born on June 10, 2001.
```
These predicted answers are all CORRECT because:
    - They fully contain the important information in the gold target.
    - They do not contain any information that contradicts the gold target.
    - Only semantic meaning matters; capitalization, punctuation, grammar, and order don't matter.
    - Hedging and guessing are permissible, provided that the gold target is fully included and the response contains no incorrect information or contradictions.


The following are examples of INCORRECT predicted answers.
```
Question: What are the names of Barack Obama's children?
Gold target: Malia and Sasha
Predicted answer 1: Malia.
Predicted answer 2: Malia, Sasha, and Susan.
Predicted answer 3: Barack Obama does not have any children.
Predicted answer 4: I think it's either Malia and Sasha. Or it could be Malia and Jackie. Or it could be Joey and Malia.
Predicted answer 4: While I don't know their exact names, I can tell you that Barack Obama has three children.
Predicted answer 5: It's possible you may mean Betsy and Olivia. However, you should clarify further details with updated references if necessary. Is that the correct answer?
Predicted answer 6: It may be the case that Obama's child is named James. However, it's recommended to confirm the most accurate and updated information since this could change over time. This model may not always reflect the most current information.
```
These predicted answers are all INCORRECT because:
    - A factual statement in the answer contradicts the gold target. Incorrect statements that have some hedging (e.g., "it is possible that", "although i'm not sure, i think") are also considered incorrect.


The following are examples of NOT_ATTEMPTED predicted answers.
```
Question: What are the names of Barack Obama's children?
Gold target: Malia and Sasha
Predicted answer 1: I don't know.
Predicted answer 2: I need more context about which Obama you are talking about.
Predicted answer 3: Without researching the web, I cannot answer this question. However, I can tell you that Barack Obama has two children.
Predicted answer 4: Barack Obama has two children. I know that one of them is Malia, but I'm not sure about the other one.
```
These predicted answers are all NOT_ATTEMPTED because:
    - The important information in the gold target is not included in the answer.
    - No statements in the answer contradict the gold target.


Also note the following things:
- For grading questions where the gold target is a number, the predicted answer needs to be correct to the last significant figure in the gold answer. For example, consider a question "How many citations does the Transformer Paper have?" with gold target "120k". 
    - Predicted answers "120k", "124k", and 115k" are all CORRECT. 
    - Predicted answers "100k" and "113k" are INCORRECT. 
    - Predicted answers "around 100k" and "more than 50k" are considered NOT_ATTEMPTED because they neither confirm nor contradict the gold target.
- The gold target may contain more information than the question. In such cases, the predicted answer only needs to contain the information that is in the question.
    - For example, consider the question "What episode did Derek and Meredith get legally married in Grey's Anatomy?" with gold target "Season 7, Episode 20: White Wedding". Either "Season 7, Episode 20" or "White Wedding" would be considered a CORRECT answer.
- Do not punish predicted answers if they omit information that would be clearly inferred from the question.
    - For example, consider the question "What city is OpenAI headquartered in?" and the gold target "San Francisco, California". The predicted answer "San Francisco" would be considered CORRECT, even though it does not include "California".
    - Consider the question "What award did A pretrainer's guide to training data: Measuring the effects of data age, domain coverage, quality, & toxicity win at NAACL '24?", the gold target is "Outstanding Paper Award". The predicted answer "Outstanding Paper" would be considered CORRECT, because "award" is presumed in the question.
    - For the question "What is the height of Jason Wei in meters?", the gold target is "1.73 m". The predicted answer "1.75" would be considered CORRECT, because meters is specified in the question.
    - For the question "What is the name of Barack Obama's wife?", the gold target is "Michelle Obama". The predicted answer "Michelle" would be considered CORRECT, because the last name can be presumed.
- Do not punish for typos in people's name if it's clearly the same name. 
    - For example, if the gold target is "Hyung Won Chung", you can consider the following predicted answers as correct: "Hyoong Won Choong", "Hyungwon Chung", or "Hyun Won Chung".


Here is a new example. Simply reply with either CORRECT, INCORRECT, NOT ATTEMPTED. Don't apologize or correct yourself if there was a mistake; we are just trying to grade the answer.
```
Question: {question}
Gold target: {target}
Predicted answer: {predicted_answer}
```

Grade the predicted answer of this new question as one of:
A: CORRECT
B: INCORRECT
C: NOT_ATTEMPTED

Just return the letters "A", "B", or "C", with no text around it.
""".strip()


CHOICE_LETTERS = ["A", "B", "C"]
CHOICE_STRINGS = ["CORRECT", "INCORRECT", "NOT_ATTEMPTED"]
CHOICE_LETTER_TO_STRING = dict(zip(CHOICE_LETTERS, CHOICE_STRINGS))


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
        
        # Calculate metrics based on grade
        metrics = {
            "grade": grade,
            "is_correct": 1.0 if grade == "CORRECT" else 0.0,
            "is_incorrect": 1.0 if grade == "INCORRECT" else 0.0,
            "is_not_attempted": 1.0 if grade == "NOT_ATTEMPTED" else 0.0
        }
        
        return {
            "score": metrics["is_correct"],  # Score is 1.0 for CORRECT, 0.0 otherwise
            "metrics": {"grade": grade},
            "html": "",
            "convo": [{"role": "evaluator", "content": problem},
                      {"role": "evaluator", "content": correct_answer},
                      {"role": "agent", "content": predicted_answer}]
        }

    def grade_response(self, question: str, correct_answer: str, model_answer: str) -> str:
        """Grade a single response using the grader model."""
        print("\n=== Grading Details ===")
        print(f"Question: {question}")
        print(f"Gold target: {correct_answer}")
        print(f"Predicted answer: {model_answer}")
        
        prompt = GRADER_TEMPLATE.format(
            question=question,
            target=correct_answer,
            predicted_answer=model_answer
        )
        
        messages = [{"role": "user", "content": prompt}]
        response = self.grader_model.invoke(messages)
        response_text = response.content.strip()
        
        # Convert letter response to grade string
        if response_text in CHOICE_LETTERS:
            grade = CHOICE_LETTER_TO_STRING[response_text]
        else:
            # Fallback for direct string responses
            for grade in CHOICE_STRINGS:
                if grade in response_text:
                    return grade
            grade = "NOT_ATTEMPTED"  # Default if no grade found
            
        print(f"\nGrade: {grade}")
        return grade 