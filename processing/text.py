"""Text processing functions"""
import urllib
from typing import Dict, Generator, Optional
import string

from selenium.webdriver.remote.webdriver import WebDriver

from config import Config
from agent.llm_utils import create_chat_completion
import os
from md2pdf.core import md2pdf

CFG = Config()


def split_text(text: str, max_length: int = 8192) -> Generator[str, None, None]:
    """Split text into chunks of a maximum length

    Args:
        text (str): The text to split
        max_length (int, optional): The maximum length of each chunk. Defaults to 8192.

    Yields:
        str: The next chunk of text

    Raises:
        ValueError: If the text is longer than the maximum length
    """
    paragraphs = text.split("\n")
    current_length = 0
    current_chunk = []

    for paragraph in paragraphs:
        if current_length + len(paragraph) + 1 <= max_length:
            current_chunk.append(paragraph)
            current_length += len(paragraph) + 1
        else:
            yield "\n".join(current_chunk)
            current_chunk = [paragraph]
            current_length = len(paragraph) + 1

    if current_chunk:
        yield "\n".join(current_chunk)


def summarize_text(
    url: str, text: str, question: str, driver: Optional[WebDriver] = None
) -> str:
    """Summarize text using the OpenAI API

    Args:
        url (str): The url of the text
        text (str): The text to summarize
        question (str): The question to ask the model
        driver (WebDriver): The webdriver to use to scroll the page

    Returns:
        str: The summary of the text
    """
    if not text:
        return "Error: No text to summarize"

    summaries = []
    chunks = list(split_text(text))
    scroll_ratio = 1 / len(chunks)

    for i, chunk in enumerate(chunks):
        if driver:
            scroll_to_percentage(driver, scroll_ratio * i)

        memory_to_add = f"Source: {url}\n" f"Raw content part#{i + 1}: {chunk}"

        #MEMORY.add_documents([Document(page_content=memory_to_add)])

        messages = [create_message(chunk, question)]

        summary = create_chat_completion(
            model=CFG.fast_llm_model,
            messages=messages,
        )
        summaries.append(summary)
        memory_to_add = f"Source: {url}\n" f"Content summary part#{i + 1}: {summary}"

        #MEMORY.add_documents([Document(page_content=memory_to_add)])


    combined_summary = "\n".join(summaries)
    messages = [create_message(combined_summary, question)]

    return create_chat_completion(
        model=CFG.fast_llm_model,
        messages=messages,
    )


def scroll_to_percentage(driver: WebDriver, ratio: float) -> None:
    """Scroll to a percentage of the page

    Args:
        driver (WebDriver): The webdriver to use
        ratio (float): The percentage to scroll to

    Raises:
        ValueError: If the ratio is not between 0 and 1
    """
    if ratio < 0 or ratio > 1:
        raise ValueError("Percentage should be between 0 and 1")
    driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {ratio});")


def create_message(chunk: str, question: str) -> Dict[str, str]:
    """Create a message for the chat completion

    Args:
        chunk (str): The chunk of text to summarize
        question (str): The question to answer

    Returns:
        Dict[str, str]: The message to send to the chat completion
    """
    return {
        "role": "user",
        "content": f'"""{chunk}""" Using the above text, answer the following'
        f' question: "{question}" -- if the question cannot be answered using the text,'
        " simply summarize the text in depth. "
        "Include all factual information, numbers, stats etc if available.",
    }

def write_to_file(filename: str, text: str) -> None:
    """Write text to a file

    Args:
        text (str): The text to write
        filename (str): The filename to write to
    """
    with open(filename, "w") as file:
        file.write(text)

async def write_md_to_pdf(task: str, directory_name: str, text: str) -> None:
    file_path = f"./outputs/{directory_name}/{task}"
    write_to_file(f"{file_path}.md", text)
    md_to_pdf(f"{file_path}.md", f"{file_path}.pdf")
    print(f"{task} written to {file_path}.pdf")

    encoded_file_path = urllib.parse.quote(f"{file_path}.pdf")

    return encoded_file_path

def read_txt_files(directory):
    all_text = ''

    for filename in os.listdir(directory):
        if filename.endswith('.txt'):
            with open(os.path.join(directory, filename), 'r') as file:
                all_text += file.read() + '\n'

    return all_text


def md_to_pdf(input_file, output_file):
    md2pdf(output_file,
           md_content=None,
           md_file_path=input_file,
           css_file_path=None,
           base_url=None)
