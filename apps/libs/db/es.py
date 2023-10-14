import uuid
import inspect

from enum import Enum

from datetime import datetime
from gettext import gettext as _
from typing import Any

from elasticsearch import AsyncElasticsearch
from elastic_transport import ObjectApiResponse
from fastapi.exceptions import ValidationException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from pydantic.fields import FieldInfo

from apps.settings import settings
from apps.utils import singleton, get_logger
from apps.common.special import Choice


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
    def _need_set_keyword(cls: 'RootModel | ESManager', field_name: str, field_info: FieldInfo):
        is_keyword = False
        if field_info.annotation is uuid.UUID:
            is_keyword = True
        elif inspect.isclass(field_info.annotation) and \
                issubclass(field_info.annotation, Enum):
            is_keyword = True
        elif field_info.json_schema_extra and \
                field_info.json_schema_extra.get('index', False):
            is_keyword = True
        elif field_name in cls.Config.index_fields:
            is_keyword = True
        elif field_name in cls.Config.unique_fields:
            is_keyword = True
        return is_keyword

    @classmethod
    def get_mapping(cls: 'BaseModel | ESManager') -> dict:
        if not cls._mapping:
            properties = {}
            for name, field in cls.model_fields.items():
                _type = 'text'
                if field.annotation is datetime:
                    _type = 'date'
                elif cls._need_set_keyword(name, field):
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

    async def _pre_check(
            self: 'RootModel | ESManager', data: dict, current_index: str
    ) -> None:
        errors: dict = {}
        unique_fields: tuple = self.Config.unique_fields
        foreign_fields: dict = self.Config.foreign_fields

        should: list = []
        for field in unique_fields:
            if value := data.get(field):
                should.append({
                    'bool': {
                        'must': [
                            {'term': {field: value}},
                            {'term': {'_index': current_index}}
                        ]
                    }
                })

        foreign_index = []
        for field, index_info in foreign_fields.items():
            index_name, index_primary = index_info
            foreign_index.append(index_name)
            if value := data.get(field):
                should.append({
                    'bool': {
                        'must': [
                            {'term': {index_primary: value}},
                            {'term': {'_index': index_name}}
                        ],
                    }
                })

        if not should:
            return

        unique_err = _('Object with this %s already exists.')
        foreign_err = _('The attribute %s associated with the object does not exist')

        body = {'query': {'bool': {'should': should}}}
        response: ObjectApiResponse[Any] = await self._client.search(
            index=[self.get_table_name(), *foreign_index], body=body
        )
        result: list = response['hits']['hits']
        if foreign_fields and not result:
            for field, __ in foreign_fields.items():
                errors.setdefault(field, [foreign_err % field])

        for item in result:
            source_data: dict = item['_source']
            # 检查唯一性
            for field in unique_fields:
                if source_data.get(field) == data[field]:
                    errors.setdefault(field, [unique_err % field])
            # 检查外键
            for field, index_info in foreign_fields.items():
                index_name, index_primary = index_info
                if index_name != item['_index']:
                    continue

                if not source_data.get(index_primary):
                    errors.setdefault(field, [foreign_err % field])

        if errors:
            raise ValidationException(errors)

    async def _save(self: 'RootModel | ESManager', data: dict) -> dict:
        table_name: str = self.get_table_name()
        data: dict = jsonable_encoder(data)
        await self._pre_check(data, table_name)

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
