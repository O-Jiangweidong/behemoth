import os

from pydantic import BaseModel


class App(BaseModel):
    NAME: str = 'behemoth'
    HOST: str = '0.0.0.0'
    PORT: int = 8088
    DEBUG: bool = False
    RELOAD: bool = False
    LOG_LEVEL: str = 'error'
    CORE_HOST: str = 'http://jms_core'
    BOOTSTRAP_TOKEN: str
    SECRET_KEY: str
