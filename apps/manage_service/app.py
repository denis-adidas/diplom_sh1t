import requests, uvicorn

from fastapi import FastAPI, Body
from config import settings
from pydantic import TypeAdapter

from models import (
    GetStudentList,
    PostStudentWithGroupsRequest,
    CreateUser,
    GroupOrm,
    PostCreateStudent,
    PostCreateStudentWithGroups
)

app = FastAPI(title="Manage Service")


@app.get("/")
def status_index():
    return {
        "message": "success"
    }


@app.get("/get/students")
def get_student_list():
    response = requests.get(f"{settings.DATA_URL}/students/get")
    return GetStudentList(**response.json())


@app.get("/get/stud_info")
def student_with_groups_list():
    students = requests.get(f"{settings.DATA_URL}/students/get")
    groups = requests.get(f"{settings.DATA_URL}/groups/get")

    payload = PostStudentWithGroupsRequest(
        students=students.json()["students"],
        groups=groups.json()["groups"]
    )

    response = requests.post(
        url=f"{settings.BUSSINESS_URL}/post/student_group",
        json=payload.model_dump(exclude_none=True)
    )

    return response.json()


@app.post("/post/create/student")
def post_create_student(
        body: PostCreateStudent = Body(...)
):
    response = requests.get(f"{settings.DATA_URL}/groups/get")

    groups_list = TypeAdapter(list[GroupOrm]).validate_python(response.json()["groups"])

    group_id = requests.post(
        url=f"{settings.BUSSINESS_URL}/post/find_group",
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
            json={"name": body.group_name}
        )
        response = requests.get(f"{settings.DATA_URL}/groups/get")

        groups_list = TypeAdapter(list[GroupOrm]).validate_python(response.json()["groups"])

        for group in groups_list:
            if group.name == body.group_name:
                group_id = group.id

        requests.post(
            url=f"{settings.DATA_URL}/students/new",
            json={
                "name": body.name,
                "group_id": group_id
            }
        )
        return {"message" : "success"}
    else:
        requests.post(
            url=f"{settings.DATA_URL}/students/new",
            json={
                "name": body.name,
                "group_id": group_id
            }
        )
        return {"message" : "success"}



if __name__ == '__main__':
    uvicorn.run(app, port=8000)
