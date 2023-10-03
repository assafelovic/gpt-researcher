from langchain.chat_models import ChatOpenAI, ChatAnthropic
from langchain.schema.output_parser import StrOutputParser
from langchain.prompts import SystemMessagePromptTemplate
from config import Config

CFG = Config()

class ReviserActor:
    def __init__(self):
        self.model = ChatOpenAI(model=CFG.smart_llm_model)
        self.prompt = SystemMessagePromptTemplate.from_template(
            "You are an expert writer. "
            "You have been tasked by your editor with revising the following draft, which was written by a non-expert. "
            "You may follow the editor's notes or not, as you see fit."
        ) + "Draft:\n\n{draft}" + "Editor's notes:\n\n{notes}"

    @property
    def runnable(self):
        return {
            "draft": {
                "draft": lambda x: x["draft"],
                "notes": lambda x: x["notes"],
            } | self.prompt | self.model | StrOutputParser()
        }
