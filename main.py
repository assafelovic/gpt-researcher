# Description: Main file for running the agent
from agent.run import run_agent

OPTION_TO_REPORT_TYPE = {
    "1": "research_report",
    "2": "resource_report",
    "3": "outline_report"
}

if __name__ == "__main__":
    while True:
        research_task = input("What would you like me to research next?\n>> ")
        report_type = input("What type of report would you like me to generate?\n"
                            "[1] - Research Report\n"
                            "[2] - Resource Report\n"
                            "[3] - Outline Report\n>>")
        run_agent(research_task, OPTION_TO_REPORT_TYPE[report_type])
