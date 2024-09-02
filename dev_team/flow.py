from langgraph import Graph, Node, Edge
from .agents import create_github_fetcher_agent, create_filesystem_analyzer_agent
from .tools import github_fetcher_tools, filesystem_analyzer_tools

def run_dev_team_flow(repo_url: str, query: str):
    graph = Graph()

    # Create nodes
    github_fetcher_node = Node(id="github_fetcher", value={"agent": create_github_fetcher_agent(github_fetcher_tools)})
    filesystem_analyzer_node = Node(id="filesystem_analyzer", value={"agent": create_filesystem_analyzer_agent(filesystem_analyzer_tools)})

    # Add nodes to the graph
    graph.add_node(github_fetcher_node)
    graph.add_node(filesystem_analyzer_node)

    # Create edge
    edge = Edge(source=github_fetcher_node, target=filesystem_analyzer_node)
    graph.add_edge(edge)

    # Run the flow
    github_fetcher_result = github_fetcher_node.value["agent"].run(repo_url)
    filesystem_analyzer_result = filesystem_analyzer_node.value["agent"].run(query)

    return filesystem_analyzer_result