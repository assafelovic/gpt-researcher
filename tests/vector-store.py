import asyncio
import pytest
from typing import List
from gpt_researcher import GPTResearcher

from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS, InMemoryVectorStore
from langchain_core.documents import Document


# taken from https://paulgraham.com/persistence.html
essay = """
The right kind of Stubborn

July 2024

Successful people tend to be persistent. New ideas often don't work at first, but they're not deterred. They keep trying and eventually find something that does.

Mere obstinacy, on the other hand, is a recipe for failure. Obstinate people are so annoying. They won't listen. They beat their heads against a wall and get nowhere.

But is there any real difference between these two cases? Are persistent and obstinate people actually behaving differently? Or are they doing the same thing, and we just label them later as persistent or obstinate depending on whether they turned out to be right or not?

If that's the only difference then there's nothing to be learned from the distinction. Telling someone to be persistent rather than obstinate would just be telling them to be right rather than wrong, and they already know that. Whereas if persistence and obstinacy are actually different kinds of behavior, it would be worthwhile to tease them apart. [1]

I've talked to a lot of determined people, and it seems to me that they're different kinds of behavior. I've often walked away from a conversation thinking either "Wow, that guy is determined" or "Damn, that guy is stubborn," and I don't think I'm just talking about whether they seemed right or not. That's part of it, but not all of it.

There's something annoying about the obstinate that's not simply due to being mistaken. They won't listen. And that's not true of all determined people. I can't think of anyone more determined than the Collison brothers, and when you point out a problem to them, they not only listen, but listen with an almost predatory intensity. Is there a hole in the bottom of their boat? Probably not, but if there is, they want to know about it.

It's the same with most successful people. They're never more engaged than when you disagree with them. Whereas the obstinate don't want to hear you. When you point out problems, their eyes glaze over, and their replies sound like ideologues talking about matters of doctrine. [2]

The reason the persistent and the obstinate seem similar is that they're both hard to stop. But they're hard to stop in different senses. The persistent are like boats whose engines can't be throttled back. The obstinate are like boats whose rudders can't be turned. [3]

In the degenerate case they're indistinguishable: when there's only one way to solve a problem, your only choice is whether to give up or not, and persistence and obstinacy both say no. This is presumably why the two are so often conflated in popular culture. It assumes simple problems. But as problems get more complicated, we can see the difference between them. The persistent are much more attached to points high in the decision tree than to minor ones lower down, while the obstinate spray "don't give up" indiscriminately over the whole tree.

The persistent are attached to the goal. The obstinate are attached to their ideas about how to reach it.

Worse still, that means they'll tend to be attached to their first ideas about how to solve a problem, even though these are the least informed by the experience of working on it. So the obstinate aren't merely attached to details, but disproportionately likely to be attached to wrong ones.



Why are they like this? Why are the obstinate obstinate? One possibility is that they're overwhelmed. They're not very capable. They take on a hard problem. They're immediately in over their head. So they grab onto ideas the way someone on the deck of a rolling ship might grab onto the nearest handhold.

That was my initial theory, but on examination it doesn't hold up. If being obstinate were simply a consequence of being in over one's head, you could make persistent people become obstinate by making them solve harder problems. But that's not what happens. If you handed the Collisons an extremely hard problem to solve, they wouldn't become obstinate. If anything they'd become less obstinate. They'd know they had to be open to anything.

Similarly, if obstinacy were caused by the situation, the obstinate would stop being obstinate when solving easier problems. But they don't. And if obstinacy isn't caused by the situation, it must come from within. It must be a feature of one's personality.

Obstinacy is a reflexive resistance to changing one's ideas. This is not identical with stupidity, but they're closely related. A reflexive resistance to changing one's ideas becomes a sort of induced stupidity as contrary evidence mounts. And obstinacy is a form of not giving up that's easily practiced by the stupid. You don't have to consider complicated tradeoffs; you just dig in your heels. It even works, up to a point.

The fact that obstinacy works for simple problems is an important clue. Persistence and obstinacy aren't opposites. The relationship between them is more like the relationship between the two kinds of respiration we can do: aerobic respiration, and the anaerobic respiration we inherited from our most distant ancestors. Anaerobic respiration is a more primitive process, but it has its uses. When you leap suddenly away from a threat, that's what you're using.

The optimal amount of obstinacy is not zero. It can be good if your initial reaction to a setback is an unthinking "I won't give up," because this helps prevent panic. But unthinking only gets you so far. The further someone is toward the obstinate end of the continuum, the less likely they are to succeed in solving hard problems. [4]



Obstinacy is a simple thing. Animals have it. But persistence turns out to have a fairly complicated internal structure.

One thing that distinguishes the persistent is their energy. At the risk of putting too much weight on words, they persist rather than merely resisting. They keep trying things. Which means the persistent must also be imaginative. To keep trying things, you have to keep thinking of things to try.

Energy and imagination make a wonderful combination. Each gets the best out of the other. Energy creates demand for the ideas produced by imagination, which thus produces more, and imagination gives energy somewhere to go. [5]

Merely having energy and imagination is quite rare. But to solve hard problems you need three more qualities: resilience, good judgement, and a focus on some kind of goal.

Resilience means not having one's morale destroyed by setbacks. Setbacks are inevitable once problems reach a certain size, so if you can't bounce back from them, you can only do good work on a small scale. But resilience is not the same as obstinacy. Resilience means setbacks can't change your morale, not that they can't change your mind.

Indeed, persistence often requires that one change one's mind. That's where good judgement comes in. The persistent are quite rational. They focus on expected value. It's this, not recklessness, that lets them work on things that are unlikely to succeed.

There is one point at which the persistent are often irrational though: at the very top of the decision tree. When they choose between two problems of roughly equal expected value, the choice usually comes down to personal preference. Indeed, they'll often classify projects into deliberately wide bands of expected value in order to ensure that the one they want to work on still qualifies.

Empirically this doesn't seem to be a problem. It's ok to be irrational near the top of the decision tree. One reason is that we humans will work harder on a problem we love. But there's another more subtle factor involved as well: our preferences among problems aren't random. When we love a problem that other people don't, it's often because we've unconsciously noticed that it's more important than they realize.

Which leads to our fifth quality: there needs to be some overall goal. If you're like me you began, as a kid, merely with the desire to do something great. In theory that should be the most powerful motivator of all, since it includes everything that could possibly be done. But in practice it's not much use, precisely because it includes too much. It doesn't tell you what to do at this moment.

So in practice your energy and imagination and resilience and good judgement have to be directed toward some fairly specific goal. Not too specific, or you might miss a great discovery adjacent to what you're searching for, but not too general, or it won't work to motivate you. [6]

When you look at the internal structure of persistence, it doesn't resemble obstinacy at all. It's so much more complex. Five distinct qualities — energy, imagination, resilience, good judgement, and focus on a goal — combine to produce a phenomenon that seems a bit like obstinacy in the sense that it causes you not to give up. But the way you don't give up is completely different. Instead of merely resisting change, you're driven toward a goal by energy and resilience, through paths discovered by imagination and optimized by judgement. You'll give way on any point low down in the decision tree, if its expected value drops sufficiently, but energy and resilience keep pushing you toward whatever you choose higher up.

Considering what it's made of, it's not surprising that the right kind of stubbornness is so much rarer than the wrong kind, or that it gets so much better results. Anyone can do obstinacy. Indeed, kids and drunks and fools are best at it. Whereas very few people have enough of all five of the qualities that produce the right kind of stubbornness, but when they do the results are magical.







Notes

[1] I'm going to use "persistent" for the good kind of stubborn and "obstinate" for the bad kind, but I can't claim I'm simply following current usage. Conventional opinion barely distinguishes between good and bad kinds of stubbornness, and usage is correspondingly promiscuous. I could have invented a new word for the good kind, but it seemed better just to stretch "persistent."

[2] There are some domains where one can succeed by being obstinate. Some political leaders have been notorious for it. But it won't work in situations where you have to pass external tests. And indeed the political leaders who are famous for being obstinate are famous for getting power, not for using it well.

[3] There will be some resistance to turning the rudder of a persistent person, because there's some cost to changing direction.

[4] The obstinate do sometimes succeed in solving hard problems. One way is through luck: like the stopped clock that's right twice a day, they seize onto some arbitrary idea, and it turns out to be right. Another is when their obstinacy cancels out some other form of error. For example, if a leader has overcautious subordinates, their estimates of the probability of success will always be off in the same direction. So if he mindlessly says "push ahead regardless" in every borderline case, he'll usually turn out to be right.

[5] If you stop there, at just energy and imagination, you get the conventional caricature of an artist or poet.

[6] Start by erring on the small side. If you're inexperienced you'll inevitably err on one side or the other, and if you err on the side of making the goal too broad, you won't get anywhere. Whereas if you err on the small side you'll at least be moving forward. Then, once you're moving, you expand the goal.
"""


