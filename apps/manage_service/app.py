from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def status_index():
    return {
        "message" : "success"
    }

