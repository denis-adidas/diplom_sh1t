import asyncio
import uuid
import json
from aio_pika import connect_robust, Message, IncomingMessage, ExchangeType

class RpcClient:
    def __init__(self, amqp_url: str):
        self.amqp_url = amqp_url
        self.futures = {}
        self.channel = None
        self.exchange = None
        self.callback_queue = None

    async def connect(self):
        connection = await connect_robust(self.amqp_url)
        self.channel = await connection.channel()
        self.exchange = await self.channel.declare_exchange(
            name="rpc_direct",
            type=ExchangeType.DIRECT,
            durable=True
        )
        self.callback_queue = await self.channel.declare_queue(exclusive=True)
        await self.callback_queue.bind(self.exchange, routing_key=self.callback_queue.name)
        await self.callback_queue.consume(self.on_response)

    async def on_response(self, message: IncomingMessage):
        correlation_id = message.correlation_id
        if correlation_id in self.futures:
            future = self.futures.pop(correlation_id)
            future.set_result(json.loads(message.body))
        await message.ack()

    async def call(self, routing_key: str, payload: dict, timeout: float = 60.0) -> dict:
        correlation_id = str(uuid.uuid4())
        future = asyncio.get_running_loop().create_future()
        self.futures[correlation_id] = future

        message = Message(
            body=json.dumps(payload).encode(),
            correlation_id=correlation_id,
            reply_to=self.callback_queue.name,
            content_type="application/json"
        )

        await self.exchange.publish(message, routing_key=routing_key)

        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            self.futures.pop(correlation_id, None)
            raise TimeoutError(f"RPC call to {routing_key} timed out after {timeout} seconds")

