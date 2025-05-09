from locust import HttpUser, task, between
import random

class ManageServiceUser(HttpUser):
    wait_time = between(1, 3)

    @task(2)
    def index(self):
        self.client.get("/")

    @task(5)
    def get_students(self):
        self.client.get("/get/students")

    @task(3)
    def get_stud_info(self):
        self.client.get("/get/stud_info")

    @task(1)
    def create_student(self):
        self.client.post("/post/create/student", json={
            "name": f"TestUser{random.randint(1, 9999)}",
            "group_name": f"TestGroup{random.randint(1, 999)}"
        })
