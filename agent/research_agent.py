import traceback

import asyncio
import json
import uuid
import sys
import hashlib

from actions.web_search import web_search
from actions.web_scrape import async_browse
from processing.text import write_to_file, create_message, create_chat_completion, read_txt_files, write_md_to_pdf
from config import Config
from agent import prompts
import os
import string

CFG = Config()

class ResearchAgent:
    def __init__(self, question, agent, agent_role_prompt, websocket):
        """ Initializes the research assistant with the given question.
        Args: question (str): The question to research
        Returns: None
        """

        self.question = question
        self.agent = agent
        self.agent_role_prompt = agent_role_prompt if agent_role_prompt else prompts.generate_agent_role_prompt(agent)
        self.visited_urls = set()
        self.research_summary = ""
        self.directory_name = uuid.uuid4()
        self.dir_path = os.path.dirname(f"./outputs/{self.directory_name}/")
        self.websocket = websocket


    async def summarize(self, text, topic):
        """ Summarizes the given text for the given topic.
        Args: text (str): The text to summarize
                topic (str): The topic to summarize the text for
        Returns: str: The summarized text
        """
        try:
            messages = [create_message(text, topic)]
            await self.websocket.send_json({"type": "logs", "output": f"📝 Summarizing text for query: {text}"})

            return create_chat_completion(
                model=CFG.fast_llm_model,
                messages=messages,
            )
        except Exception as e:
            traceback.print_exc()
            await self.websocket.send_json({"type": "logs", "output": f"❌ Error occurred during summarization: {str(e)}"})
            return ""

    async def get_new_urls(self, url_set_input):
        """ Gets the new urls from the given url set.
        Args: url_set_input (set[str]): The url set to get the new urls from
        Returns: list[str]: The new urls from the given url set
        """
        try:
            new_urls = []
            for url in url_set_input:
                if url not in self.visited_urls:
                    await self.websocket.send_json({"type": "logs", "output": f"✅ Adding source url to research: {url}\n"})
                    self.visited_urls.add(url)
                    new_urls.append(url)

            return new_urls
        except Exception as e:
            traceback.print_exc()
            await self.websocket.send_json({"type": "logs", "output": f"❌ Error occurred while getting new urls: {str(e)}"})
            return []

    async def call_agent(self, action, stream=False, websocket=None):
        try:
            messages = [{
                "role": "system",
                "content": self.agent_role_prompt
            }, {
                "role": "user",
                "content": action,
            }]
            answer = create_chat_completion(
                model=CFG.smart_llm_model,
                messages=messages,
                stream=stream,
                websocket=websocket,
            )
            return answer
        except Exception as e:
            traceback.print_exc()
            await self.websocket.send_json({"type": "logs", "output": f"❌ Error occurred while calling agent: {str(e)}"})
            return ""

    async def create_search_queries(self):
        """ Creates the search queries for the given question.
        Args: None
        Returns: list[str]: The search queries for the given question
        """
        try:
            result = await self.call_agent(prompts.generate_search_queries_prompt(self.question))
            print(f"result = {result}", file=sys.stderr, flush=True)
            print(result)
            await self.websocket.send_json({"type": "logs", "output": f"🧠 I will conduct my research based on the following queries: {result}..."})
            # return json.loads(result)
            return json.loads(result) if type(result) != str else result.strip("[]").replace('"', '').split("] [")
        except Exception as e:
            traceback.print_exc()
            await self.websocket.send_json({"type": "logs", "output": f"❌ Error occurred while creating search queries: {str(e)}"})
            return []

    async def async_search(self, query):
        """ Runs the async search for the given query.
        Args: query (str): The query to run the async search for
        Returns: list[str]: The async search for the given query
        """
        try:
            search_results = json.loads(web_search(query))
            new_search_urls = self.get_new_urls([url.get("href") for url in search_results])

            await self.websocket.send_json(
                {"type": "logs", "output": f"🌐 Browsing the following sites for relevant information: {new_search_urls}..."})

            # Create a list to hold the coroutine objects
            tasks = [async_browse(url, query, self.websocket) for url in await new_search_urls]

            # Gather the results as they become available
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            return responses
        except Exception as e:
            traceback.print_exc()
            await self.websocket.send_json({"type": "logs", "output": f"❌ Error occurred during async search: {str(e)}"})
            return []

    async def run_search_summary(self, query):
        """ Runs the search summary for the given query.
        Args: query (str): The query to run the search summary for
        Returns: str: The search summary for the given query
        """
        try:
            await self.websocket.send_json({"type": "logs", "output": f"🔎 Running research for '{query}'..."})

            responses = await self.async_search(query)

            result = "\n".join(responses)
            query_hash = hashlib.sha256(query.encode()).hexdigest()[:10]
            filename = f"./outputs/research-{query_hash}.txt"
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            write_to_file(filename, result)
        except Exception as e:
            traceback.print_exc()
            await self.websocket.send_json({"type": "logs", "output": f"❌ Error occurred during search summary: {str(e)}"})

    async def conduct_research(self):
        """ Conducts the research for the given question.
        Args: None
        Returns: str: The research for the given question
        """
        try:
            self.research_summary = read_txt_files(self.dir_path) if os.path.isdir(self.dir_path) else ""

            if not self.research_summary:
                search_queries = await self.create_search_queries()
                num_queries = len(search_queries)
                for idx, query in enumerate(search_queries, 1):
                    await self.websocket.send_json(
                        {"type": "logs", "output": f"💡 Research query [{idx}/{num_queries}]: {query}..."})
                    await self.run_search_summary(query)

            await self.websocket.send_json(
                {"type": "logs", "output": f"Total research words: {len(self.research_summary.split(' '))}"})

            return self.research_summary
        except Exception as e:
            traceback.print_exc()
            await self.websocket.send_json({"type": "logs", "output": f"❌ Error occurred during research: {str(e)}"})
            return ""

    async def create_concepts(self):
        """ Creates the concepts for the given question.
        Args: None
        Returns: list[str]: The concepts for the given question
        """
        try:
            result = self.call_agent(prompts.generate_concepts_prompt(self.question, self.research_summary))
            await self.websocket.send_json({"type": "logs", "output": f"I will research based on the following concepts: {result}\n"})
            return json.loads(result)
        except Exception as e:
            traceback.print_exc()
            await self.websocket.send_json({"type": "logs", "output": f"❌ Error occurred while creating concepts: {str(e)}"})
            return []

    async def write_report(self, report_type, websocket):
        """ Writes the report for the given question.
        Args: None
        Returns: str: The report for the given question
        """
        try:
            report_type_func = prompts.get_report_by_type(report_type)
            await websocket.send_json(
                {"type": "logs", "output": f"✍️ Writing {report_type} for research task: {self.question}..."})
            answer = await self.call_agent(report_type_func(self.question, self.research_summary), stream=True,
                                           websocket=websocket)
            file_directory = f"./outputs/{self.directory_name}"
            os.makedirs(file_directory, exist_ok=True)
            file_path = f"{file_directory}/research_report"
            write_to_file(f"{file_path}.md", str(answer))  # Write the MD file
            path = await write_md_to_pdf(report_type, self.directory_name, await answer)
            return answer, path
        except Exception as e:
            traceback.print_exc()
            await self.websocket.send_json({"type": "logs", "output": f"❌ Error occurred while writing report: {str(e)}"})
            return "", ""

    async def write_lessons(self):
        """ Writes lessons on essential concepts of the research.
        Args: None
        Returns: None
        """
        try:
            concepts = await self.create_concepts()
            num_concepts = len(concepts)
            for idx, concept in enumerate(concepts, 1):
                await self.websocket.send_json(
                    {"type": "logs", "output": f"📖 Writing lesson [{idx}/{num_concepts}]: {concept}..."})
                answer = await self.call_agent(prompts.generate_lesson_prompt(concept), stream=True)
                await write_md_to_pdf("Lesson", self.directory_name, answer)
        except Exception as e:
            traceback.print_exc()
            await self.websocket.send_json({"type": "logs", "output": f"❌ Error occurred while writing lessons: {str(e)}"})