def load_document():
    document = [Document(page_content=essay)]
    text_splitter = CharacterTextSplitter(chunk_size=200, chunk_overlap=30, separator="\n")
    return text_splitter.split_documents(documents=document)


def create_vectorstore(documents: List[Document]):
    embeddings = OpenAIEmbeddings()
    return FAISS.from_documents(documents, embeddings)

@pytest.mark.asyncio
async def test_gpt_researcher_with_vector_store():
    docs = load_document()
    vectorstore = create_vectorstore(docs)

    query = """
        Summarize the essay into 3 or 4 succint sections.
        Make sure to include key points regarding the differences between
        persistance vs obstinate.

        Include some recommendations for entrepeneurs in the conclusion.
        Recommend some ways to increase persistance in a healthy way.
    """


    # Create an instance of GPTResearcher
    researcher = GPTResearcher(
        query=query,
        report_type="research_report",
        report_source="langchain_vectorstore",
        vector_store=vectorstore,
    )

    # Conduct research and write the report
    await researcher.conduct_research()
    report = await researcher.write_report()

    assert report is not None

@pytest.mark.asyncio
async def test_store_in_vector_store_web():
    vector_store = InMemoryVectorStore(embedding=OpenAIEmbeddings())
    query = "Which one is the best LLM"

    researcher = GPTResearcher(
        query=query,
        report_type="research_report",
        report_source="web",
        vector_store=vector_store,
    )

    await researcher.conduct_research()

    related_contexts = await vector_store.asimilarity_search("GPT-4", k=2)

    assert len(related_contexts) == 2
    # Add more assertions as needed to verify the results


