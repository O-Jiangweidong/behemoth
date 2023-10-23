import asyncio
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

from settings import settings
from common.utils import singleton, get_logger, random_string
from common.fields import EncryptedField


logger = get_logger()


class ESQuerySet(object):
    def __init__(self, data: dict, model: BaseModel) -> None:
        self._model = model
        self._data: list = data['data']
        self._length: int = data['total']

    def __len__(self):
        return self._length

    @property
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
    async def _need_set_keyword(cls: 'RootModel | ESManager', field_name: str, field_info: FieldInfo):
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
    async def get_mapping(cls: 'BaseModel | ESManager') -> dict:
        if not cls._mapping:
            properties = {}
            for name, field in cls.model_fields.items():
                _type_name, _type = 'type', 'text'
                if field.annotation is datetime:
                    _type = 'date'
                elif await cls._need_set_keyword(name, field):
                    _type = 'keyword'
                elif field.json_schema_extra:
                    if mapping := field.json_schema_extra.get('es_mapping'):
                        _type_name = 'properties'
                        _type = {k: {'type': v} for k, v in mapping.items()}
                properties[name] = {_type_name: _type}
            cls._mapping = {'mappings': {'properties': properties}}
        return cls._mapping

    @classmethod
    async def get_table_name(cls: 'BaseModel | ESManager'):
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
            await cls._client.indices.create(index=index_name, body=await cls.get_mapping())
        except Exception as error:
            raise error
        else:
            logger.info(f'Succeeded in creating {index_name}')

    @classmethod
    async def ensure_index_uniform(cls: 'BaseModel | ESManager', index_name: str) -> None:
        new_mapping: dict = (await cls.get_mapping())
        response = await cls._client.indices.get(index=index_name)
        old_mapping = {'mappings': response[index_name]['mappings']}
        if new_mapping == old_mapping:
            return

        logger.debug(f'old mapping: {old_mapping}')
        logger.debug(f'new mapping: {new_mapping}')
        logger.info(f'Start migrating model [{index_name}] mappings')
        # 查询旧索引数据数量
        response: ObjectApiResponse = await cls._client.count(index=index_name)
        old_document_count: int = response['count']
        logger.debug(f'old_document_count: {old_document_count}')
        # 创建新索引
        new_index_name: str = f'{index_name}-{random_string(4, upper=False)}'
        await cls._client.indices.create(index=new_index_name, body=new_mapping)
        # 新旧索引替换
        reindex_body = {
            'source': {'index': index_name}, 'dest': {'index': new_index_name}
        }
        await cls._client.reindex(body=reindex_body, wait_for_completion=True,)
        # 处理旧索引
        await cls._client.indices.delete(index=index_name)
        await cls._client.indices.create(index=index_name, body=new_mapping)
        reindex_body = {
            'source': {'index': new_index_name}, 'dest': {'index': index_name}
        }
        # 查询新索引数据是否都导入完成
        new_document_count: int = 0
        while new_document_count != old_document_count:
            logger.debug(
                f'new_document_count({new_document_count}) !='
                f' old_document_count({old_document_count})'
            )
            response: ObjectApiResponse = await cls._client.count(index=new_index_name)
            new_document_count = response['count']
            await asyncio.sleep(1)
        await cls._client.reindex(body=reindex_body, wait_for_completion=True)
        await cls._client.indices.delete(index=new_index_name)
        logger.info(f'The migration model [{index_name}] mapping is complete')

    @classmethod
    async def check(cls: 'BaseModel | ESManager') -> None:
        table_name: str = await cls.get_table_name()
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
            index=[await self.get_table_name(), *foreign_index], body=body
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
        table_name: str = await self.get_table_name()
        data: dict = jsonable_encoder(
            data, custom_encoder={EncryptedField: lambda x: str(x)}
        )
        await self._pre_check(data, table_name)
        await self._client.index(index=table_name, document=data)
        return data

    @staticmethod
    async def _build_query_body(params: dict) -> dict:
        size = params.pop('size', None)
        page = params.pop('page', None)
        if not params:
            query_body: dict = {'query': {'match_all': {}}}
        else:
            must: list = [{'term': {k: v}} for k, v in params.items()]
            query_body: dict = {'query': {'bool': {'must': must}}}
        if size:
            query_body.update(size=size)
        if page:
            size = size or 15
            query_body.update({'from': (page - 1) * size})
        return query_body

    @classmethod
    async def _list(cls, params: dict) -> dict:
        table_name = await cls.get_table_name()
        body: dict = await cls._build_query_body(params)
        logger.debug(f'List query body: {body}')
        response: ObjectApiResponse[Any] = await cls._client.search(
            index=table_name, body=body
        )
        result: dict = {
            'data': [hit['_source'] for hit in response['hits']['hits']],
            'total': response["hits"]["total"]["value"]
        }
        return result
