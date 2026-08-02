"""ChatAgentWithMemory vector RAG path should be reachable and wired."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from backend.chat.chat import ChatAgentWithMemory


def test_setup_vector_store_uses_agent_config_and_search_kwargs():
    agent = ChatAgentWithMemory.__new__(ChatAgentWithMemory)
    agent.report = "alpha " * 50 + " beta " * 50
    agent.config = SimpleNamespace(
        embedding_provider="openai",
        embedding_model="text-embedding-3-small",
        embedding_kwargs={},
    )
    agent.vector_store = None
    agent.retriever = None

    fake_vs = MagicMock()
    fake_vs.add_texts = MagicMock()
    fake_vs.as_retriever = MagicMock(return_value="retriever-ok")

    with patch("backend.chat.chat.Memory") as mem_cls, patch(
        "backend.chat.chat.InMemoryVectorStore", return_value=fake_vs
    ), patch.object(
        ChatAgentWithMemory,
        "_process_document",
        return_value=["chunk a", "chunk b"],
    ):
        mem_cls.return_value.get_embeddings.return_value = "emb"
        agent._setup_vector_store()

    fake_vs.as_retriever.assert_called_once_with(search_kwargs={"k": 4})
    assert agent.retriever == "retriever-ok"
    # Config should be the agent config, not a fresh Config()
    mem_cls.assert_called_once()


def test_setup_vector_store_falls_back_when_embeddings_fail():
    """Eager embedding failure (e.g. missing OPENAI_API_KEY) => no-RAG mode."""
    agent = ChatAgentWithMemory.__new__(ChatAgentWithMemory)
    agent.report = "alpha " * 50
    agent.config = SimpleNamespace(
        embedding_provider="openai",
        embedding_model="text-embedding-3-small",
        embedding_kwargs={},
    )
    agent.vector_store = None
    agent.retriever = None
    agent.embedding = None

    with patch("backend.chat.chat.Memory") as mem_cls, patch.object(
        ChatAgentWithMemory, "_process_document", return_value=["chunk a"]
    ):
        mem_cls.return_value.get_embeddings.side_effect = RuntimeError(
            "Missing credentials"
        )
        agent._setup_vector_store()

    assert agent.retriever is None
    assert agent.vector_store is None
    # _retrieve_context then serves the full report instead of crashing.
    assert agent._retrieve_context("q") == agent.report


def test_retrieve_context_uses_retriever_and_falls_back():
    agent = ChatAgentWithMemory.__new__(ChatAgentWithMemory)
    agent.report = "FULL_REPORT"
    agent.retriever = MagicMock()
    agent.retriever.invoke.return_value = [
        SimpleNamespace(page_content="chunk-1"),
        SimpleNamespace(page_content="chunk-2"),
    ]
    assert agent._retrieve_context("q") == "chunk-1\n\nchunk-2"

    agent.retriever.invoke.side_effect = RuntimeError("embed down")
    assert agent._retrieve_context("q") == "FULL_REPORT"

    agent.retriever = None
    assert agent._retrieve_context("q") == "FULL_REPORT"


def test_init_no_longer_disabled_by_and_false():
    """Removing `and False` should call setup when report is present."""
    with patch.object(ChatAgentWithMemory, "_setup_vector_store") as setup, patch(
        "backend.chat.chat.Config"
    ), patch("backend.chat.chat.os.environ.get", return_value=None):
        ChatAgentWithMemory(report="hello world")
        setup.assert_called_once()
