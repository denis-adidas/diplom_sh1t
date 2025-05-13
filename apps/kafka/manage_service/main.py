import uvicorn
from fastapi import FastAPI, Body
from uuid import uuid4
import asyncio

from kafka_producer import KafkaManager
from kafka_consumer import KafkaResponseConsumer, pending_results
from config import settings
from models import PostCreateStudent

app = FastAPI(title="Manage Service (Kafka)")
kafka = KafkaManager(settings.KAFKA_BOOTSTRAP_SERVERS)
consumer = KafkaResponseConsumer(settings.KAFKA_BOOTSTRAP_SERVERS, topics=[
    "students_response", "groups_response", "student_group_response"
])

@app.on_event("startup")
async def startup():
    await kafka.start()
    await consumer.start()

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

    await kafka.send("create_student_request", {
        "correlation_id": correlation_id,
        "student": body.model_dump(exclude_none=True)
    })

    try:
        result = await asyncio.wait_for(future, timeout=60)
        return result
    except asyncio.TimeoutError:
        return {"error": "timeout while waiting for create_student_response"}
    finally:
        pending_results.pop(correlation_id, None)

if __name__ == "__main__":
    uvicorn.run(app, port=8000)
