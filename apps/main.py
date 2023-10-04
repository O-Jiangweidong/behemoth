import uvicorn

from fastapi import FastAPI

from apps.middlewares import TokenMiddleware
from apps.settings import settings


app = FastAPI()

app.add_middleware(TokenMiddleware, )


@app.get('/')
async def get():
    return {'data': 'hello world'}


if __name__ == '__main__':
    uvicorn.run(
        'main:app', host=settings.APP.HOST, port=settings.APP.PORT,
        reload=settings.APP.RELOAD
    )
