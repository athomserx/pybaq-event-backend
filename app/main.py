from fastapi import FastAPI

from app.routers.chat import router as chat_router

app = FastAPI()
app.include_router(chat_router)


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

