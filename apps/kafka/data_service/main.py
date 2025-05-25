from enum import StrEnum
import json
import asyncio
import uvicorn

from fastapi import FastAPI, Body
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from config import settings

from models import (
    PostNewStudentBody,
    PostUpdateStudentBody,
    PostUpdateGroupBody,
    PostNewGroupBody
)
from query.orm import AsyncORM
from database import init_models

app = FastAPI(title="Data service")


class apis(StrEnum):
    students = "Students"
    groups = "Groups"


@app.get("/")
def status_index():
    return {"message": "success"}


@app.on_event("startup")
async def on_startup():
    await init_models()
    asyncio.create_task(kafka_listener())


async def kafka_listener():
    consumer = AIOKafkaConsumer(
        "get_students",
        "get_groups",
        "create_student_full",
        "create_group",
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="data_service",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )

    producer = AIOKafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )

    await consumer.start()
    await producer.start()

    try:
        async for msg in consumer:
            print(f"[kafka] TOPIC: {msg.topic!r}")
            data = msg.value
            correlation_id = data.get("correlation_id")

            if msg.topic == "get_students":
                students = await AsyncORM.select_students()
                await producer.send_and_wait("students_response", {
                    "correlation_id": correlation_id,
                    "students": [
                        {"id": s.id, "name": s.name, "group_id": s.group_id}
                        for s in students
                    ]
                })

            elif msg.topic == "get_groups":
                groups = await AsyncORM.select_group()
                await producer.send_and_wait("groups_response", {
                    "correlation_id": correlation_id,
                    "groups": [
                        {"id": g.id, "name": g.name}
                        for g in groups
                    ]
                })

            elif msg.topic == "create_student_full":
                print(f"[data_service] Handling create_student_full for: {data}")
                student = data["student"]
                result = await AsyncORM.insert_student(
                    name=student["name"],
                    group_id=student["group_id"]
                )
                await producer.send_and_wait("create_student_full_response", {
                    "correlation_id": correlation_id,
                    "status": "ok",
                    "created_id": result.id if result else None
                })

            elif msg.topic == "create_group":
                group_name = data.get("group_name")
                correlation_id = data.get("correlation_id")

                print(f"[data_service] Creating group: {group_name}")
                group = await AsyncORM.insert_group(name=group_name)

                await producer.send_and_wait("find_group_response", {
                    "correlation_id": correlation_id,
                    "group_id": group.id
                })


    finally:
        await consumer.stop()
        await producer.stop()


# ----------------------------------------
# REST
# ----------------------------------------

@app.get("/students/get", tags=[apis.students])
async def get_student_list():
    students = await AsyncORM.select_students()
    return {"students": students}


@app.post("/students/new", tags=[apis.students])
async def post_new_student(data: PostNewStudentBody = Body(...)):
    return await AsyncORM.insert_student(
        name=data.name,
        group_id=data.group_id
    )


@app.post("/students/update", tags=[apis.students])
async def post_update_student(data: PostUpdateStudentBody = Body(...)):
    return await AsyncORM.update_student(
        student_id=data.student_id,
        new_name=data.new_name
    )


@app.get("/groups/get", tags=[apis.groups])
async def get_group_list():
    groups = await AsyncORM.select_group()
    return {"groups": groups}


@app.post("/groups/new", tags=[apis.groups], status_code=204)
async def post_new_group(data: PostNewGroupBody = Body(...)):
    return await AsyncORM.insert_group(name=data.name)


@app.post("/groups/update", tags=[apis.groups], status_code=204)
async def post_update_group(data: PostUpdateGroupBody = Body(...)):
    return await AsyncORM.update_group(
        group_id=data.group_id,
        name=data.name
    )


if __name__ == '__main__':
    uvicorn.run(app, port=8001)
