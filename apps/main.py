import importlib
import inspect

import uvicorn

from typing import Callable
from gettext import gettext as _

from fastapi import FastAPI
from starlette.middleware import Middleware

from apps.middlewares import TokenMiddleware
from settings import settings
from assets.routers import router as assets_router
from common.exceptions import register_exceptions
from common.init import check_db, apps_init


async def startup():
    await check_db()
    await apps_init()


app = FastAPI(
    title='Behemoth', summary=_('Command managed management component'),
    on_startup=[startup],
    # middleware=[Middleware(TokenMiddleware)]
)

# 添加全局异常捕捉器
register_exceptions(app)

# 先手动注册路由
app.include_router(assets_router)


if __name__ == '__main__':
    uvicorn.run(
        'main:app', host=settings.APP.HOST, port=settings.APP.PORT,
        reload=settings.APP.RELOAD
    )
