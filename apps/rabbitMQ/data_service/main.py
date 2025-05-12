import asyncio
import uvicorn
from fastapi import FastAPI
from config import settings

from models import (
    PostNewStudentBody,
    PostUpdateStudentBody,
    PostUpdateGroupBody,
    PostNewGroupBody
)

from query.orm import AsyncORM
from database import init_models
from rabbitmq_consumer import RpcConsumer

app = FastAPI(title="Data service")


consumer = RpcConsumer(settings.RABBITMQ_URL)


@app.get("/")
def status_index():
    return {"message": "success"}


@app.on_event("startup")
async def on_startup():
    await init_models()

    consumer.register_handler("data.get_students", handle_get_students)
    consumer.register_handler("data.get_groups", handle_get_groups)
    consumer.register_handler("data.groups_new", handle_new_group)
    consumer.register_handler("data.groups_update", handle_update_group)
    consumer.register_handler("data.create_student", handle_new_student)
    consumer.register_handler("data.students_update", handle_update_student)

    asyncio.create_task(consumer.start())


async def handle_get_students(_: dict) -> dict:
    print(">>> handle_get_students() called!")

    students = await AsyncORM.select_students()
    return {
        "students": [
            {
                "id": s.id,
                "name": s.name,
                "group_id": s.group_id
            }
            for s in students
        ]
    }

async def handle_get_groups(_: dict) -> dict:
    groups = await AsyncORM.select_group()
    return {
        "groups": [
            {
                "id": g.id,
                "name": g.name
            }
            for g in groups
        ]
    }

async def handle_new_group(data: dict) -> dict:
    name = data.get("name")
    if name:
        await AsyncORM.insert_group(name=name)
        return {"status": "ok"}
    return {"error": "no group name"}

async def handle_update_group(data: dict) -> dict:
    group_id = data.get("group_id")
    name = data.get("name")
    if group_id and name:
        await AsyncORM.update_group(group_id=group_id, name=name)
        return {"status": "updated"}
    return {"error": "invalid group_id or name"}

async def handle_new_student(data: dict) -> dict:
    name = data.get("name")
    group_id = data.get("group_id")
    if name and group_id is not None:
        await AsyncORM.insert_student(name=name, group_id=group_id)
        return {"status": "created"}
    return {"error": "missing name or group_id"}

async def handle_update_student(data: dict) -> dict:
    student_id = data.get("student_id")
    new_name = data.get("new_name")
    if student_id and new_name:
        await AsyncORM.update_student(student_id=student_id, new_name=new_name)
        return {"status": "updated"}
    return {"error": "invalid student_id or new_name"}

if __name__ == '__main__':
    uvicorn.run(app, port=8001)