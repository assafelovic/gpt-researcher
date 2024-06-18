import asyncio

from fastapi import WebSocket

from gpt_researcher.master.agent import GPTResearcher
from gpt_researcher.master.actions import (add_source_urls, extract_headers,
                                             table_of_contents)


class DetailedReport():
    def __init__(self, query: str, report_type: str, report_source: str, source_urls, config_path: str, websocket: WebSocket, subtopics=[]):
        self.query = query
        self.report_type = report_type
        self.report_source = report_source
        self.source_urls = source_urls
        self.config_path = config_path
        self.websocket = websocket
        self.subtopics = subtopics
        
        # A parent task assistant. Adding research_report as default
        self.main_task_assistant = GPTResearcher(self.query, "research_report", self.report_source, self.source_urls, self.config_path, self.websocket)
        self.existing_headers = []
        # This is a global variable to store the entire context accumulated at any point through searching and scraping
        self.global_context = []
    
        # This is a global variable to store the entire url list accumulated at any point through searching and scraping
        if self.source_urls:
            self.global_urls = set(self.source_urls)

    async def run(self):

        # Conduct initial research using the main assistant
        await self._initial_research()

        # Get list of all subtopics
        subtopics = await self._get_all_subtopics()
        
        # Generate report introduction
        report_introduction = await self.main_task_assistant.write_introduction()

        # Generate the subtopic reports based on the subtopics gathered
        _, report_body = await self._generate_subtopic_reports(subtopics)

        # Construct the final list of visited urls
        self.main_task_assistant.visited_urls.update(self.global_urls)

        # Construct the final detailed report (Optionally add more details to the report)
        report = await self._construct_detailed_report(report_introduction, report_body)

        return report

    async def _initial_research(self):
        # Conduct research using the main task assistant to gather content for generating subtopics
        await self.main_task_assistant.conduct_research()
        # Update context of the global context variable
        self.global_context = self.main_task_assistant.context
        # Update url list of the global list variable
        self.global_urls = self.main_task_assistant.visited_urls

    async def _get_all_subtopics(self) -> list:
        subtopics = await self.main_task_assistant.get_subtopics()
        return subtopics.dict()["subtopics"]

    async def _generate_subtopic_reports(self, subtopics: list) -> tuple:
        subtopic_reports = []
        subtopics_report_body = ""

        async def fetch_report(subtopic):

            subtopic_report = await self._get_subtopic_report(subtopic)

            return {
                "topic": subtopic,
                "report": subtopic_report
            }

        # This is the asyncio version of the same code below
        # Although this will definitely run faster, the problem
        # lies in avoiding duplicate information.
        # To solve this the headers from previous subtopic reports are extracted
        # and passed to the next subtopic report generation.
        # This is only possible to do sequentially

        # tasks = [fetch_report(subtopic) for subtopic in subtopics]
        # results = await asyncio.gather(*tasks)

        # for result in filter(lambda r: r["report"], results):
        #     subtopic_reports.append(result)
        #     subtopics_report_body += "\n\n\n" + result["report"]

        for subtopic in subtopics:
            result = await fetch_report(subtopic)
            if result["report"]:
                subtopic_reports.append(result)
                subtopics_report_body += "\n\n\n" + result["report"]

        return subtopic_reports, subtopics_report_body

    async def _get_subtopic_report(self, subtopic: dict) -> tuple:
        current_subtopic_task = subtopic.get("task")
        subtopic_assistant = GPTResearcher(
            query=current_subtopic_task,
            report_type="subtopic_report",
            report_source=self.report_source,
            websocket=self.websocket,
            parent_query=self.query,
            subtopics=self.subtopics,
            visited_urls=self.global_urls,
            agent=self.main_task_assistant.agent,
            role=self.main_task_assistant.role
        )

        # The subtopics should start research from the context gathered till now
        subtopic_assistant.context = list(set(self.global_context))

        # Conduct research on the subtopic
        await subtopic_assistant.conduct_research()

        # Here the headers gathered from previous subtopic reports are passed to the write report function
        # The LLM is later instructed to avoid generating any information relating to these headers as they have already been generated
        subtopic_report = await subtopic_assistant.write_report(self.existing_headers)

        # Update context of the global context variable
        self.global_context = list(set(subtopic_assistant.context))
        # Update url list of the global list variable
        self.global_urls.update(subtopic_assistant.visited_urls)

        # After a subtopic report has been generated then append the headers of the report to existing headers
        self.existing_headers.append(
            {
                "subtopic task": current_subtopic_task,
                "headers": extract_headers(subtopic_report),
            }
        )

        return subtopic_report

    async def _construct_detailed_report(self, introduction: str, report_body: str):
        # Generating a table of contents from report headers
        toc = table_of_contents(report_body)
        
        # Concatenating all source urls at the end of the report
        report_with_references = add_source_urls(report_body, self.main_task_assistant.visited_urls)
        
        return f"{introduction}\n\n{toc}\n\n{report_with_references}"