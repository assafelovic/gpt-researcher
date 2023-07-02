# Description: This file is used to run the agent. It is the entry point for the agent.
from agent.research_assistant import ResearchAssistant
import datetime


def run_agent(task, report_type):
    """ Runs the agent with the given task.
    Args: task (str): The task to run the agent with
    Returns: None
    """

    start_time = datetime.datetime.now()
    print("Start time: ", start_time)

    assistant = ResearchAssistant(task)
    assistant.conduct_research()
    assistant.write_report(report_type)
    #assistant.write_report("research_report")
    #assistant.write_report("resource_report")
    #assistant.write_report("outline_report")
    assistant.write_lessons()

    end_time = datetime.datetime.now()
    print("End time: ", end_time)
    print("Total run time: ", end_time - start_time)
