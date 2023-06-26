from agent.research_assistant import ResearchAssistant
import datetime

def run_agent(task):
    start_time = datetime.datetime.now()
    print("Start time: ", start_time)

    assistant = ResearchAssistant(task)
    assistant.conduct_research()
    assistant.write_report()

    end_time = datetime.datetime.now()
    print("End time: ", end_time)
    print("Total run time: ", end_time - start_time)