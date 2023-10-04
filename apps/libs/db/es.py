from typing import Optional

from elasticsearch import AsyncElasticsearch

from settings import settings


class ESObject(object):
    def __init__(self) -> None:
        self._client: Optional[AsyncElasticsearch] = None

    @property
    def client(self) -> AsyncElasticsearch:
        if self._client is None:
            self._client = self.get_client()
        return self._client

    @staticmethod
    def get_client() -> AsyncElasticsearch:
        return AsyncElasticsearch(
            hosts=settings.ES.HOSTS,
        )
