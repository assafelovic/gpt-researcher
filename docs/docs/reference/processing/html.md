---
sidebar_label: html
title: processing.html
---

HTML processing functions

#### extract\_hyperlinks

```python
def extract_hyperlinks(soup: BeautifulSoup,
                       base_url: str) -> list[tuple[str, str]]
```

Extract hyperlinks from a BeautifulSoup object

**Arguments**:

- `soup` _BeautifulSoup_ - The BeautifulSoup object
- `base_url` _str_ - The base URL
  

**Returns**:

  List[Tuple[str, str]]: The extracted hyperlinks

#### format\_hyperlinks

```python
def format_hyperlinks(hyperlinks: list[tuple[str, str]]) -> list[str]
```

Format hyperlinks to be displayed to the user

**Arguments**:

- `hyperlinks` _List[Tuple[str, str]]_ - The hyperlinks to format
  

**Returns**:

- `List[str]` - The formatted hyperlinks

