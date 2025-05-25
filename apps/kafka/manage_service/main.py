import uvicorn
from fastapi import FastAPI, Body
from uuid import uuid4
import asyncio
from datetime import datetime
from aiokafka import AIOKafkaConsumer
from collections import defaultdict
from aiokafka.structs import TopicPartition
from kafka_producer import KafkaManager
from kafka_consumer import KafkaResponseConsumer, pending_results
from config import settings
from models import PostCreateStudent

app = FastAPI(title="Manage Service (Kafka)")
kafka = KafkaManager(settings.KAFKA_BOOTSTRAP_SERVERS)
consumer = KafkaResponseConsumer(settings.KAFKA_BOOTSTRAP_SERVERS, topics=[
    "students_response",
    "groups_response",
    "student_group_response",
    "create_student_full_response",
    "find_group_response"
])

async def log_kafka_queue_sizes(interval=5):
    consumer = AIOKafkaConsumer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="monitoring_group",
        enable_auto_commit=False
    )
    await consumer.start()
    try:
        topics = [
            "get_students",
            "get_groups",
            "process_student_group",
            "find_group_request",
            "create_student_full"
        ]
        while True:
            topic_sizes = defaultdict(dict)

            for topic in topics:
                partitions = consumer.partitions_for_topic(topic)
                if not partitions:
                    continue
                for p in partitions:
                    tp = TopicPartition(topic, p)
                    end_offset = await consumer.end_offsets([tp])
                    topic_sizes[topic][p] = end_offset[tp]

            now = datetime.now().isoformat(timespec="seconds")
            for topic, parts in topic_sizes.items():
                for p, offset in parts.items():
                    print(f"[{now}] [KAFKA] {topic} [partition {p}]: offset={offset}")

            await asyncio.sleep(interval)
    finally:
        await consumer.stop()



@app.on_event("startup")
async def startup():
    await kafka.start()
    await consumer.start()
    asyncio.create_task(log_kafka_queue_sizes(interval=5))

@app.on_event("shutdown")
async def shutdown():
    await kafka.stop()
    await consumer.stop()

@app.get("/get/students")
async def get_student_list():
    correlation_id = str(uuid4())
    future = asyncio.get_event_loop().create_future()
    pending_results[correlation_id] = future

    await kafka.send("get_students", {"correlation_id": correlation_id})
    try:
        result = await asyncio.wait_for(future, timeout=60)
        return result
    except asyncio.TimeoutError:
        return {"error": "timeout while waiting for students_response"}
    finally:
        pending_results.pop(correlation_id, None)

@app.get("/get/stud_info")
async def student_with_groups_list():
    correlation_id = str(uuid4())

    future = asyncio.get_event_loop().create_future()
    pending_results[correlation_id] = future

    await kafka.send("get_students", {"correlation_id": correlation_id})
    await kafka.send("get_groups", {"correlation_id": correlation_id})
    await kafka.send("process_student_group", {"correlation_id": correlation_id})

    try:
        result = await asyncio.wait_for(future, timeout=60)
        return result
    except asyncio.TimeoutError:
        return {"error": "timeout while waiting for student_group_response"}
    finally:
        pending_results.pop(correlation_id, None)

@app.post("/post/create/student")
async def post_create_student(body: PostCreateStudent = Body(...)):
    correlation_id = str(uuid4())
    future = asyncio.get_event_loop().create_future()
    pending_results[correlation_id] = future

    # 1. Запрашиваем все группы
    await kafka.send("get_groups", {"correlation_id": correlation_id})
    groups_response = await asyncio.wait_for(future, timeout=60)
    groups_list = groups_response["groups"]

    # 2. Запрашиваем group_id у бизнес-сервиса
    correlation_id2 = str(uuid4())
    future2 = asyncio.get_event_loop().create_future()
    pending_results[correlation_id2] = future2

    await kafka.send("find_group_request", {
        "correlation_id": correlation_id2,
        "student": body.model_dump(exclude_none=True),
        "groups_list": groups_list
    })

    group_id_response = await asyncio.wait_for(future2, timeout=60)
    group_id = group_id_response["group_id"]

    # 3. Отправляем финальный create_student_full
    correlation_id3 = str(uuid4())
    future3 = asyncio.get_event_loop().create_future()
    pending_results[correlation_id3] = future3

    await kafka.send("create_student_full", {
        "correlation_id": correlation_id3,
        "student": {
            "name": body.name,
            "group_id": group_id
        }
    })
    print(f"[manage_service] Sent create_student_full with group_id={group_id}")

    await asyncio.wait_for(future3, timeout=60)
    return {"message": "success"}


if __name__ == "__main__":
    uvicorn.run(app, port=8000)
