import asyncio
from rabbitmq_consumer import RpcConsumer
from models import (
    PostStudentWithGroupsRequest,
    StudentAndGroup,
    PostStudentWithGroupResponse,
    PostCreateStudentWithGroups
)

AMQP_URL = "amqp://guest:guest@rabbitmq/"

consumer = RpcConsumer(AMQP_URL)

async def handle_student_group(data: dict) -> dict:
    print("📩 handle_student_group called")

    body = PostStudentWithGroupsRequest(**data)
    students = body.students
    groups = body.groups

    result = []
    for student in students:
        for group in groups:
            if student.group_id == group.id:
                result.append(
                    StudentAndGroup(
                        name=student.name,
                        group=group.name
                    )
                )

    return PostStudentWithGroupResponse(info=result).model_dump()

async def handle_find_group(data: dict) -> int | None:
    print("📩 handle_find_group called")

    body = PostCreateStudentWithGroups(**data)

    if body.group_id is not None:
        return body.group_id

    for group in body.groups_list:
        if group.name == body.group_name:
            return group.id

    return None

consumer.register_handler("business.student_group", handle_student_group)
consumer.register_handler("business.find_group", handle_find_group)

if __name__ == '__main__':
    import asyncio

    async def main():
        await consumer.start()
        print("✅ Business Service is running")
        while True:
            await asyncio.sleep(3600)

    asyncio.run(main())
