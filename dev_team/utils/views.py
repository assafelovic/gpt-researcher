from colorama import Fore, Style

def print_agent_output(message, agent):
    color = {
        "GITHUB": Fore.BLUE,
        "ANALYZER": Fore.GREEN,
        "WEBSEARCH": Fore.YELLOW,
        "RUBBERDUCKER": Fore.MAGENTA,
        "TECHLEAD": Fore.CYAN
    }.get(agent.upper(), Fore.WHITE)

    print(f"{color}[{agent.upper()}] {message}{Style.RESET_ALL}")