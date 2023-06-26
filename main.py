from agent.run import run_agent

if __name__ == "__main__":
    while True:
        research_task = input("What would you like me to research next?\n>> ")
        run_agent(research_task)