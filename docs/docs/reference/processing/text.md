---
sidebar_label: text
title: processing.text
---

Text processing functions

#### split\_text

```python
def split_text(text: str,
               max_length: int = 8192) -> Generator[str, None, None]
```

Split text into chunks of a maximum length

**Arguments**:

- `text` _str_ - The text to split
- `max_length` _int, optional_ - The maximum length of each chunk. Defaults to 8192.
  

**Yields**:

- `str` - The next chunk of text
  

**Raises**:

- `ValueError` - If the text is longer than the maximum length

#### summarize\_text

```python
def summarize_text(url: str,
                   text: str,
                   question: str,
                   driver: Optional[WebDriver] = None) -> str
```

Summarize text using the OpenAI API

**Arguments**:

- `url` _str_ - The url of the text
- `text` _str_ - The text to summarize
- `question` _str_ - The question to ask the model
- `driver` _WebDriver_ - The webdriver to use to scroll the page
  

**Returns**:

- `str` - The summary of the text

#### scroll\_to\_percentage

```python
def scroll_to_percentage(driver: WebDriver, ratio: float) -> None
```

Scroll to a percentage of the page

**Arguments**:

- `driver` _WebDriver_ - The webdriver to use
- `ratio` _float_ - The percentage to scroll to
  

**Raises**:

- `ValueError` - If the ratio is not between 0 and 1

#### create\_message

```python
def create_message(chunk: str, question: str) -> Dict[str, str]
```

Create a message for the chat completion

**Arguments**:

- `chunk` _str_ - The chunk of text to summarize
- `question` _str_ - The question to answer
  

**Returns**:

  Dict[str, str]: The message to send to the chat completion

#### write\_to\_file

```python
def write_to_file(filename: str, text: str) -> None
```

Write text to a file

**Arguments**:

- `text` _str_ - The text to write
- `filename` _str_ - The filename to write to

