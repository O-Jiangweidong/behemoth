import uuid

from datetime import datetime
from gettext import gettext as _
from typing import Any

from elasticsearch import AsyncElasticsearch
from elastic_transport import ObjectApiResponse
from fastapi.exceptions import ValidationException
from pydantic import BaseModel

from apps.settings import settings
from apps.utils import singleton, get_logger


logger = get_logger()


class ESQuerySet(object):
    def __init__(self, data: dict, model: BaseModel) -> None:
        self._model = model
        self._data: list = data['data']
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
    _mapping: dict = {}

    @classmethod
    def get_mapping(cls: 'BaseModel | ESManager') -> dict:
        if not cls._mapping:
            properties = {}
            for name, field in cls.model_fields.items():
                _type = 'text'
                if field.annotation is datetime:
                    _type = 'date'
                elif field.annotation is uuid.UUID:
                    _type = 'keyword'

                properties[name] = {'type': _type}
            cls._mapping = {'mappings': {'properties': properties}}
        return cls._mapping

    @classmethod
    def get_table_name(cls: 'BaseModel | ESManager'):
        table_name: str = cls.model_config.get('table_name', '')
        if not table_name:
            raise ValueError(_('%s model_config no attribute table_name') % (cls,))
        return table_name

    @classmethod
    async def ensure_index_exist(cls: 'BaseModel | ESManager', index_name: str) -> None:
        logger.info(f'Start to check whether {index_name} exists')

        try:
            exist = await cls._client.indices.exists(index=index_name)
        except Exception as error:
            exist = False
            logger.warning(f'An error occurred while checking {index_name}: {error}')

        logger.info(f'Check whether {index_name} exists: {exist}')

        if exist:
            return None

        try:
            await cls._client.indices.create(index=index_name, body=cls.get_mapping())
        except Exception as error:
            raise error
        else:
            logger.info(f'Succeeded in creating {index_name}')

    @classmethod
    async def ensure_index_uniform(cls: 'BaseModel | ESManager', index_name: str) -> None:
        new_mapping: dict = cls.get_mapping()['mappings']
        response = await cls._client.indices.get(index=index_name)
        old_mapping = response[index_name]['mappings']
        if new_mapping == old_mapping:
            return

        logger.info(f'Start migrating model [{index_name}] mappings')
        # 更新索引 mapping
        await cls._client.indices.put_mapping(index=index_name, body=new_mapping)
        logger.info(f'The migration model [{index_name}] mapping is complete')

    @classmethod
    async def check(cls: 'BaseModel | ESManager') -> None:
        table_name: str = cls.get_table_name()
        await cls.ensure_index_exist(table_name)
        await cls.ensure_index_uniform(table_name)

    @staticmethod
    async def json_encoder(data: dict):
        from fastapi.encoders import jsonable_encoder
        data = jsonable_encoder(data)
        return data

    async def _pre_check(self, unique_fields: tuple, data: dict) -> None:
        should: list = []
        errors: dict = {}
        for field in unique_fields:
            if value := data.get(field):
                should.append({'term': {field: value}})
                errors[field] = [_('Object with this %s already exists.') % field]

        if not should:
            return

        body = {'query': {'bool': {'should': should}}}
        response: ObjectApiResponse[Any] = await self._client.search(
            index=self.get_table_name(), body=body
        )
        if response['hits']['total']['value'] > 0:
            raise ValidationException(errors)

    async def _save(self: 'RootModel | ESManager', data: dict) -> dict:
        unique_fields: tuple = self.Config.unique_fields
        table_name = self.get_table_name()
        data = await self.json_encoder(data)
        await self._pre_check(unique_fields, data)

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
