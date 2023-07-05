import asyncio
from agent.research_assistant import ResearchAssistant
import datetime

async def run_agent(task, report_type):
    """ Runs the agent with the given task.
    Args: task (str): The task to run the agent with
    Returns: None
    """

    start_time = datetime.datetime.now()
    print("Start time: ", start_time)

    assistant = ResearchAssistant(task)
    await assistant.conduct_research()
    report, path = assistant.write_report(report_type)
    #assistant.write_lessons()

    end_time = datetime.datetime.now()
    print("End time: ", end_time)
    print("Total run time: ", end_time - start_time)
    return report, path
