import asyncio
import json

from fastapi import FastAPI
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import uvicorn

app = FastAPI(title="Business Service")

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"

@app.on_event("startup")
async def startup():
    asyncio.create_task(kafka_listener())


async def kafka_listener():
    consumer = AIOKafkaConsumer(
        "find_group_request",
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="business_service",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest"
    )
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )

    await consumer.start()
    await producer.start()
    print("[business_service] Kafka consumer and producer started")

    try:
        async for msg in consumer:
            print(f"[business_service] Received topic: {msg.topic}")
            try:
                data = msg.value
                correlation_id = data["correlation_id"]
                student = data["student"]
                groups_list = data["groups_list"]

                group_id = student.get("group_id")

                if group_id is None:
                    group_name = student.get("group_name")
                    for group in groups_list:
                        if group["name"] == group_name:
                            group_id = group["id"]
                            break

                    if group_id is None:
                        print(f"[business_service] Group '{group_name}' not found. Creating...")
                        await producer.send_and_wait("create_group", {
                            "correlation_id": correlation_id,
                            "group_name": group_name
                        })
                        continue  # Ждём, что data_service сам отправит find_group_response

                print(f"[business_service] Returning group_id={group_id}")
                await producer.send_and_wait("find_group_response", {
                    "correlation_id": correlation_id,
                    "group_id": group_id
                })

            except Exception as e:
                print(f"[business_service] Error processing message: {e}")

    finally:
        await consumer.stop()
        await producer.stop()
        print("[business_service] Kafka consumer and producer stopped")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
