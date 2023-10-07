import uuid

from datetime import datetime

from elasticsearch import AsyncElasticsearch
from pydantic import BaseModel

from apps.settings import settings
from apps.utils import singleton, get_logger


logger = get_logger()


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
        table_name: str = cls.model_config.get('table_name')
        if not table_name:
            return

        await cls.ensure_index_exist(table_name)
