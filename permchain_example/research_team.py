from operator import itemgetter
from langchain.runnables.openai_functions import OpenAIFunctionsRouter

from permchain.connection_inmemory import InMemoryPubSubConnection
from permchain.pubsub import PubSub
from permchain.topic import Topic

'''
    This is the research team. 
    It is a group of autonomous agents that work together to answer a given question
    using a comprehensive research process that includes: 
        - Searching for relevant information across multiple sources
        - Extracting relevant information
        - Writing a well structured report
        - Validating the report
        - Revising the report
        - Repeat until the report is satisfactory
'''
class ResearchTeam:
    def __init__(self, research_actor, editor_actor, reviser_actor):
        self.research_actor_instance = research_actor
        self.editor_actor_instance = editor_actor
        self.revise_actor_instance = reviser_actor

    def run(self, query):
        # create topics
        editor_inbox = Topic("editor_inbox")
        reviser_inbox = Topic("reviser_inbox")

        research_chain = (
            # Listed in inputs
            Topic.IN.subscribe()
            | {"draft": lambda x: self.research_actor_instance.run(x["question"])}
            # The draft always goes to the editor inbox
            | editor_inbox.publish()
        )

        editor_chain = (
            # Listen for events in the editor_inbox
            editor_inbox.subscribe()
            | self.editor_actor_instance.runnable
            # Depending on the output, different things should happen
            | OpenAIFunctionsRouter({
                # If revise is chosen, we send a push to the critique_inbox
                "revise": (
                        {
                            "notes": itemgetter("notes"),
                            "draft": editor_inbox.current() | itemgetter("draft"),
                            "question": Topic.IN.current() | itemgetter("question"),
                        }
                        | reviser_inbox.publish()
                ),
                # If accepted, then we return
                "accept": editor_inbox.current() | Topic.OUT.publish(),
            })
        )

        reviser_chain = (
            # Listen for events in the reviser's inbox
            reviser_inbox.subscribe()
            | self.revise_actor_instance.runnable
            # Publish to the editor inbox
            | editor_inbox.publish()
        )

        web_researcher = PubSub(
            research_chain,
            editor_chain,
            reviser_chain,
            connection=InMemoryPubSubConnection(),
        )

        res = web_researcher.invoke({"question": query})
        print(res)
        return res["draft"]
