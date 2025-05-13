from aiokafka import AIOKafkaConsumer
import asyncio
import json

pending_results = {}

class KafkaResponseConsumer:
    def __init__(self, bootstrap_servers: str, topics: list[str]):
        self.bootstrap_servers = bootstrap_servers
        self.topics = topics
        self.consumer = None

    async def start(self):
        self.consumer = AIOKafkaConsumer(
            *self.topics,
            bootstrap_servers=self.bootstrap_servers,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            group_id="manage_service"
        )
        await self.consumer.start()
        asyncio.create_task(self.consume())

    async def stop(self):
        if self.consumer:
            await self.consumer.stop()

    async def consume(self):
        async for msg in self.consumer:
            data = msg.value
            correlation_id = data.get("correlation_id")

            future = pending_results.get(correlation_id)
            if future and not future.done():
                future.set_result(data)