@pytest.mark.asyncio
async def test_store_in_vector_store_urls():
    vector_store = InMemoryVectorStore(embedding=OpenAIEmbeddings())
    query = "Who won the world cup in 2022"

    researcher = GPTResearcher(
        query=query,
        report_type="research_report",
        vector_store=vector_store,
        source_urls=["https://en.wikipedia.org/wiki/FIFA_World_Cup"]
    )

    await researcher.conduct_research()

    related_contexts = await vector_store.asimilarity_search("GPT-4", k=2)

    assert len(related_contexts) == 2


@pytest.mark.asyncio
async def test_store_in_vector_store_langchain_docs():
    vector_store = InMemoryVectorStore(embedding=OpenAIEmbeddings())
    docs = load_document()
    query = "What does successful people tend to do?"

    researcher = GPTResearcher(
        query=query,
        report_type="research_report",
        vector_store=vector_store,
        report_source="langchain_documents",
        documents=docs
    )

    await researcher.conduct_research()

    related_contexts = await vector_store.asimilarity_search("GPT-4", k=2)

    assert len(related_contexts) == 2

@pytest.mark.asyncio
async def test_store_in_vector_store_locals():
    vector_store = InMemoryVectorStore(embedding=OpenAIEmbeddings())
    query = "What is transformer?"

    researcher = GPTResearcher(
        query=query,
        report_type="research_report",
        vector_store=vector_store,
        report_source="local",
        config_path= "test_local"
    )

    await researcher.conduct_research()

    related_contexts = await vector_store.asimilarity_search("GPT-4", k=2)

    assert len(related_contexts) == 2

@pytest.mark.asyncio
async def test_store_in_vector_store_hybrids():
    vector_store = InMemoryVectorStore(embedding=OpenAIEmbeddings())
    query = "What is transformer?"
    
    researcher = GPTResearcher(
        query=query,
        report_type="research_report",
        vector_store=vector_store,
        report_source="hybrid",
        config_path= "test_local"
    )
    
    await researcher.conduct_research()
    
    related_contexts = await vector_store.asimilarity_search("GPT-4", k=2)
    
    assert len(related_contexts) == 2
