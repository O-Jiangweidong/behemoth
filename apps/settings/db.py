from pydantic import BaseModel


class ElasticSearch(BaseModel):
    HOSTS: str
