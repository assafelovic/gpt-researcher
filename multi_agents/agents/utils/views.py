from colorama import Fore, Style
from enum import Enum


class AgentColor(Enum):
    RESEARCHER = Fore.LIGHTBLUE_EX
    EDITOR = Fore.YELLOW
    WRITER = Fore.LIGHTGREEN_EX
    PUBLISHER = Fore.MAGENTA
    REVIEWER = Fore.CYAN
    REVISOR = Fore.LIGHTWHITE_EX
    MASTER = Fore.LIGHTYELLOW_EX
    EXPLORER = Fore.LIGHTBLUE_EX
    SYNTHESIZER = Fore.LIGHTMAGENTA_EX
    PLANNER = Fore.LIGHTCYAN_EX
    FINALIZER = Fore.LIGHTWHITE_EX
    REPORTER = Fore.LIGHTWHITE_EX
    DEEP_WRITER = Fore.LIGHTGREEN_EX
    ORCHESTRATOR = Fore.LIGHTRED_EX


def print_agent_output(output:str, agent: str="RESEARCHER"):
    print(f"{AgentColor[agent].value}{agent}: {output}{Style.RESET_ALL}")