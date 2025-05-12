import asyncio
import json
from typing import Callable, Awaitable
from aio_pika import connect_robust, IncomingMessage, Message, ExchangeType

class RpcConsumer:
    def __init__(self, amqp_url: str):
        self.amqp_url = amqp_url
        self.handlers: dict[str, Callable[[dict], Awaitable[dict]]] = {}
        self.channel = None
        self.exchange = None

    def register_handler(self, routing_key: str, handler: Callable[[dict], Awaitable[dict]]):
        self.handlers[routing_key] = handler

    async def start(self):
        connection = await connect_robust(self.amqp_url)
        self.channel = await connection.channel()
        await self.channel.set_qos(prefetch_count=10)

        self.exchange = await self.channel.declare_exchange(
            name="rpc_direct",
            type=ExchangeType.DIRECT,
            durable=True
        )
        self.exchange = await self.channel.get_exchange("rpc_direct")
        for routing_key, handler in self.handlers.items():
            queue = await self.channel.declare_queue(routing_key, durable=True)
            await queue.bind(self.exchange, routing_key)
            await queue.consume(self._create_callback(handler), no_ack=False)

    def _create_callback(self, handler: Callable[[dict], Awaitable[dict]]):
        async def callback(message: IncomingMessage):
            try:
                async with message.process():
                    data = json.loads(message.body)
                    result = await handler(data)

                    if message.reply_to and message.correlation_id:
                        reply = Message(
                            body=json.dumps(result).encode(),
                            correlation_id=message.correlation_id,
                            content_type="application/json"
                        )
                        await self.exchange.publish(
                            reply,
                            routing_key=message.reply_to
                        )

                    print("✅ Message processed and acknowledged")

            except Exception as e:
                print(f"❌ Error in handler for {message.routing_key}: {e}")
                await message.nack(requeue=False)

        return callback


