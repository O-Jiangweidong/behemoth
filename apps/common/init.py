import importlib
import inspect

from common.models import RootModel
from libs.jms.client import jms_client


async def check_jms():
    pass


async def check_db():
    db_check_apps = ['assets']
    for app_name in db_check_apps:
        try:
            module = importlib.import_module(f'apps.{app_name}.models')
        except ModuleNotFoundError:
            continue

        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and inspect.getmodule(obj) == module \
                    and issubclass(obj, RootModel) and hasattr(obj, 'check'):
                if getattr(getattr(obj, 'Config', None), 'abstract', False):
                    await obj.check()


async def apps_init():
    db_check_apps = ['assets']
    for app_name in db_check_apps:
        try:
            module = importlib.import_module(f'apps.{app_name}.init')
        except ModuleNotFoundError:
            continue

        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj) and inspect.getmodule(obj) == module:
                await obj()
