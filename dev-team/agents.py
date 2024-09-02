
# multi_agents/dev-team/agents.py
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

def create_github_fetcher_agent(tools):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an agent that fetches GitHub repository contents and stores them in a vector database."),
        ("human", "{input}"),
        ("human", "Fetch the contents of the GitHub repository and store them in the vector database.")
    ])
    llm = ChatOpenAI(model="gpt-4")
    agent = create_openai_functions_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools)

def create_filesystem_analyzer_agent(tools):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an agent that analyzes the filesystem structure and runs GPTResearcher."),
        ("human", "{input}"),
        ("human", "Analyze the filesystem structure and run GPTResearcher with the given query.")
    ])
    llm = ChatOpenAI(model="gpt-4")
    agent = create_openai_functions_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools)
