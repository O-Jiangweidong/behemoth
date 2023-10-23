import os
import uuid

import asyncssh

from typing import Optional, Any
from gettext import gettext as _

from pydantic import Field, BaseModel
from fastapi.exceptions import ValidationException
from asyncssh import SSHClientConnection, SSHCompletedProcess

from settings import settings
from common.models import RootModel
from common.fields import EncryptedField
from common.utils import get_logger, calc_file_md5

from .const import PlatformCategory, Protocol, WorkerCategory


logger = get_logger()


class ProtocolItem(BaseModel):
    name: Protocol = Protocol.ssh
    port: int = 22


class Asset(RootModel):
    name: str
    address: str
    tag: Optional[str] = None
    platform: PlatformCategory = PlatformCategory.mysql
    protocols: list[ProtocolItem] = Field(
        json_schema_extra={
            'es_mapping': {'name': 'keyword', 'port': 'long'}
        }
    )

    class Config(RootModel.Config):
        table_name: str = 'assets_asset'
        foreign_fields: dict = {
            **RootModel.Config.foreign_fields
        }
        index_fields = RootModel.Config.index_fields + ('tag',)
        unique_fields = RootModel.Config.unique_fields + ('name',)

    def __str__(self):
        return _('Asset(%s)') % self.name


class Account(RootModel):
    name: str
    username: str = Field(title=_('username'))
    password: Optional[EncryptedField] = None
    asset_id: uuid.UUID = Field(title=_('Asset'))

    class Config(RootModel.Config):
        table_name: str = 'assets_account'
        foreign_fields: dict = {
            'asset_id': ('assets_asset', 'id'),
            **RootModel.Config.foreign_fields
        }
        index_fields = RootModel.Config.index_fields + ('username',)


class Task(RootModel):
    worker_id: uuid.UUID = Field(title=_('Worker'))
    asset_id: uuid.UUID = Field(title=_('Asset'))

    class Config(RootModel.Config):
        table_name: str = 'assets_task'
        foreign_fields: dict = {
            'worker_id': ('assets_asset', 'id'),
            'asset_id': ('assets_asset', 'id'),
            **RootModel.Config.foreign_fields
        }


class Worker(Asset):
    platform: WorkerCategory = WorkerCategory.worker
    account: Optional[Account] = None

    class Config(Asset.Config):
        abstract: bool = True

    def __str__(self):
        return _('Task worker(<%s>)') % self.name

    def __init__(self, **data: Any):
        super().__init__(**data)
        self._ssh_client: Optional[SSHClientConnection] = None
        self._local_script_file: str = os.path.join(
            settings.APP_DIR, 'libs', 'script_templates', 'worker.py'
        )
        self._remote_script_file: str = '/tmp/behemoth/script/worker.py'
        self._local_commands_file: Optional[str] = None
        self._remote_commands_file: Optional[str] = None

    async def set_account(self):
        accounts = await Account.list(return_model=True)
        if len(accounts) < 1:
            raise ValidationException({
                'worker': _('%s has no account' % self)
            })
        self.account = accounts[0]

    async def get_port(self, protocol=Protocol.ssh) -> int:
        port: int = 0
        for p in self.protocols:
            if p.name == protocol:
                port = p.port
        return port

    async def test_connectivity(self, immediate_disconnect=True) -> bool:
        connectivity: bool = False
        try:
            await self.set_account()
        except Exception as error:
            logger.error(f'Task worker set account failed: {error}')

        try:
            conn: SSHClientConnection = await asyncssh.connect(
                    host=self.address, port=self.get_port(),
                    username=self.account.username,
                    password=self.account.password,
                    known_hosts=None,
            )
            connectivity = True
            if not immediate_disconnect:
                self._ssh_client = conn
            else:
                conn.close()
        except Exception as error:
            logger.error(f'Task worker test ssh connect failed: {error}')
        return connectivity

    async def __check(self):
        error: dict = {
            'worker': _('The ssh client is not connected')
        }
        if self._ssh_client is None:
            raise ValidationException(error)
        session, __, __ = await self._ssh_client.open_session()
        if session.is_closing():
            raise ValidationException(error)

    async def __ensure_script_exist(self) -> None:
        result: SSHCompletedProcess = await self._ssh_client.run(
            f'md5sum {self._remote_script_file}'
        )
        if result.returncode == 0:
            remote_file_md5: str = str(result.stdout).split()[0].strip()
            if calc_file_md5(self._local_script_file) == remote_file_md5:
                return

        await self._ssh_client.run(f'mkdir -p {os.path.dirname(self._remote_script_file)}')
        await asyncssh.scp(
            self._local_script_file, (self._ssh_client, self._remote_script_file)
        )

    async def __process_commands_file(self):
        pass

    async def __process_file(self) -> None:
        await self.__ensure_script_exist()
        await self.__process_commands_file()
        await asyncssh.scp(
            self._src_path, (self._ssh_client, self._dest_path)
        )

    async def __clear(self) -> None:
        # 清理远端文件
        result: SSHCompletedProcess = await self._ssh_client.run(f'rm -f {self._remote_commands_file}')
        if result.returncode != 0:
            logger.warning(f'Remote file({self._remote_commands_file}) deletion failed')
        # 清理本地文件
        os.remove(self._local_commands_file)

    async def __execute(self) -> None:
        await self.__process_file()
        await self._ssh_client.create_process(f'python3 {self._dest_file}')

    async def run(self) -> None:
        # TODO 这里参数得传入Task对象，根据Task对象生成commands文件名称
        await self.__check()
        await self.__execute()
        await self.__clear()
