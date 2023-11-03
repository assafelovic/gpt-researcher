from colorama import Fore
import os


class APIKeyError(Exception):
    """
    Exception raised when an API key is not set in config.py or as an environment variable.
    """

    def __init__(self, service_name: str):
        self.service_name = service_name

    def __str__(self):
        if self.service_name == "Tavily":
            service_env = "TAVILY_API_KEY"
            link = "https://app.tavily.com"
        elif self.service_name == "GoogleSerp":
            service_env = "SERP_API_KEY"
            link = "https://serper.dev/"
        elif self.service_name == "Google":
            service_env = "Google_API_KEY and GOOGLE_CX"
            link = "https://developers.google.com/custom-search/v1/overview"
        elif self.service_name == "Searx":
            service_env = "SEARX_URL"
            link = "https://searx.space/"
        elif self.service_name == "OpenAI":
            link = "https://platform.openai.com/account/api-keys"
            return (
                    Fore.RED
                    + "Please set your OpenAI API key in .env or as an environment variable.\n"
                    + "You can get your key from https://platform.openai.com/account/api-keys"
            )

        return (
                Fore.RED
                + f"Please set your {self.service_name} API key in .env or as an environment variable '{service_env}'.\n"
                + f"You can get your key from {link} \n"
                + "Alternatively, you can change the 'search_api' value in config.py to 'duckduckgo'."
        )


def check_agent_setup(agent) -> None:
    check_openai_api_key(agent)
    if agent.search_api == "tavily":
        check_tavily_api_key(agent)
    elif agent.search_api == "googleAPI":
        check_google_api_key(agent)
    elif agent.search_api == "googleSerp":
        check_serp_api_key(agent)
    elif agent.search_api == "searx":
        check_searx_url(agent)


def check_openai_api_key(agent) -> None:
    """Check if the OpenAI API key is set in config.py or as an environment variable."""
    if not agent.openai_api_key:
        raise APIKeyError("OpenAI")


def check_tavily_api_key(agent) -> None:
    """Check if the Tavily Search API key is set in config.py or as an environment variable."""
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key and agent.search_api == "tavily":
        raise APIKeyError("Tavily")


def check_google_api_key(agent) -> None:
    """Check if the Google API key is set in config.py or as an environment variable."""
    google_api_key = os.getenv("GOOGLE_API_KEY")
    google_cx = os.getenv("GOOGLE_CX")
    if not google_api_key and not google_cx and agent.search_api == "googleAPI":
        raise APIKeyError("Google")


def check_serp_api_key(agent) -> None:
    """Check if the SERP API key is set in config.py or as an environment variable."""
    serp_api_key = os.getenv("SERP_API_KEY")
    if not serp_api_key and agent.search_api == "googleSerp":
        raise APIKeyError("GoogleSerp")


def check_searx_url(agent) -> None:
    """Check if the Searx URL is set in config.py or as an environment variable."""
    searx_url = os.getenv("SEARX_URL")
    if not searx_url and agent.search_api == "searx":
        raise APIKeyError("Searx")
