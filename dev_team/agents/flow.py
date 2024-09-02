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

class DevTeamFlow:
    def __init__(self, github_token, repo_name):
        self.github_agent = GithubAgent(github_token=os.environ.get("GITHUB_TOKEN"), repo_name='elishakay/gpt-researcher')
        self.repo_analyzer_agent = RepoAnalyzerAgent()
        self.web_search_agent = WebSearchAgent()
        self.rubber_ducker_agent = RubberDuckerAgent()
        self.tech_lead_agent = TechLeadAgent()

    def init_flow(self):
        workflow = StateGraph(AgentState)

        workflow.add_node("fetch_github", lambda state: self.github_agent.fetch_repo_data(state))
        workflow.add_node("analyze_repo", lambda state: {**state, "repo_analysis": self.repo_analyzer_agent.analyze_repo(state)})
        workflow.add_node("web_search", lambda state: {**state, "web_search_results": self.web_search_agent.search_web(state)})
        workflow.add_node("rubber_duck", lambda state: {**state, "rubber_duck_thoughts": self.rubber_ducker_agent.think_aloud(state["repo_analysis"], state["web_search_results"])})
        workflow.add_node("tech_lead", lambda state: {**state, "tech_lead_review": self.tech_lead_agent.review_and_compose(state)})

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
            github_data={},
            repo_analysis="",
            web_search_results=[],
            rubber_duck_thoughts="",
            tech_lead_review=""
        )

        result = await chain.ainvoke(initial_state)
        return result