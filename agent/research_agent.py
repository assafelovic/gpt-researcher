# Description: Research assistant class that handles the research process for a given question.

# libraries
import asyncio
import json
import uuid

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
import string


CFG = Config()


class ResearchAgent:
    def __init__(self, question, agent, agent_role_prompt, websocket, rabbit):
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
        self.rabbit = rabbit

    async def summarize(self, text, topic):
        """ Summarizes the given text for the given topic.
        Args: text (str): The text to summarize
                topic (str): The topic to summarize the text for
        Returns: str: The summarized text
        """

        messages = [create_message(text, topic)]

        summary_text_logs = {"type": "logs", "output": f"📝 Summarizing text for query: {text}"}
        self.rabbit.publish_to_rabbit(summary_text_logs)
        await self.websocket.send_json(summary_text_logs)

        return create_chat_completion(
            model=CFG.fast_llm_model,
            messages=messages,
        )

    async def get_new_urls(self, url_set_input):
        """ Gets the new urls from the given url set.
        Args: url_set_input (set[str]): The url set to get the new urls from
        Returns: list[str]: The new urls from the given url set
        """

        new_urls = []
        for url in url_set_input:
            if url not in self.visited_urls:
                adding_source_url_logs = {"type": "logs", "output": f"✅ Adding source url to research: {url}\n"}
                self.rabbit.publish_to_rabbit(adding_source_url_logs)
                await self.websocket.send_json(adding_source_url_logs)
                self.visited_urls.add(url)
                new_urls.append(url)

        return new_urls

    async def call_agent(self, action, stream=False, websocket=None):
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
            rabbit=self.rabbit
        )
        return answer

    async def create_search_queries(self):
        """ Creates the search queries for the given question.
        Args: None
        Returns: list[str]: The search queries for the given question
        """
        result = await self.call_agent(prompts.generate_search_queries_prompt(self.question))
        print(result)

        research_queries_logs = {"type": "logs", "output": f"🧠 I will conduct my research based on the following queries: {result}..."}

        self.rabbit.publish_to_rabbit(research_queries_logs)
        await self.websocket.send_json(research_queries_logs)
        return json.loads(result)

    async def async_search(self, query):
        """ Runs the async search for the given query.
        Args: query (str): The query to run the async search for
        Returns: list[str]: The async search for the given query
        """
        search_results = json.loads(web_search(query))
        new_search_urls = self.get_new_urls([url.get("href") for url in search_results])
        
        sites_to_browse_logs = {"type": "logs", "output": f"🌐 Browsing the following sites for relevant information: {new_search_urls}..."}
        self.rabbit.publish_to_rabbit(sites_to_browse_logs)
        await self.websocket.send_json(sites_to_browse_logs)

        # Create a list to hold the coroutine objects
        tasks = [async_browse(url, query, self.websocket, self.rabbit) for url in await new_search_urls]

        # Gather the results as they become available
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        return responses

    async def run_search_summary(self, query):
        """ Runs the search summary for the given query.
        Args: query (str): The query to run the search summary for
        Returns: str: The search summary for the given query
        """

        query_to_research_logs = {"type": "logs", "output": f"🔎 Running research for '{query}'..."}
        self.rabbit.publish_to_rabbit(query_to_research_logs)
        await self.websocket.send_json(query_to_research_logs)

        responses = await self.async_search(query)

        result = "\n".join(responses)
        result_logs = {"type": "final report", "output": result}
        self.rabbit.publish_to_rabbit({"type": "final report", "output": result})
        
        # os.makedirs(os.path.dirname(f"./outputs/{self.directory_name}/research-{query}.txt"), exist_ok=True)
        # write_to_file(f"./outputs/{self.directory_name}/research-{query}.txt", result)
        return result

    async def conduct_research(self):
        """ Conducts the research for the given question.
        Args: None
        Returns: str: The research for the given question
        """

        self.research_summary = read_txt_files(self.dir_path) if os.path.isdir(self.dir_path) else ""

        if not self.research_summary:
            search_queries = await self.create_search_queries()
            for query in search_queries:
                research_result = await self.run_search_summary(query)
                self.research_summary += f"{research_result}\n\n"

        research_summary_logs = {"type": "logs", "output": f"Total research words: {len(self.research_summary.split(' '))}"}
        self.rabbit.publish_to_rabbit(research_summary_logs)
        await self.websocket.send_json(research_summary_logs)

        return self.research_summary


    async def create_concepts(self):
        """ Creates the concepts for the given question.
        Args: None
        Returns: list[str]: The concepts for the given question
        """
        result = self.call_agent(prompts.generate_concepts_prompt(self.question, self.research_summary))
        
        concepts_to_research_logs = {"type": "logs", "output": f"I will research based on the following concepts: {result}\n"}
        self.rabbit.publish_to_rabbit(concepts_to_research_logs)
        await self.websocket.send_json(concepts_to_research_logs)
        return json.loads(result)

    async def write_report(self, report_type, websocket):
        """ Writes the report for the given question.
        Args: None
        Returns: str: The report for the given question
        """
        report_type_func = prompts.get_report_by_type(report_type)
        
        writing_report_logs = {"type": "logs", "output": f"✍️ Writing {report_type} for research task: {self.question}..."}

        self.rabbit.publish_to_rabbit(writing_report_logs)
        await websocket.send_json(writing_report_logs)
        answer = await self.call_agent(report_type_func(self.question, self.research_summary), stream=True,
                                       websocket=websocket)

        path = await write_md_to_pdf(report_type, self.directory_name, await answer)

        return answer, path

    async def write_lessons(self):
        """ Writes lessons on essential concepts of the research.
        Args: None
        Returns: None
        """
        concepts = await self.create_concepts()
        for concept in concepts:
            answer = await self.call_agent(prompts.generate_lesson_prompt(concept), stream=True)
            write_md_to_pdf("Lesson", self.directory_name, answer)
