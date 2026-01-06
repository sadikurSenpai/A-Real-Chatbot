from fastapi import FastAPI
from api.endpoints.chat import router

app = FastAPI()

app.include_router(router, tags=['Chat'])

@app.get('/')
def home():
    return {'msg': 'Welcome'}