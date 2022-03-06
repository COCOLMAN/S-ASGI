from fastapi import FastAPI
from asgi_server import run

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/sol")
async def root():
    return {"message": "Hello Sol"}



if __name__ == "__main__":
    run(app, host="127.0.0.1", port=8000)
    # python -m example.asgi_app