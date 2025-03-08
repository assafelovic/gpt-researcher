# OpenAI-Compatible APIs

This feature is currently experimental.
OpenAI-Compatible APIs refer to HTTP endpoints that mimic the behavior of OpenAI's HTTP API endpoints. This allows for easy integration of this agent into other UIs designed for OpenAI APIs, such as [Open-WebUI](https://github.com/open-webui/open-webui).

## Supported APIs

Currently supported OpenAI-compatible HTTP API endpoints are listed below:

- `/models`
- `/chat/completions`

Refer to the OpenAI API reference for more details.

## Usage

You can access these endpoints at `{server_base_url}/openai/api`, for example: `curl localhost:8000/openai/api/models`.
