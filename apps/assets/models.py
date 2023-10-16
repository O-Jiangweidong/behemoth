import uuid

from typing import Optional
from gettext import gettext as _

from pydantic import Field, BaseModel

from common.models import RootModel
from common.fields import EncryptedField

from .const import PlatformCategory, Protocol, TASK_WORKER


class ProtocolItem(BaseModel):
    name: Protocol = Protocol.ssh
    port: int = 22


class Asset(RootModel):
    name: str
    address: str
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


class TaskWorker(Asset):
    platform: str = TASK_WORKER
    accounts: list[Account] = []

    class Config(Asset.Config):
        pass

    def __str__(self):
        return _('Task worker(<%s>)') % self.name

    async def get_accounts(self):
        self.accounts = await Account.list(return_model=True)
