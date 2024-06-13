import os

from colorama import Fore, Style
from langchain_openai import AzureChatOpenAI

'''
Please note:
Needs additional env vars such as: 
    AZURE_OPENAI_ENDPOINT  e.g. https://xxxx.openai.azure.com/",
    AZURE_OPENAI_API_KEY e.g "xxxxxxxxxxxxxxxxxxxxx",
    OPENAI_API_VERSION, e.g. "2024-03-01-preview" but needs to updated over time as API verison updates,
    AZURE_EMBEDDING_MODEL e.g. "ada2" The Azure OpenAI embedding model deployment name.

config.py settings for Azure OpenAI should look like:
    self.embedding_provider = os.getenv('EMBEDDING_PROVIDER', 'azureopenai')
    self.llm_provider = os.getenv('LLM_PROVIDER', "azureopenai")
    self.fast_llm_model = os.getenv('FAST_LLM_MODEL', "gpt-3.5-turbo-16k") #Deployment name of your GPT3.5T model as per azure OpenAI studio deployment section
    self.smart_llm_model = os.getenv('SMART_LLM_MODEL', "gpt4")  #Deployment name of your GPT4 1106-Preview+ (GPT4T) model as per azure OpenAI studio deployment section
'''
class AzureOpenAIProvider:

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
        Gets the OpenAI API key
        Returns:

        """
        try:
            api_key = os.environ["AZURE_OPENAI_API_KEY"]
        except:
            raise Exception(
                "Azure OpenAI API key not found. Please set the AZURE_OPENAI_API_KEY environment variable.")
        return api_key

    def get_llm_model(self):
        # Initializing the chat model
        llm = AzureChatOpenAI(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
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
