import asyncio
import uvicorn
import aiohttp
from datetime import datetime
from config import settings
from fastapi import FastAPI, Body
from pydantic import TypeAdapter

from models import (
    GetStudentList,
    PostStudentWithGroupsRequest,
    CreateUser,
    GroupOrm,
    PostCreateStudent,
    PostCreateStudentWithGroups
)

from rabbitmq_client import RpcClient

app = FastAPI(title="Manage Service")
loop = asyncio.get_event_loop()
rpc = RpcClient(settings.RABBITMQ_URL)

QUEUE_NAMES = [
    "data.get_students",
    "data.get_groups",
    "data.groups_new",
    "data.create_student",
    "business.find_group",
    "business.student_group"
]

async def log_queue_sizes(interval=5):
    url = f"http://{settings.RABBITMQ_HOST}:15672/api/queues"
    auth = aiohttp.BasicAuth(
        login=settings.RABBITMQ_USER,
        password=settings.RABBITMQ_PASSWORD
    )

    async with aiohttp.ClientSession(auth=auth) as session:
        while True:
            try:
                async with session.get(url) as resp:
                    queues = await resp.json()
                    now = datetime.now().isoformat(timespec="seconds")
                    for q in queues:
                        if q["name"] in QUEUE_NAMES:
                            print(f"[{now}] [QUEUE] {q['name']}: messages={q['messages']}")
            except Exception as e:
                print(f"[QUEUE LOG ERROR] {e}")
            await asyncio.sleep(interval)


@app.on_event("startup")
async def startup_event():
    await rpc.connect()
    asyncio.create_task(log_queue_sizes(interval=5))


@app.get("/")
def status_index():
    return { "message": "success" }


@app.get("/get/students")
async def get_student_list():
    response = await rpc.call("data.get_students", {})
    return GetStudentList(**response)


@app.get("/get/stud_info")
async def student_with_groups_list():
    students = await rpc.call("data.get_students", {})
    groups = await rpc.call("data.get_groups", {})

    payload = PostStudentWithGroupsRequest(
        students=students["students"],
        groups=groups["groups"]
    )

    response = await rpc.call("business.student_group", payload.model_dump(exclude_none=True))
    return response


@app.post("/post/create/student")
async def post_create_student(body: PostCreateStudent = Body(...)):
    groups_data = await rpc.call("data.get_groups", {})
    groups_list = TypeAdapter(list[GroupOrm]).validate_python(groups_data["groups"])

    group_id_response = await rpc.call("business.find_group", PostCreateStudentWithGroups(
        name=body.name,
        group_id=body.group_id if body.group_id else None,
        group_name=body.group_name if body.group_name else None,
        groups_list=groups_list
    ).model_dump(exclude_none=True))

    if group_id_response is None:
        await rpc.call("data.groups_new", {"name": body.group_name})
        groups_data = await rpc.call("data.get_groups", {})
        groups_list = TypeAdapter(list[GroupOrm]).validate_python(groups_data["groups"])
        for group in groups_list:
            if group.name == body.group_name:
                group_id_response = group.id

    await rpc.call("data.create_student", {
        "name": body.name,
        "group_id": group_id_response
    })

    return {"message": "student created"}


if __name__ == '__main__':
    uvicorn.run(app, port=8000)
