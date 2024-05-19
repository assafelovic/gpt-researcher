from backend.report_type.custom_detailed_report.custom_detailed_report import CustomDetailedReport
from gpt_researcher.utils.llm import construct_subtopics, construct_directors, construct_director_sobject

async def test_llm_functions():
    # Dummy data for construct_subtopics
    task_subtopics = "Write a report on the history of artificial intelligence"
    data_subtopics = "Artificial intelligence has a long history dating back to the 1950s. Early research focused on symbolic reasoning and expert systems. In the 1980s and 1990s, machine learning techniques such as neural networks gained popularity. Recent advancements in deep learning have led to breakthroughs in areas like computer vision and natural language processing."
    config_subtopics = {"smart_llm_model": "gpt-3.5-turbo", "llm_provider": "openai", "max_subtopics": 5}

    # Dummy data for construct_directors
    task_directors = "Write a report on the directors of Wiredirect Services Limited"
    data_directors = "Wiredirect Services Limited has 8 active directors: Emma Joan Strydom, Darran Pienaar, Terence William Cave, Jesse David Hemson-Struthers, Donald Duke Jackson, Maximilian Benedikt Von Both, and Exceed COSEC Services Limited."
    config_directors = {"smart_llm_model": "gpt-3.5-turbo", "llm_provider": "openai"}

    # Dummy data for construct_director_sobjects
    task_sobjects = "Write a report on Emma Joan Strydom, a director of Wiredirect Services Limited"
    data_sobjects = "Emma Joan Strydom is a director of Wiredirect Services Limited. She was appointed on 21 January 2021."
    config_sobjects = {"smart_llm_model": "gpt-3.5-turbo", "llm_provider": "openai"}

    subtopics = await construct_subtopics(task_subtopics, data_subtopics, config_subtopics)
    print("Subtopics:", subtopics)

    directors = await construct_directors(task_directors, data_directors, config_directors)
    print("Directors:", directors)

    sobjects = await construct_director_sobject(task_sobjects, data_sobjects, config_sobjects)
    print("Director SObjects:", sobjects)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_llm_functions())