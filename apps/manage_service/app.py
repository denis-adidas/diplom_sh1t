import requests, uvicorn

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def status_index():
    return {
        "message" : "success"
    }

@app.get("/get/info")
def test():
    response = requests.get("http://localhost:8001/students/get") #todo как не задавать прямые ссылки?
    return response.json()

if __name__ == '__main__':
    uvicorn.run(app, port=8000)