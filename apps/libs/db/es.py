import uuid

from datetime import datetime
from gettext import gettext as _
from typing import Any, Optional

from elasticsearch import AsyncElasticsearch
from elastic_transport import ObjectApiResponse
from pydantic import BaseModel

from apps.settings import settings
from apps.utils import singleton, get_logger


logger = get_logger()


class ESQuerySet(object):
    def __init__(self, data: dict) -> None:
        self._data: dict = data['data']
        self._length = data['total']

    def __len__(self):
        return self._length

    def data(self):
        return self._data


@singleton
class ESClient(object):
    @staticmethod
    def get_client() -> AsyncElasticsearch:
        return AsyncElasticsearch(
            hosts=settings.ES.HOSTS,
        )


class ESManager(object):
    _client: AsyncElasticsearch = ESClient().get_client()

    @classmethod
    def get_table_name(cls: 'BaseModel'):
        table_name: str = cls.model_config.get('table_name', '')
        if not table_name:
            raise ValueError(_('%s model_config no attribute table_name') % (cls,))
        return table_name

    @classmethod
    async def ensure_index_exist(cls: 'BaseModel', index_name: str) -> None:
        logger.info(f'Start to check whether {index_name} exists')

        try:
            exist = await cls._client.indices.exists(index=index_name)
        except Exception as error:
            exist = False
            logger.warning(f'An error occurred while checking {index_name}: {error}')

        logger.info(f'Check whether {index_name} exists: {exist}')

        if exist:
            return None

        properties: dict = {}
        for name, field in cls.model_fields.items():
            _type = 'text'
            if field.annotation is datetime:
                _type = 'date'
            elif field.annotation is uuid.UUID:
                _type = 'keyword'

            properties[name] = {'type': _type}
        body = {'mappings': {'properties': properties}}
        try:
            await cls._client.indices.create(index=index_name, body=body)
        except Exception as error:
            logger.error(f'Failed to create {index_name}: {error}')
        else:
            logger.info(f'Succeeded in creating {index_name}')

    @classmethod
    async def check(cls: 'BaseModel') -> None:
        await cls.ensure_index_exist(cls.get_table_name())

    async def _save(self: 'BaseModel', data: dict) -> dict:
        table_name = self.get_table_name()
        await self._client.index(index=table_name, body=data)
        return data

    @classmethod
    async def _list(cls, param: dict) -> dict:
        size = param.get('size', 100)
        table_name = cls.get_table_name()
        query = {'query': {'match_all': {}}, 'size': size}
        response: ObjectApiResponse[Any] = await cls._client.search(
            index=table_name, body=query
        )
        result: dict = {
            'data': [hit['_source'] for hit in response['hits']['hits']],
            'total': response["hits"]["total"]["value"]
        }
        return result
