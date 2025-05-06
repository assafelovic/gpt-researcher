---
sidebar_label: config
title: config.config
---

Configuration class to store the state of bools for different scripts access.

## Config Objects

```python
class Config(metaclass=Singleton)
```

Configuration class to store the state of bools for different scripts access.

#### \_\_init\_\_

```python
def __init__() -> None
```

Initialize the Config class

#### set\_fast\_llm\_model

```python
def set_fast_llm_model(value: str) -> None
```

Set the fast LLM model value.

#### set\_smart\_llm\_model

```python
def set_smart_llm_model(value: str) -> None
```

Set the smart LLM model value.

#### set\_fast\_token\_limit

```python
def set_fast_token_limit(value: int) -> None
```

Set the fast token limit value.

#### set\_smart\_token\_limit

```python
def set_smart_token_limit(value: int) -> None
```

Set the smart token limit value.

#### set\_browse\_chunk\_max\_length

```python
def set_browse_chunk_max_length(value: int) -> None
```

Set the browse_website command chunk max length value.

#### set\_openai\_api\_key

```python
def set_openai_api_key(value: str) -> None
```

Set the OpenAI API key value.

#### set\_debug\_mode

```python
def set_debug_mode(value: bool) -> None
```

Set the debug mode value.

## APIKeyError Objects

```python
class APIKeyError(Exception)
```

Exception raised when an API key is not set in config.py or as an environment variable.

#### check\_openai\_api\_key

```python
def check_openai_api_key(cfg) -> None
```

Check if the OpenAI API key is set in config.py or as an environment variable.

#### check\_tavily\_api\_key

```python
def check_tavily_api_key(cfg) -> None
```

Check if the Tavily Search API key is set in config.py or as an environment variable.

#### check\_google\_api\_key

```python
def check_google_api_key(cfg) -> None
```

Check if the Google API key is set in config.py or as an environment variable.

#### check\_serp\_api\_key

```python
def check_serp_api_key(cfg) -> None
```

Check if the SERP API key is set in config.py or as an environment variable.

#### check\_searx\_url

```python
def check_searx_url(cfg) -> None
```

Check if the Searx URL is set in config.py or as an environment variable.

