# Description: Research assistant class that handles the research process for a given question.

# libraries
import asyncio
import json
from actions.web_search import web_search
from actions.web_scrape import async_browse
from processing.text import write_to_file, create_message, create_chat_completion, md_to_pdf, read_txt_files
from config import Config
from agent import prompts
import os

CFG = Config()


class ResearchAssistant:
    def __init__(self, question):
        """ Initializes the research assistant with the given question.
        Args: question (str): The question to research
        Returns: None
        """

        self.question = question
        self.visited_urls = set()
        self.research_summary = ""
        self.directory_name = question[:100] if len(question) > 100 else question
        self.dir_path = os.path.dirname(f"./outputs/{self.directory_name}/")

    def summarize(self, text, topic):
        """ Summarizes the given text for the given topic.
        Args: text (str): The text to summarize
                topic (str): The topic to summarize the text for
        Returns: str: The summarized text
        """

        messages = [create_message(text, topic)]
        print("Summarizing text for query: ", text)
        return create_chat_completion(
            model=CFG.fast_llm_model,
            messages=messages,
        )

    def get_new_urls(self, url_set_input):
        """ Gets the new urls from the given url set.
        Args: url_set_input (set[str]): The url set to get the new urls from
        Returns: list[str]: The new urls from the given url set
        """

        new_urls = []
        for url in url_set_input:
            if url not in self.visited_urls:
                print("New url found: ", url)
                self.visited_urls.add(url)
                new_urls.append(url)
        return new_urls

    def create_search_queries(self):
        """ Creates the search queries for the given question.
        Args: None
        Returns: list[str]: The search queries for the given question
        """

        messages = [{
            "role": "system",
            "content": prompts.generate_agent_role_prompt(),
        }, {
            "role": "user",
            "content": prompts.generate_search_queries_prompt(self.question),
        }]
        result = create_chat_completion(
            model=CFG.fast_llm_model,
            messages=messages,
        )
        print(f"Search queries: {result}")
        return json.loads(result)

    def write_report(self):
        """ Writes the report for the given question.
        Args: None
        Returns: str: The report for the given question
        """

        messages = [{
            "role": "system",
            "content": prompts.generate_agent_role_prompt(),
        }, {
            "role": "user",
            "content": prompts.generate_report_prompt(self.question, self.research_summary),
        }]
        print(f"Writing report for query: {self.question}...")
        answer = create_chat_completion(
            model="gpt-4",
            messages=messages,
            stream=True,
        )
        file_path = f"./outputs/{self.directory_name}/report"
        write_to_file(f"{file_path}.md", answer)
        md_to_pdf(f"{file_path}.md", f"{file_path}.pdf")
        print(f"Report written to {file_path}.pdf")
        return answer

    async def async_search(self, query):
        """ Runs the async search for the given query.
        Args: query (str): The query to run the async search for
        Returns: list[str]: The async search for the given query
        """

        search_results = json.loads(web_search(query))
        new_search_urls = self.get_new_urls([url.get("href") for url in search_results])
        tasks = [asyncio.create_task(async_browse(url, query)) for url in new_search_urls]
        print("Visited urls: ", self.visited_urls)
        return await asyncio.gather(*tasks)

    def run_search_summary(self, query):
        """ Runs the search summary for the given query.
        Args: query (str): The query to run the search summary for
        Returns: str: The search summary for the given query
        """

        print(f"Running research for {query}...")
        loop = asyncio.get_event_loop()
        responses = loop.run_until_complete(self.async_search(query))

        result = "\n".join(responses)
        os.makedirs(os.path.dirname(f"./outputs/{self.directory_name}/research-{query}.txt"), exist_ok=True)
        write_to_file(f"./outputs/{self.directory_name}/research-{query}.txt", result)
        return result

    def conduct_research(self):
        """ Conducts the research for the given question.
        Args: None
        Returns: str: The research for the given question
        """

        self.research_summary = read_txt_files(self.dir_path) if os.path.isdir(self.dir_path) else ""

        if not self.research_summary:
            search_queries = self.create_search_queries()  # + [self.question]
            for query in search_queries:
                research_result = self.run_search_summary(query)  # summarize(run_search_summary(query), query)
                self.research_summary += f"{research_result}\n\n"  # f"{query}\n{research_result}\n\n"
                print("Research summary so far: ", self.research_summary)

        print(self.research_summary)
        print("Total research words: {0}".format(len(self.research_summary.split(" "))))
        return self.research_summary

    def write_resource_report(self):
        """ Writes the resource report for the given question.
        Args: None
        Returns: str: The resource report for the given question
        """

        messages = [{
            "role": "system",
            "content": prompts.generate_agent_role_prompt(),
        }, {
            "role": "user",
            "content": prompts.generate_resource_report_prompt(self.question, self.research_summary),
        }]
        print(f"Writing resource report for query: {self.question}...")
        answer = create_chat_completion(
            model="gpt-4",
            messages=messages,
            stream=True,
        )
        file_path = f"./outputs/{self.directory_name}/resource_report"
        write_to_file(f"{file_path}.md", answer)
        md_to_pdf(f"{file_path}.md", f"{file_path}.pdf")
        print(f"Resource Report written to {file_path}.pdf")
        return answer

    def write_outline_report(self):
        """ Writes the outline report for the given question.
        Args: None
        Returns: str: The outline report for the given question
        """

        messages = [{
            "role": "system",
            "content": prompts.generate_agent_role_prompt(),
        }, {
            "role": "user",
            "content": prompts.generate_outline_report_prompt(self.question, self.research_summary),
        }]
        print(f"Writing resource report for query: {self.question}...")
        answer = create_chat_completion(
            model="gpt-4",
            messages=messages,
            stream=True,
        )
        file_path = f"./outputs/{self.directory_name}/outline_report"
        write_to_file(f"{file_path}.md", answer)
        md_to_pdf(f"{file_path}.md", f"{file_path}.pdf")
        print(f"Outline Report written to {file_path}.pdf")
        return answer

