from aiokafka import AIOKafkaProducer
import json

class KafkaManager:
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None

    async def start(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )
        await self.producer.start()

    async def stop(self):
        await self.producer.stop()

    async def send(self, topic: str, value: dict):
        await self.producer.send_and_wait(topic, value)
