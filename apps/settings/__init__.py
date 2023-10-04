import os

import yaml

from pydantic import BaseModel

from .db import ElasticSearch
from .app import App


class Settings(BaseModel):
    APP_DIR: str = os.path.dirname(os.path.dirname(__file__))
    PROJECT_DIR: str = os.path.dirname(APP_DIR)
    DATA_DIR: str = os.path.join(PROJECT_DIR, 'data')
    ES: ElasticSearch
    APP: App

    @classmethod
    def from_yml(cls):
        current_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        config_path = os.path.join(current_path, 'config.yml')
        with open(config_path) as f:
            config = yaml.safe_load(f)
        return cls(**config)


settings = Settings.from_yml()
