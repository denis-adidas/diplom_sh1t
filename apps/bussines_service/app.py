import requests, uvicorn

from fastapi import FastAPI, Body


from models import (
    PostStudentWithGroupsRequest,
    StudentOrm,
    PostStudentWithGroupResponse, StudentAndGroup
)

app = FastAPI(title="Business Service")

@app.get("/")
def status_index():
    return {
        "message" : "success"
    }

@app.post("/post/student_group")
def post_get_stu_with_groups(
        body: PostStudentWithGroupsRequest = Body(...)
):
    students = body.students
    groups = body.groups

    res = []
    for student in students:
        for group in groups:
            if student.group_id == group.id:
                res.append(
                    StudentAndGroup(
                        name=student.name,
                        group=group.name
                    )
                )

    return PostStudentWithGroupResponse(info=res)

if __name__ == '__main__':
    uvicorn.run(app, port=8002)
