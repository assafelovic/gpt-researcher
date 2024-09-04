import os
from langgraph.graph import StateGraph, END
from dev_team.agents import GithubAgent, RepoAnalyzerAgent, WebSearchAgent, RubberDuckerAgent, TechLeadAgent

import asyncio

async def run_dev_team_flow(repo_url: str, query: str):
    flow = DevTeamFlow(github_token=os.environ.get("GITHUB_TOKEN"), repo_name=repo_url)
    response = await flow.run_flow(query)
    return response

from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class AgentState(TypedDict):
    query: str
    github_data: dict
    repo_analysis: str
    web_search_results: list
    rubber_duck_thoughts: str
    tech_lead_review: str
    vector_store: dict
    repo_name: str
    model: str

class DevTeamFlow:
    def __init__(self, github_token, repo_name):
        self.github_agent = GithubAgent(github_token=os.environ.get("GITHUB_TOKEN"), repo_name='assafelovic/gpt-researcher')
        self.repo_analyzer_agent = RepoAnalyzerAgent()
        self.web_search_agent = WebSearchAgent(repo_name=repo_name)
        self.rubber_ducker_agent = RubberDuckerAgent()
        self.tech_lead_agent = TechLeadAgent()

    def init_flow(self):
        workflow = StateGraph(AgentState)

        workflow.add_node("fetch_github", self.github_agent.fetch_repo_data)
        workflow.add_node("analyze_repo", self.repo_analyzer_agent.analyze_repo)
        workflow.add_node("web_search", self.web_search_agent.search_web)
        workflow.add_node("rubber_duck", self.rubber_ducker_agent.think_aloud)
        workflow.add_node("tech_lead", self.tech_lead_agent.review_and_compose)

        workflow.add_edge('fetch_github', 'analyze_repo')
        workflow.add_edge('analyze_repo', 'web_search')
        workflow.add_edge('web_search', 'rubber_duck')
        workflow.add_edge('rubber_duck', 'tech_lead')

        workflow.set_entry_point("fetch_github")
        workflow.add_edge('tech_lead', END)

        return workflow

    async def run_flow(self, query):
        # vector_store = self.github_agent.get_vector_store()
        # self.repo_analyzer_agent = RepoAnalyzerAgent(vector_store)

        workflow = self.init_flow()
        chain = workflow.compile()

        initial_state = AgentState(
            query=query,
            model="gpt-4o",
            github_data={},
            repo_analysis="",
            web_search_results=[],
            rubber_duck_thoughts="",
            tech_lead_review=""
        )

        result = await chain.ainvoke(initial_state)
        return result