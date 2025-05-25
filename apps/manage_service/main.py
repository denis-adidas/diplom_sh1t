import requests, uvicorn
from requests.exceptions import Timeout

from fastapi import FastAPI, Body, HTTPException
from config import settings
from pydantic import TypeAdapter

from models import (
    GetStudentList,
    PostStudentWithGroupsRequest,
    GroupOrm,
    PostCreateStudent,
    PostCreateStudentWithGroups
)

app = FastAPI(title="Manage Service")


@app.get("/")
def status_index():
    return {"message": "success"}


@app.get("/get/students")
def get_student_list():
    try:
        response = requests.get(f"{settings.DATA_URL}/students/get", timeout=60)
        return GetStudentList(**response.json())
    except Timeout:
        raise HTTPException(status_code=504, detail="Timeout while fetching student list")


@app.get("/get/stud_info")
def student_with_groups_list():
    try:
        students = requests.get(f"{settings.DATA_URL}/students/get", timeout=60)
        groups = requests.get(f"{settings.DATA_URL}/groups/get", timeout=60)

        payload = PostStudentWithGroupsRequest(
            students=students.json()["students"],
            groups=groups.json()["groups"]
        )

        response = requests.post(
            url=f"{settings.BUSSINESS_URL}/post/student_group",
            json=payload.model_dump(exclude_none=True),
            timeout=60
        )

        return response.json()
    except Timeout:
        raise HTTPException(status_code=504, detail="Timeout while processing student group info")


@app.post("/post/create/student")
def post_create_student(body: PostCreateStudent = Body(...)):
    try:
        response = requests.get(f"{settings.DATA_URL}/groups/get", timeout=60)
        groups_list = TypeAdapter(list[GroupOrm]).validate_python(response.json()["groups"])

        group_id = requests.post(
            url=f"{settings.BUSSINESS_URL}/post/find_group",
            timeout=60,
            json=PostCreateStudentWithGroups(
                name=body.name,
                group_id=body.group_id if body.group_id else None,
                group_name=body.group_name if body.group_name else None,
                groups_list=groups_list
            ).model_dump(exclude_none=True)
        ).json()

        if group_id is None:
            requests.post(
                url=f"{settings.DATA_URL}/groups/new",
                json={"name": body.group_name},
                timeout=60
            )
            response = requests.get(f"{settings.DATA_URL}/groups/get", timeout=60)
            groups_list = TypeAdapter(list[GroupOrm]).validate_python(response.json()["groups"])
            for group in groups_list:
                if group.name == body.group_name:
                    group_id = group.id

        requests.post(
            url=f"{settings.DATA_URL}/students/new",
            json={"name": body.name, "group_id": group_id},
            timeout=60
        )
        return {"message": "success"}

    except Timeout:
        raise HTTPException(status_code=504, detail="Timeout during student creation flow")


if __name__ == '__main__':
    uvicorn.run(app, port=8000)
