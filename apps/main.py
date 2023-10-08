import importlib
import inspect

import uvicorn

from gettext import gettext as _

from fastapi import FastAPI

from apps.middlewares import TokenMiddleware
from apps.settings import settings
from apps.assets.routers import router as assets_router
from common.models import RootModel


async def check_database():
    apps = ['assets']
    for app in apps:
        try:
            module = importlib.import_module(f'apps.{app}.models')
        except ModuleNotFoundError:
            continue

        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and inspect.getmodule(obj) == module \
                    and issubclass(obj, RootModel) and hasattr(obj, 'check'):
                await obj.check()


app = FastAPI(
    title='Behemoth', summary=_('Command managed management component'),
    on_startup=[check_database]
)

# 添加中间件
# app.add_middleware(TokenMiddleware, )

# 先手动注册路由
app.include_router(assets_router)


if __name__ == '__main__':
    uvicorn.run(
        'main:app', host=settings.APP.HOST, port=settings.APP.PORT,
        reload=settings.APP.RELOAD
    )
