from aiokafka import AIOKafkaConsumer
import asyncio
import json

pending_results = {}

class KafkaResponseConsumer:
    def __init__(self, servers: str, topics: list[str]):
        self.servers = servers
        self.topics = topics
        self.consumer = None
        self._running = False

    async def start(self):
        self.consumer = AIOKafkaConsumer(
            *self.topics,
            bootstrap_servers=self.servers,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            group_id="manage_service_consumer",
            auto_offset_reset="earliest"
        )

        await self.consumer.start()
        self._running = True
        asyncio.create_task(self.consume())

    async def stop(self):
        self._running = False
        if self.consumer:
            await self.consumer.stop()

    async def consume(self):
        while self._running:
            async for msg in self.consumer:
                data = msg.value
                correlation_id = data.get("correlation_id")
                print(f"[manage_service] Got message on topic '{msg.topic}': {data}")

                if correlation_id in pending_results:
                    pending_results[correlation_id].set_result(data)
