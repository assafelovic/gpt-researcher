#sf_primary_agent.py

import asyncio
from typing import Union, List, Optional

from sf_researcher.master.agent import SFResearcher
from sf_researcher.master.functions import (add_source_urls,
                                             table_of_contents)
from sf_researcher.utils.llm import *
from sf_researcher.utils.validators import ReportResponse, Contact, Contacts, Subtopics
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SFComplianceReport():
    def __init__(
            self, 
            query: str, 
            contacts,    
            namespace: str,  # Add namespace parameter here
            main_report_type: str,
            child_report_type: str,
            subtopics=[], 
            index_name: str = "sfresearcher",
            config_path=None,
            source_urls=None,
            include_domains=None, 
            exclude_domains=None, 
            parent_sub_queries=None, 
            child_sub_queries=None,
            verbose: bool = True,
            
        ):
        self.query = query
        self.source_urls = source_urls
        self.config_path = config_path
        self.subtopics = subtopics
        self.parent_sub_queries = parent_sub_queries
        self.child_sub_queries = child_sub_queries
        # A parent task assistant. Adding compliance_report as default
        self.main_task_assistant = SFResearcher(
            query=self.query,
            source_urls=self.source_urls,
            config_path=self.config_path,
            report_type=main_report_type,
            include_domains=include_domains,
            exclude_domains=exclude_domains,
            custom_sub_queries=parent_sub_queries,
            index_name=index_name,
            namespace=namespace,
        )
        self.existing_headers = []
        # This is a global variable to store the entire context accumulated at any point through searching and scraping
        self.global_context = []
        # This is a global variable to store the entire url list accumulated at any point through searching and scraping
        if self.source_urls:
            self.global_urls = set(self.source_urls)
        self.contacts = self._initialize_contacts(contacts)
        self.contact_sobjects = []
        self.company_sobject = None
        self.namespace = namespace
        self.index_name = index_name
        self.verbose = verbose
        self.child_report_type = child_report_type
        
    def _initialize_contacts(self, contacts):
        if contacts == []:
            logger.info("No contacts provided. Contactss will be constructed.")
            return None
        else:
            logger.info(f"Initializing contacts from provided list: {contacts}")
            contacts_list = Contacts(contacts=[])
            for name in contacts:
                name_parts = name.split()
                if len(name_parts) >= 2:
                    first_name = name_parts[0]
                    last_name = " ".join(name_parts[1:])
                    contacts_list.contacts.append(Contact(first_name=first_name, last_name=last_name))
                else:
                    logger.warning(f"Cannot construct contacts from user provided list; failed on name: {name}")
                    logger.warning("Will default to construct contacts from search")
                    return None
            return contacts_list

    async def run(self):
        # Conduct initial research using the main assistant
        await self._initial_research()

        # Get list of all subtopics
        if not self.contacts:
            logger.info(f"Constructing contacts using construct_contacts function")
            self.contacts = await construct_contacts(
                company_name=self.query,
                data=self.main_task_assistant.context,
                config=self.main_task_assistant.cfg,
            )
        else:
            logger.info("Using the provided contacts list")
        
        logger.info("Contacts **** : %s", self.contacts)
        
        # Generate report => if compliance/sales report type is handled by function.py
        compliance_report = await self.main_task_assistant.write_report()
        
        if self.main_task_assistant.report_type == "compliance_report":
            company_sobject = await construct_compliance_company_sobject(self.main_task_assistant.visited_urls, self.main_task_assistant.query, self.main_task_assistant.context, self.main_task_assistant.cfg)
            if company_sobject:
                self.company_sobject = company_sobject
        
        # create construct_sales_company_sobject
        else:
            company_sobject = await construct_sales_company_sobject(self.main_task_assistant.visited_urls, self.main_task_assistant.query, self.main_task_assistant.context, self.main_task_assistant.cfg)
            if company_sobject:
                self.company_sobject = company_sobject

        # Generate the subtopic reports based on the subtopics gathered
        await self._generate_contacts_reports(self.contacts)

        # Construct the final list of visited urls
        self.main_task_assistant.visited_urls.update(self.global_urls)

        # return report_introduction
        print(f"In run method: compliance_report type: {type(compliance_report)}")
        print(f"In run method: self.company_sobject type: {type(self.company_sobject)}")
        print(f"In run method: self.contact_sobjects type: {type(self.contact_sobjects)}")
        
        return ReportResponse(
            report=compliance_report,
            company=self.company_sobject,
            contacts=self.contact_sobjects,
            source_urls=list(self.main_task_assistant.visited_urls)  # Convert to list
        )

    async def _initial_research(self):
        # Conduct research using the main task assistant to gather content for generating subtopics
        await self.main_task_assistant.conduct_research_insert()
        await self.main_task_assistant.conduct_research_query()
        # Update context of the global context variable
        self.global_context = self.main_task_assistant.context
        # Update url list of the global list variable
        self.global_urls = self.main_task_assistant.visited_urls

    async def _generate_contacts_reports(self, contacts: Contacts) -> tuple:
        async def fetch_report(contact: Contact):
                    await self._get_subtopic_report(contact)

        print("Contacts: ", contacts)
        tasks = [fetch_report(contact) for contact in contacts.contacts]
        await asyncio.gather(*tasks)

    async def _get_subtopic_report(self, contact: Contact) -> tuple:
        print("Starting _get_subtopic_report")
        print("Contact object: ", contact)
        print("Main Assistant Report Type: ", self.main_task_assistant.report_type)

        current_subtopic_task = f"{contact.first_name} {contact.last_name}"
        
        if self.child_sub_queries:
            custom_sub_queries = [f"\"{current_subtopic_task}\" {child_sub_query}" for child_sub_query in self.child_sub_queries]
        else:
            custom_sub_queries = []
        
        print("Custom Sub Queries: ", custom_sub_queries)
        subtopic_assistant = SFResearcher(
            query=current_subtopic_task,
            report_type=self.child_report_type,
            parent_query=self.query,
            subtopics=custom_sub_queries,
            visited_urls=self.global_urls,
            agent=self.main_task_assistant.agent,
            role=self.main_task_assistant.role,
            custom_sub_queries=custom_sub_queries,
            index_name=self.index_name,
            namespace=self.namespace,
        )

        # The subtopics should start research from the context gathered till now
        subtopic_assistant.context = self.main_task_assistant.context

        # Conduct research on the subtopic
        await subtopic_assistant.conduct_research_insert()
        await subtopic_assistant.conduct_research_query()

        # Generate Report
        contact_report = await subtopic_assistant.write_report()

        self.global_context = list(set(subtopic_assistant.context))
        self.global_urls.update(subtopic_assistant.visited_urls)

        contact_sobject = await construct_contact_sobject(
            subtopic_assistant.query, 
            subtopic_assistant.visited_urls, 
            subtopic_assistant.parent_query, 
            subtopic_assistant.context,
            subtopic_assistant.report_type,
            self.main_task_assistant.cfg
        )

        if contact_sobject:
            contact_sobject_dict = contact_sobject.dict()
            contact_sobject_dict["report"] = contact_report
            contact_sobject_dict["visited_urls"] = list(subtopic_assistant.visited_urls)  # Convert to list
            self.contact_sobjects.append(contact_sobject_dict)

        return contact_report