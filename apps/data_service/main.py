import asyncio
from enum import StrEnum

import uvicorn

from models import (
    PostNewStudentBody,
    PostUpdateStudentBody,
    PostUpdateGroupBody,
    PostNewGroupBody
)

from fastapi import FastAPI
from query.orm import AsyncORM
from fastapi import Body

app = FastAPI(title="Data service")

class apis(StrEnum):
    students = "Students"
    groups = "Groups"


@app.get("/")
def status_index():
    return {
        "message" : "success"
    }

# вынести в роутеры
@app.get("/students/get", tags=[apis.students])
async def get_student_list():
    students = await AsyncORM.select_students()
    return {"students" : students}

@app.post("/students/new", tags=[apis.students])
async def post_new_student(
    data: PostNewStudentBody = Body(...)
):
    return await AsyncORM.insert_student(
        name=data.name,
        group_id=data.group_id
    )

@app.post("/students/update", tags=[apis.students])
async def post_new_student(
    data: PostUpdateStudentBody = Body(...)
):
    return await AsyncORM.update_student( #todo status code
        student_id=data.student_id,
        new_name=data.new_name
    )


@app.get("/groups/get", tags=[apis.groups])
async def get_student_list():
    groups = await AsyncORM.select_group()
    return {"groups" : groups}

@app.post("/groups/new", tags=[apis.groups])
async def post_new_student(
    data: PostNewGroupBody = Body(...)
):
    return await AsyncORM.insert_group(
        name=data.name,
    )

@app.post("/groups/update", tags=[apis.groups])
async def post_new_student(
    data: PostUpdateGroupBody = Body(...)
):
    return await AsyncORM.update_group(
        group_id=data.group_id,
        name=data.name
    )


if __name__ == '__main__':
    uvicorn.run(app, port=8001)