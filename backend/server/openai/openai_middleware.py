import asyncio
from datetime import datetime
import json
import logging
import re
import time
import traceback
from typing import (
    Annotated,
    List,
    Literal,
    Optional,
    cast,
    TypeAlias,
)
import uuid
from fastapi import APIRouter
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel, Field
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    BaseMessage,
    AIMessageChunk,
    AIMessage,
    HumanMessage,
)
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import (
    StrOutputParser,
    PydanticToolsParser,
)
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
)
from langchain_core.tools import tool, InjectedToolArg
from langchain_core.vectorstores import InMemoryVectorStore

from backend.chat.chat import ChatAgentWithMemory
from backend.server.openai.OpenAiResponseFormatter import OpenAiResponseFormatter
from backend.server.server_utils import get_file_path, run_research
from backend.server.openai.sse_websocket_adapter import (
    SseWebSocketAdapter,
)
from backend.server import websocket_manager

from gpt_researcher.config.config import Config
from gpt_researcher.memory.embeddings import Memory
from gpt_researcher.utils.enum import ReportSource, Tone, ReportType
from gpt_researcher.utils.llm import get_llm


router = APIRouter()
logger = logging.getLogger(__name__)


class JsonMessage(BaseModel):
    role: str
    content: str


class ChatCompletionsRequest(BaseModel):
    model: str
    messages: List[JsonMessage]
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[List[str]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = 0
    frequency_penalty: Optional[float] = 0
    user: Optional[str] = None
    metadata: Optional[dict] = None


def json_to_langchain_messages(messages: List[JsonMessage]) -> List[BaseMessage]:
    langchain_messages = []
    for message in messages:
        if message.role == "user":
            langchain_messages.append(HumanMessage(content=message.content))
        elif message.role == "assistant":
            langchain_messages.append(AIMessage(content=message.content))
        elif message.role == "system":
            # ignore system messages from the user
            pass
        else:
            raise ValueError(f"Unsupported role: {message.role}")
    return langchain_messages


class ChatCompletionsResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[dict]


class ModelsResponse(BaseModel):
    object: str
    data: List[dict]


class ModelResponse(BaseModel):
    id: str
    object: str
    created: int
    owned_by: str


@router.get("/models", response_model=ModelsResponse)
async def list_models():
    response = {
        "object": "list",
        "data": [
            {
                "id": "gpt-researcher",
                "object": "model",
                "created": 0,
                "owned_by": "gpt-researcher",
            },
        ],
    }
    return response


@router.get("/models/{model}", response_model=ModelResponse)
async def retrieve_model(model: str):
    response = {
        "id": model,
        "object": "model",
        "created": 0,
        "owned_by": "gpt-researcher",
    }
    return response


cfg = Config()
smart_chat_model = cast(
    BaseChatModel,
    get_llm(
        llm_provider=cfg.smart_llm_provider,
        model=cfg.smart_llm_model,
        temperature=0.5,
        top_p=0.9,
        max_tokens=cfg.smart_token_limit,  # type: ignore
        **cfg.llm_kwargs,
    ).llm,
)

fast_chat_model = cast(
    BaseChatModel,
    get_llm(
        llm_provider=cfg.fast_llm_provider,
        model=cfg.fast_llm_model,
        temperature=0.5,
        max_tokens=cfg.fast_token_limit,  # type: ignore
        **cfg.llm_kwargs,
    ).llm,
)


research_type_descriptions = {
    ReportType.ResearchReport: "A brief summary, ~2 min",
    ReportType.DeepResearch: "advanced recursive deep research workflow",
    ReportType.MultiAgents: "leveraging multiple agents with specialized skills",
}


class BaseResearchTaskMetaData(BaseModel):
    """Base class for research task metadata."""

    report_tone: Literal[
        Tone.Analytical,
        Tone.Speculative,
        Tone.Critical,
        Tone.Formal,
        Tone.Objective,
        Tone.Persuasive,
    ] = Field(
        description="Highly prefer one of following report tones: \n"
        f" - {Tone.Analytical}\n"
        f" - {Tone.Speculative}\n"
        f" - {Tone.Critical}\n"
    )
    research_type: Literal[
        ReportType.ResearchReport, ReportType.DeepResearch, ReportType.MultiAgents
    ] = Field(
        description="Highly prefer one of following research types: \n"
        + "\n".join(f"  - {k}: {v}" for k, v in research_type_descriptions.items())
    )
    research_prompt: str = Field(
        description="The prompt that is passed to the next agent for the research task."
        "It should be the user input or a revised prompt based on the user input."
        "Include as much information as possible to get the best results.",
    )


class ResearchTaskMetadata(BaseResearchTaskMetaData):
    task_id: Annotated[int, InjectedToolArg]
    task_name: str = Field(description="Should be in snake_case.")
    message_index: int | None = Field(None, description="Injected parameter.")


@tool
async def propose_research_task(
    metadata: BaseResearchTaskMetaData,
    sse_writer: Annotated[SseWebSocketAdapter, InjectedToolArg],
) -> None:
    """Propose a research task to user."""
    await sse_writer.send_text(
        "Would you like to proceed with the proposed research task as outlined, or would you like me to provide more information or adjust the parameters?"
    )
    await sse_writer.send_text("\n## Proposed Research Task\n")
    for k, v in metadata.model_dump().items():
        await sse_writer.send_text(f"  - **{k.replace('_', ' ').title()}**: {v}")
        if k == "research_type" and v in research_type_descriptions:
            await sse_writer.send_text(f" ({research_type_descriptions[v]})")
        await sse_writer.send_text("\n")


# to debug schema, start_research.tool_call_schema.model_json_schema()
@tool
async def start_research(
    metadata: ResearchTaskMetadata,
    sse_writer: Annotated[SseWebSocketAdapter, InjectedToolArg],
) -> None:
    """Start a research task."""
    await sse_writer.send_text(
        f"\n```research_task_metadata\n{metadata.model_dump_json(indent=2, exclude_none=True)}\n```\n"
    )

    await run_research(
        websocket=sse_writer,
        task=metadata.research_prompt,
        report_type=metadata.research_type,
        source_urls=[],
        document_urls=["./my-docs"],
        tone=metadata.report_tone.name,
        headers={},
        report_source=ReportSource.Web,
        query_domains=[],
        manager=websocket_manager,
        task_id=metadata.task_id,
        task_name=metadata.task_name,
    )


str_output_parser = StrOutputParser()

TriageResultValue: TypeAlias = Literal["fast", "research"]


class TriageResult(BaseModel):
    value: TriageResultValue = Field(
        ...,
        description=(
            "'fast' agent for very simple tasks like `generating a title`. "
            "'research' agent for tasks that require research workflow or external data."
        ),
    )


triage_agent = (
    ChatPromptTemplate.from_messages(
        (
            SystemMessagePromptTemplate.from_template(
                "Today is {today_date}. decide which agent to handle the request."
            ),
            MessagesPlaceholder("messages"),
        )
    )
    | fast_chat_model.with_structured_output(TriageResult)
    | RunnableLambda[TriageResult, TriageResultValue](lambda r: r.value)
)

research_tools = [propose_research_task, start_research]
research_tools_parser = PydanticToolsParser(tools=research_tools)
research_model = smart_chat_model.bind_tools(research_tools)
research_prompt = ChatPromptTemplate.from_messages(
    (
        SystemMessagePromptTemplate.from_template(
            "Decide if you need to start a research tool call. note that today is {today_date}."
            "If you have enough info, propose a research task. always wait for user to confirm first."
            "Else ask for necessary info to suggest the parameters."
            "If user confirms, start the research task."
        ),
        MessagesPlaceholder("messages"),
    )
)
research_agent = research_prompt | research_model


async def triage_request(
    messages: List[BaseMessage],
) -> tuple[Literal[TriageResultValue, "follow_up"], ResearchTaskMetadata | None]:
    pattern = r"\s*```research_task_metadata\s+([\s\S]*?)```"
    for i, message in enumerate(messages):
        if isinstance(message, AIMessage):
            content = str_output_parser.invoke(message)
            if match := re.search(pattern, content):
                json_data = json.loads(match.group(1))
                json_data["message_index"] = i
                return "follow_up", ResearchTaskMetadata(**json_data)

    today_date = datetime.now().strftime("%Y-%m-%d")
    result = await triage_agent.ainvoke(
        {"today_date": today_date, "messages": messages}
    )
    return result, None


async def prepare_research(
    messages: List[BaseMessage],
    sse_writer: SseWebSocketAdapter,
    request: ChatCompletionsRequest,
):
    today_date = datetime.now().strftime("%Y-%m-%d")
    chunks = research_agent.astream({"today_date": today_date, "messages": messages})
    tool_call_message = None
    async for chunk in chunks:
        if isinstance(chunk, AIMessageChunk) and chunk.tool_call_chunks:
            if tool_call_message is None:
                tool_call_message = chunk
            else:
                tool_call_message = cast(AIMessageChunk, tool_call_message + chunk)
            continue
        else:
            content = str_output_parser.invoke(chunk)
            if content:
                await sse_writer.send_text(content)
    if tool_call_message:
        if not request.stream:
            await sse_writer.send_text(
                "Please enable streaming response for this request."
            )
            return

        for tool_call in tool_call_message.tool_calls:
            if tool_call["name"] == "propose_research_task":
                tool_call["args"]["sse_writer"] = sse_writer
                # metadata = BaseResearchTaskMetaData.model_validate(tool_call["args"])
                await propose_research_task.ainvoke(tool_call)
            elif tool_call["name"] == "start_research":
                tool_call["args"]["metadata"]["task_id"] = int(time.time())
                tool_call["args"]["sse_writer"] = sse_writer
                # metadata = ResearchTaskMetadata.model_validate(tool_call["args"])
                await start_research.ainvoke(tool_call)
            else:
                raise ValueError(f"Unknown tool call: {tool_call['name']}")


if not cfg.embedding_provider or not cfg.embedding_model:
    raise ValueError("Embedding provider or model not found.")
embedding = Memory(
    cfg.embedding_provider, cfg.embedding_model, **cfg.embedding_kwargs
).get_embeddings()


async def followup_research(
    messages: List[BaseMessage],
    task_metadata: ResearchTaskMetadata,
    sse_writer: SseWebSocketAdapter,
):
    vector_store_path = get_file_path(
        task_metadata.task_id, task_metadata.task_name, "vector_store"
    )

    vector_store = None
    if vector_store_path.exists():
        try:
            vector_store = InMemoryVectorStore.load(str(vector_store_path), embedding)
            logger.debug(f"vector_store loaded. {vector_store_path}")
        except Exception as e:
            logger.error(f"Error loading vector store: {e}")

    message_index = task_metadata.message_index
    if not isinstance(message_index, int):
        raise ValueError("message_index is required for follow up research.")

    report = str_output_parser.invoke(messages[message_index])

    followup_agent = ChatAgentWithMemory(
        report=report,
        config_path="default",
        headers=None,
        vector_store=vector_store,
    )

    if not vector_store:
        vector_store = followup_agent.vector_store
        if not vector_store:
            raise ValueError("Vector store not found.")
        # persist the vector store
        vector_store.dump(str(vector_store_path))

    messages_copy = messages.copy()
    messages_copy[message_index] = AIMessage(
        "Research is done. Report is added to the vector store."
    )
    await followup_agent.chat(messages_copy, sse_writer)


async def workflow(
    request: ChatCompletionsRequest,
    sse_writer: SseWebSocketAdapter,
):
    try:
        messages = json_to_langchain_messages(request.messages)
        triage_result, research_task_metadata = await triage_request(messages)
        if triage_result == "fast":
            async for chunk in fast_chat_model.astream(messages):
                await sse_writer.send_text(str_output_parser.invoke(chunk))
            return
        elif triage_result == "research":
            await prepare_research(messages, sse_writer, request)
            return
        elif triage_result == "follow_up" and research_task_metadata:
            await followup_research(messages, research_task_metadata, sse_writer)
            return
        else:
            raise ValueError(f"Unknown triage result: {triage_result}")
    except asyncio.CancelledError:
        logger.info("workflow cancelled")
        raise
    except Exception as e:
        logger.error(f"Error processing request: {e}\n{traceback.format_exc()}")
        await sse_writer.send_text(f"Error: {e}")


@router.post("/chat/completions", response_model=ChatCompletionsResponse)
async def create_completion(request: ChatCompletionsRequest):
    response_id = str(uuid.uuid4())
    created_time = int(time.time())

    sse_formatter = OpenAiResponseFormatter(
        response_id, created_time, request.stream or False
    )
    sse_writer = SseWebSocketAdapter(sse_formatter)

    async def start_workflow():
        try:
            await workflow(request, sse_writer)
        finally:
            await sse_writer.close()

    workflow_task = asyncio.create_task(start_workflow())

    if request.stream:

        async def stream_generator():
            try:
                async for chunk in sse_writer:
                    yield chunk
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(f"Error stream_generator response: {e}")
            finally:
                if not workflow_task.done():
                    workflow_task.cancel()

        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    else:
        return Response(await sse_writer, media_type="application/json")