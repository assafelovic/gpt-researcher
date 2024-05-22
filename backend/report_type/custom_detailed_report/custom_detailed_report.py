#custom_detailed_report.py

import asyncio
from typing import Union, List, Optional

from gpt_researcher.master.agent import GPTResearcher
from gpt_researcher.master.functions import (add_source_urls,
                                             table_of_contents)
from gpt_researcher.utils.llm import construct_director_sobject, construct_company_sobject, construct_directors
from gpt_researcher.utils.validators import CompanyReport, Director, Directors, Subtopics

class CustomDetailedReport():
    def __init__(self, query: str, source_urls, config_path: str, subtopics=[], include_domains=None, exclude_domains=None, parent_sub_queries=None, child_sub_queries=None, directors: Optional[Union[List[str], Directors]] = None):
        self.query = query
        self.source_urls = source_urls
        self.config_path = config_path
        self.subtopics = subtopics
        self.parent_sub_queries = parent_sub_queries
        self.child_sub_queries = child_sub_queries
        # A parent task assistant. Adding compliance_report as default
        self.main_task_assistant = GPTResearcher(
            self.query,
            "compliance_report",
            self.source_urls,
            self.config_path,
            include_domains=include_domains,
            exclude_domains=exclude_domains,
            custom_sub_queries=parent_sub_queries
        )

        self.existing_headers = []
        # This is a global variable to store the entire context accumulated at any point through searching and scraping
        self.global_context = []
    
        # This is a global variable to store the entire url list accumulated at any point through searching and scraping
        if self.source_urls:
            self.global_urls = set(self.source_urls)
        self.directors = self._initialize_directors(directors)
        self.director_sobjects = []
        self.company_sobject = None

    def _initialize_directors(self, directors):
        if directors is None:
            return Directors(directors=[])
        elif isinstance(directors, list):
            directors_list = [Director(first_name=name.split()[0], last_name=" ".join(name.split()[1:])) for name in directors]
            return Directors(directors=directors_list)
        else:
            return directors

    async def run(self):
        # Conduct initial research using the main assistant
        await self._initial_research()

        # Get list of all subtopics
        if not self.directors.directors:
            print(f"Constructing directors using construct_directors function")
            self.directors = await construct_directors(
                task=self.query,
                data=self.main_task_assistant.context,
                config=self.main_task_assistant.cfg,
            )
        
        print("Directors **** : ", self.directors.directors)
        
        # Generate report introduction
        compliance_report = await self.main_task_assistant.write_report()
        
        company_sobject = await construct_company_sobject(compliance_report, self.main_task_assistant.visited_urls, self.main_task_assistant.query, self.main_task_assistant.context, self.main_task_assistant.cfg)
        if company_sobject:
            self.company_sobject = company_sobject

        # Generate the subtopic reports based on the subtopics gathered
        # _, report_body = await self._generate_directors_reports(directors)
        print("Directors **** : ", self.directors.directors)
        await self._generate_directors_reports(self.directors)

        # Construct the final list of visited urls
        self.main_task_assistant.visited_urls.update(self.global_urls)

        # Construct the final detailed report (Optionally add more details to the report)
        # report = await self._construct_detailed_report(report_introduction, report_body)

        # return report_introduction
        print(f"In run method: compliance_report type: {type(compliance_report)}")
        print(f"In run method: self.company_sobject type: {type(self.company_sobject)}")
        print(f"In run method: self.director_sobjects type: {type(self.director_sobjects)}")
        

        return CompanyReport(
            report=compliance_report,
            company=self.company_sobject,
            directors=self.director_sobjects,
            source_urls=list(self.main_task_assistant.visited_urls)
        )

    async def _initial_research(self):
        # Conduct research using the main task assistant to gather content for generating subtopics
        await self.main_task_assistant.conduct_research()
        # Update context of the global context variable
        self.global_context = self.main_task_assistant.context
        # Update url list of the global list variable
        self.global_urls = self.main_task_assistant.visited_urls

    async def _get_all_subtopics(self) -> list:
        if self.main_task_assistant.report_type == "compliance_report":
            directors = await self.main_task_assistant.get_subtopics()
            return directors
        else:
            subtopics = await self.main_task_assistant.get_subtopics()
            return subtopics.dict()["subtopics"]

    async def _generate_directors_reports(self, directors: Directors) -> tuple:
        async def fetch_report(director: Director):
                    await self._get_subtopic_report(director)

        print("Directors: ", directors)
        tasks = [fetch_report(director) for director in directors.directors]
        await asyncio.gather(*tasks)

    async def _get_subtopic_report(self, director: Director) -> tuple:
        print("Director: ", director)
        print("Report Type: ", self.main_task_assistant.report_type)

        # current_subtopic_task = director.dict()["fullname"]
        current_subtopic_task = f"{director.first_name} {director.last_name}"

        
        if self.child_sub_queries:
            custom_sub_queries = [f"\"{current_subtopic_task}\" {child_sub_query}" for child_sub_query in self.child_sub_queries]
        else:
            custom_sub_queries = []
        
        print("Custom Sub Queries: ", custom_sub_queries)
        subtopic_assistant = GPTResearcher(
            query=current_subtopic_task,
            report_type="director_report",
            parent_query=self.query,
            subtopics=custom_sub_queries,
            visited_urls=self.global_urls,
            agent=self.main_task_assistant.agent,
            role=self.main_task_assistant.role,
            custom_sub_queries=custom_sub_queries  # Pass the child_sub_queries as custom_sub_query
        )

        # The subtopics should start research from the context gathered till now
        subtopic_assistant.context = list(set(self.global_context))

        # Conduct research on the subtopic
        await subtopic_assistant.conduct_research()

        # Here the headers gathered from previous subtopic reports are passed to the write report function
        # The LLM is later instructed to avoid generating any information relating to these headers as they have already been generated
        director_report = await subtopic_assistant.write_report(self.existing_headers)

        # print(f"subtopic report for: {subtopic_assistant.query}: ", subtopic_report)
        #construct and add the directors

        # Update context of the global context variable
        self.global_context = list(set(subtopic_assistant.context))
        # Update url list of the global list variable
        self.global_urls.update(subtopic_assistant.visited_urls)

        director_sobject = await construct_director_sobject(
            subtopic_assistant.query, 
            subtopic_assistant.visited_urls, 
            subtopic_assistant.query, 
            subtopic_assistant.context, 
            self.main_task_assistant.cfg
        )

        print(f"construct_director_sobjects output for {current_subtopic_task}: ", director_sobject)
        if director_sobject:
            director_sobject_dict = director_sobject.dict()
            director_sobject_dict["report"] = director_report
            self.director_sobjects.append(director_sobject_dict)

        return director_report

    async def _construct_detailed_report(self, introduction: str, report_body: str):
        # Generating a table of contents from report headers
        toc = table_of_contents(report_body)
        
        # Concatenating all source urls at the end of the report
        report_with_references = add_source_urls(report_body, self.main_task_assistant.visited_urls)
        
        return f"{introduction}\n\n{toc}\n\n{report_with_references}"