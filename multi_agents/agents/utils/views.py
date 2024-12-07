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
    MATH_TEACHER = Fore.CYAN
    PARSER = Fore.CYAN  # ここに追加
    PLANNER = Fore.MAGENTA
    SOLVER = Fore.YELLOW
    EXPLAINER = Fore.LIGHTYELLOW_EX
    FORMATTER = Fore.MAGENTA


def print_agent_output(output:str, agent: str="RESEARCHER"):
    print(f"{AgentColor[agent].value}{agent}: {output}{Style.RESET_ALL}")