from __future__ import annotations

from enum import Enum

from colorama import Fore, Style


class AgentColor(Enum):
    RESEARCHER = Fore.LIGHTBLUE_EX
    EDITOR = Fore.YELLOW
    WRITER = Fore.LIGHTGREEN_EX
    PUBLISHER = Fore.MAGENTA
    REVIEWER = Fore.CYAN
    REVISOR = Fore.LIGHTWHITE_EX
    MASTER = Fore.LIGHTYELLOW_EX


def print_agent_output(output: str, agent: str = "RESEARCHER"):
    print(f"{AgentColor[agent].value}{agent}: {output}{Style.RESET_ALL}")
