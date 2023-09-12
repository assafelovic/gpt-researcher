from processing.text import split_text
from actions.web_scrape import scrape_text_with_selenium
from actions.web_search import web_search

from langchain.chat_models import ChatOpenAI, ChatAnthropic
from langchain.prompts import SystemMessagePromptTemplate, ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnableMap
import json
from langchain.schema.messages import SystemMessage
from agent.prompts import auto_agent_instructions
from datetime import date

summary_message = (
    '"""{chunk}""" Using the above text, answer the following'
        ' question: "{question}" -- if the question cannot be answered using the text,'
        " simply summarize the text in depth. "
        "Include all factual information, numbers, stats etc if available."
)
SUMMARY_PROMPT = ChatPromptTemplate.from_messages([
    ("user", summary_message)
])
search_message = (
    'Write 4 google search queries to search online that form an objective opinion from the following: "{question}"'\
    'You must respond with a list of strings in the following format: ["query 1", "query 2", "query 3", "query 4"]'
)

SEARCH_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "{agent_prompt}"),
    ("user", search_message)
])

AUTO_AGENT_INSTRUCTIONS = auto_agent_instructions()
CHOOSE_AGENT_PROMPT = ChatPromptTemplate.from_messages([
    SystemMessage(content=AUTO_AGENT_INSTRUCTIONS),
("user", "task: {task}")
])


summary_chain = SUMMARY_PROMPT | ChatOpenAI() | StrOutputParser()
chunk_and_combine = (lambda x: [{
    "question": x["question"],
    "chunk": chunk
} for chunk in split_text(x["text"])]) | summary_chain.map() | (lambda x: "\n".join(x))

recursive_summary_chain = {
    "question": lambda x: x["question"],
    "chunk": chunk_and_combine
} | summary_chain

scrape_and_summarize = {
    "question": lambda x: x["question"],
    "text": lambda x: scrape_text_with_selenium(x['url'])[1],
    "url": lambda x: x['url']
} | RunnableMap({
    "summary": recursive_summary_chain,
    "url": lambda x: x['url']
}) | (lambda x: f"Source Url: {x['url']}\nSummary: {x['summary']}")

multi_search = (lambda x: [
    {"url": url.get("href"), "question": x["question"]}
    for url in json.loads(web_search(x["question"]))
]) | scrape_and_summarize.map() | (lambda x: "\n".join(x))

search_query = SEARCH_PROMPT | ChatOpenAI() |  StrOutputParser() | json.loads
choose_agent = CHOOSE_AGENT_PROMPT | ChatOpenAI() | StrOutputParser() | json.loads

get_search_queries = {
    "question": lambda x: x,
    "agent_prompt": {"task": lambda x: x} | choose_agent | (lambda x: x["agent_role_prompt"])
} | search_query


class GPTResearcherActor:

    @property
    def runnable(self):
        return (
                get_search_queries
                | (lambda x: [{"question": q} for q in x])
                | multi_search.map()
                | (lambda x: "\n\n".join(x))
        )

