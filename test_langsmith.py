import logging

logging.basicConfig(level=logging.INFO)

import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define the prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. Please respond to the user's request only based on the given context."),
    ("user", "Question: {question}\nContext: {context}")
])

# Initialize the model and output parser
model = ChatOpenAI(model="gpt-3.5-turbo")
output_parser = StrOutputParser()

# Create the chain by piping the prompt, model, and output parser
chain = prompt | model | output_parser

# Define the question and context
question = "Can you summarize this morning's meetings?"
context = "During this morning's meeting, we solved all world conflict."

# Invoke the chain with the question and context
logging.info("Invoking the chain with question and context")
result = chain.invoke({"question": question, "context": context})

# Print the result
logging.info(f"Result: {result}")
print(result)
