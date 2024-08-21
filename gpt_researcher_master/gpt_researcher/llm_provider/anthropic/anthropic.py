import os

from colorama import Fore, Style
from langchain_anthropic import ChatAnthropic


class AnthropicProvider:

    def __init__(
            self,
            model,
            temperature,
            max_tokens
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens if max_tokens else 4096
        self.api_key = self.get_api_key()
        self.llm = self.get_llm_model()

    def get_api_key(self):
        """
        Gets the OpenAI API key
        Returns:

        """
        try:
            api_key = os.environ["ANTHROPIC_API_KEY"]
        except KeyError:
            raise Exception(
                "Anthropic API key not found. Please set the ANTHROPIC_API_KEY environment variable.")
        return api_key

    def get_llm_model(self):
        # Initializing the chat model
        llm = ChatAnthropic(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            max_tokens_to_sample=4096,
            api_key=self.api_key
        )

        return llm

    async def get_chat_response(self, messages, stream, websocket=None):
        if not stream:
            # Getting output from the model chain using ainvoke for asynchronous invoking
            output = await self.llm.ainvoke(messages)
            return output.content

        else:
            return await self.stream_response(messages, websocket)

    async def stream_response(self, messages, websocket=None):
        paragraph = ""
        response = ""

        # Streaming the response using the chain astream method from langchain
        async for chunk in self.llm.astream(messages):
            content = chunk.content
            if content is not None:
                response += content
                paragraph += content
                if "\n" in paragraph:
                    if websocket is not None:
                        await websocket.send_json({"type": "report", "output": paragraph})
                    else:
                        print(f"{Fore.GREEN}{paragraph}{Style.RESET_ALL}")
                    paragraph = ""

        return response
