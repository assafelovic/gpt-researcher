import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import asyncio
from sf_researcher.utils.llm import construct_subtopics, construct_directors, construct_director_sobject
from sf_researcher.config import Config
from sf_researcher.utils.validators import Subtopics, Directors, DirectorSobject

os.environ["SMART_LLM_MODEL"] = "gpt-4"
os.environ["LLM_PROVIDER"] = "openai"
os.environ["MAX_SUBTOPICS"] = "5"

from dotenv import load_dotenv
load_dotenv()

class TestLLMFunctions(unittest.TestCase):
    def test_construct_subtopics(self):
        task = "Write a report on the history of artificial intelligence"
        data = (
            "Artificial intelligence (AI) has a long history dating back to the 1950s. "
            "Early research focused on symbolic reasoning and expert systems. In the 1980s "
            "and 1990s, machine learning techniques such as neural networks gained popularity. "
            "Recent advancements in deep learning have led to breakthroughs in areas like "
            "computer vision and natural language processing."
        )
        config = Config()
        
        loop = asyncio.get_event_loop()
        subtopics = loop.run_until_complete(construct_subtopics(task, data, config))
        
        print("Subtopics Output:", subtopics)
        self.assertIsInstance(subtopics, Subtopics)
        self.assertGreater(len(subtopics.subtopics), 0)
        
    def test_construct_directors(self):
        task = "Write a report on the directors of Wiredirect Services Limited"
        data = (
            "Wiredirect Services Limited has 8 active directors: Emma Joan Strydom, Jesse Hemson-Struthers, "
            "Darran Pienaar, Terence William Cave, Donald Duke Jackson, Maximilian Benedikt Von Both, "
            "and Exceed COSEC Services Limited. These directors have diverse backgrounds in technology, "
            "finance, and management, contributing to the company's strategic direction."
        )
        config = Config()
        
        loop = asyncio.get_event_loop()
        directors = loop.run_until_complete(construct_directors(task, data, config))
        
        print("Directors Output:", directors)
        self.assertIsInstance(directors, Directors)
        self.assertGreater(len(directors.directors), 0)
        
    def test_construct_director_sobjects(self):
        task = (
            "Emma Joan Strydom is a director of Wiredirect Services Limited, a company based in the UK. "
            "She has been serving as a director since January 2021 and has a background in finance and management. "
            "Her role involves overseeing the company's financial strategies and ensuring regulatory compliance. "
            "Wiredirect Services Limited specializes in providing technology solutions to various industries."
        )
        data = (
            "https://example.com/director/emma-joan-strydom"
        )
        config = Config()
        
        loop = asyncio.get_event_loop()
        sobject = loop.run_until_complete(construct_director_sobject(task, data, config))
        
        print("Director Sobject Output:", sobject)
        self.assertIsInstance(sobject, DirectorSobject)
        self.assertIsInstance(sobject.firstname, str)
        self.assertIsInstance(sobject.lastname, str)
        self.assertIsInstance(sobject.company_name, str)
        self.assertIsInstance(sobject.email, (str, type(None)))
        self.assertIsInstance(sobject.mobile_phone, (str, type(None)))
        self.assertIsInstance(sobject.job_title, str)
        self.assertIsInstance(sobject.lead_source_url, str)

if __name__ == "__main__":
    unittest.main()