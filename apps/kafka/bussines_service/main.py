import json
import asyncio
import uvicorn
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from fastapi import FastAPI

KAFKA_BOOTSTRAP_SERVERS = "kafka.default.svc.cluster.local:9092"

app = FastAPI(title="Business Service")


@app.get("/")
def status_index():
    return {"message": "success"}


@app.on_event("startup")
async def on_startup():
    asyncio.create_task(kafka_listener())


async def kafka_listener():
    consumer = AIOKafkaConsumer(
        "process_student_group", "find_group_request",
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="business_service",
        value_deserializer=lambda v: json.loads(v.decode("utf-8"))
    )

    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )

    await consumer.start()
    await producer.start()

    try:
        async for msg in consumer:
            payload = msg.value
            correlation_id = payload.get("correlation_id")

            if msg.topic == "process_student_group":
                students = payload.get("students", [])
                groups = payload.get("groups", [])

                res = []
                for student in students:
                    for group in groups:
                        if student["group_id"] == group["id"]:
                            res.append({
                                "name": student["name"],
                                "group": group["name"]
                            })

                await producer.send_and_wait("student_group_response", {
                    "correlation_id": correlation_id,
                    "info": res
                })

            elif msg.topic == "find_group_request":
                group_id = payload.get("group_id")
                group_name = payload.get("group_name")
                groups_list = payload.get("groups_list", [])

                if group_id is not None:
                    final_group_id = group_id
                else:
                    final_group_id = None
                    for group in groups_list:
                        if group["name"] == group_name:
                            final_group_id = group["id"]
                            break

                await producer.send_and_wait("find_group_response", {
                    "correlation_id": correlation_id,
                    "group_id": final_group_id
                })

    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    uvicorn.run(app, port=8002)
