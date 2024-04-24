from agent import prompts
import pika
import uuid
import json

rabbitConnection = None

class RabbitTaskManager:
    def __init__(self, task, agent, agent_role_prompt):
        """ Initializes the Rabbit Task Manager (1 new Channel per Task) for the main question.
        Args: question (str): The main question to research
        Returns: None
        """
        self.question = task
        self.agent = agent
        self.agent_role_prompt = agent_role_prompt if agent_role_prompt else prompts.generate_agent_role_prompt(agent)
        self.task_id = uuid.uuid4()
        self.channel = None
        self.exchange_name = 'gpt-researcher'
        self.routing_key= 'logs'


    async def create_channel(self):
        global rabbitConnection
        if not rabbitConnection or rabbitConnection.is_closed:
            rabbitConnection = pika.BlockingConnection(pika.ConnectionParameters(blocked_connection_timeout=3600,heartbeat=3600,host='rabbit'))
        
        self.channel = rabbitConnection.channel()
        # This will create the exchange if it doesn't already exist.
        self.channel.exchange_declare(exchange=self.exchange_name, exchange_type='fanout', durable=True)


    def publish_to_rabbit(self, message):
        """ Publishes message to rabbitmq
        Args: message (dict): message to publish
            channel: rabbitmq channel created for the task
        """
        message["task_id"] = f"{self.task_id}"
        message["question"] = self.question
        message["agent"] = self.agent
        message["agent_role_prompt"]= self.agent_role_prompt

        self.channel.basic_publish(exchange=self.exchange_name,
                                routing_key=self.routing_key,
                                body=json.dumps(message),
                                properties=pika.BasicProperties(
                                    delivery_mode = 2,
                                ))
    
    