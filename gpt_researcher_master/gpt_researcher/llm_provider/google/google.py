import os

from colorama import Fore, Style
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI


class GoogleProvider:

    def __init__(
        self,
        model,
        temperature,
        max_tokens
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_key = self.get_api_key()
        self.llm = self.get_llm_model()

    def get_api_key(self):
        """
        Gets the GEMINI_API_KEY
        Returns:

        """
        try:
            api_key = os.environ["GEMINI_API_KEY"]
        except:
            raise Exception(
                "GEMINI API key not found. Please set the GEMINI_API_KEY environment variable.")
        return api_key

    def get_llm_model(self):
        # Initializing the chat model
        llm = ChatGoogleGenerativeAI(
            model=self.model,
            temperature=self.temperature,
            max_output_tokens=self.max_tokens,
            google_api_key=self.api_key
        )

        return llm

    def convert_messages(self, messages):
        """
        The function `convert_messages` converts messages based on their role into either SystemMessage
        or HumanMessage objects.
        
        Args:
          messages: It looks like the code snippet you provided is a function called `convert_messages`
        that takes a list of messages as input and converts each message based on its role into either a
        `SystemMessage` or a `HumanMessage`.
        
        Returns:
          The `convert_messages` function is returning a list of converted messages based on the input
        `messages`. The function checks the role of each message in the input list and creates a new
        `SystemMessage` object if the role is "system" or a new `HumanMessage` object if the role is
        "user". The function then returns a list of these converted messages.
        """
        converted_messages = []
        for message in messages:
            if message["role"] == "system":
                converted_messages.append(
                    SystemMessage(content=message["content"]))
            elif message["role"] == "user":
                converted_messages.append(
                    HumanMessage(content=message["content"]))

        return converted_messages

    async def get_chat_response(self, messages, stream, websocket=None):
        if not stream:
            # Getting output from the model chain using ainvoke for asynchronous invoking
            converted_messages = self.convert_messages(messages)
            output = await self.llm.ainvoke(converted_messages)

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
