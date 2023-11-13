from permchain.connection_inmemory import InMemoryPubSubConnection
from permchain.pubsub import PubSub
from permchain.topic import Topic


class Researcher:
    def __init__(self, search_actor, writer_actor):
        self.search_actor_instance = search_actor
        self.writer_actor_instance = writer_actor

    def run(self, query):
        # The research inbox
        research_inbox = Topic("research")
        search_actor = (
            Topic.IN.subscribe()
            | {
                "query": lambda x: x,
                "results": self.search_actor_instance.runnable
            }
            | research_inbox.publish()
        )

        write_actor = (
            research_inbox.subscribe()
            | self.writer_actor_instance.runnable
            | Topic.OUT.publish()
        )

        researcher = PubSub(
            search_actor,
            write_actor,
            connection=InMemoryPubSubConnection(),
        )

        res = researcher.invoke(query)
        return res["answer"]
