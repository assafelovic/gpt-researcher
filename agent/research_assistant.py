# Description: Research assistant class that handles the research process for a given question.

# libraries
import asyncio
import json
import string
from actions.web_search import web_search
from actions.web_scrape import async_browse
from processing.text import \
    write_to_file, \
    create_message, \
    create_chat_completion, \
    read_txt_files, \
    write_md_to_pdf
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
        self.directory_name = ''.join(c for c in self.directory_name if c in string.ascii_letters or c in string.digits or c.isspace())

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

    def call_agent(self, action, stream=False):
        messages = [{
            "role": "system",
            "content": prompts.generate_agent_role_prompt(),
        }, {
            "role": "user",
            "content": action,
        }]
        answer = create_chat_completion(
            model="gpt-4",
            messages=messages,
            stream=stream,
        )
        return answer

    def create_search_queries(self):
        """ Creates the search queries for the given question.
        Args: None
        Returns: list[str]: The search queries for the given question
        """
        result = self.call_agent(prompts.generate_search_queries_prompt(self.question))
        print(f"Search queries: {result}")
        return json.loads(result)

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

    async def run_search_summary(self, query):
        """ Runs the search summary for the given query.
        Args: query (str): The query to run the search summary for
        Returns: str: The search summary for the given query
        """
        print(f"Running research for {query}...")
        responses = await self.async_search(query)

        result = "\n".join(responses)
        os.makedirs(os.path.dirname(f"./outputs/{self.directory_name}/research-{query}.txt"), exist_ok=True)
        write_to_file(f"./outputs/{self.directory_name}/research-{query}.txt", result)
        return result

    async def conduct_research(self):
        """ Conducts the research for the given question.
        Args: None
        Returns: str: The research for the given question
        """
        self.research_summary = read_txt_files(self.dir_path) if os.path.isdir(self.dir_path) else ""

        if not self.research_summary:
            search_queries = self.create_search_queries()  # + [self.question]
            for query in search_queries:
                research_result = await self.run_search_summary(query)
                self.research_summary += f"{research_result}\n\n"
                print("Research summary so far: ", self.research_summary)

        print(self.research_summary)
        print("Total research words: {0}".format(len(self.research_summary.split(" "))))
        return self.research_summary

    def create_concepts(self):
        """ Creates the concepts for the given question.
        Args: None
        Returns: list[str]: The concepts for the given question
        """
        result = self.call_agent(prompts.generate_concepts_prompt(self.question, self.research_summary))

        print(f"Search queries: {result}")
        return json.loads(result)

    def write_report(self, report_type):
        """ Writes the report for the given question.
        Args: None
        Returns: str: The report for the given question
        """
        report_type_func = prompts.get_report_by_type(report_type)
        answer = self.call_agent(report_type_func(self.question, self.research_summary), stream=True)
        print(f"Writing {report_type} report for query: {self.question}...")
        path = write_md_to_pdf(report_type, self.directory_name, answer)
        return answer, path

    def write_lessons(self):
        """ Writes lessons on essential concepts of the research.
        Args: None
        Returns: None
        """
        concepts = self.create_concepts()
        for concept in concepts:
            answer = self.call_agent(prompts.generate_lesson_prompt(concept), stream=True)
            write_md_to_pdf("Lesson", self.directory_name, answer)
