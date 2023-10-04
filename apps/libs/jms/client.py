import asyncio
import os
import random
import string

import requests
import aiofiles

from typing import Optional

from pydantic import BaseModel, Field

from settings import settings
from utils import get_logger


logger = get_logger()


class AccessKey(BaseModel):
    id_: Optional[str] = Field(default=None, alias='id')
    secret: Optional[str] = None


class ServiceAccount(BaseModel):
    access_key: Optional[AccessKey] = None


class RegisterResponse(BaseModel):
    service_account: ServiceAccount


class JumpServerClient:
    def __init__(self):
        self.base_url: str = settings.APP.CORE_HOST
        self.key_path: str = os.path.join(settings.DATA_DIR, 'keys')
        self.key_file: str = os.path.join(self.key_path, '.access_key')
        self.access_key: Optional[AccessKey] = None
        asyncio.run(self._load_auth())

    async def _load_auth(self) -> None:
        if not os.path.exists(self.key_file):
            await self.register()
        else:
            await self._load_from_file()

    async def _load_from_file(self) -> None:
        async with aiofiles.open(self.key_file)as reader:
            content = await reader.read()
            try:
                id_, secret = content.split(':')
                self.access_key = AccessKey(id=id_, secret=secret)
                await logger.info('Load access_key successful')
            except Exception as err:
                await logger.warning(f'Load access_key failed: {err}')
                await self.register()

    async def _save_to_file(self) -> None:
        if not os.path.exists(self.key_path):
            os.makedirs(self.key_path)

        async with aiofiles.open(self.key_file, 'w')as writer:
            await writer.write(f'{self.access_key.id_}:{self.access_key.secret}')

    async def register(self) -> None:
        await logger.info('Start register JumpServer client')
        url = f'{self.base_url}/api/v1/terminal/terminal-registrations/'
        headers = {
            'Authorization': f'BootstrapToken {settings.APP.BOOTSTRAP_TOKEN}'
        }
        data = {
            'name': await self._get_random_name(),
            'comment': 'behemoth', 'type': 'behemoth'
        }
        response = None
        try:
            response = requests.post(url, json=data, headers=headers)
            item = RegisterResponse(**response.json())
            self.access_key = item.service_account.access_key
            await self._save_to_file()
        except Exception as error:
            await logger.error(f'Register failed: {error};')
            if getattr(response, 'text', None):
                await logger.error(f'Response: {response.text}')
        await logger.info('Registered JumpServer client successfully')

    @staticmethod
    async def _get_random_name(length=6) -> str:
        ret = await asyncio.to_thread(
            random.sample, string.ascii_letters, length
        )
        return f"Behemoth-{''.join(ret)}"


jms_client = JumpServerClient()
res = jms_client.access_key.model_dump()
print(res)
