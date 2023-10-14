import uuid

from typing import Optional
from gettext import gettext as _

from pydantic import Field

from common.models import RootModel
from common.fields import EncryptedField

from .const import PlatformCategory


class Asset(RootModel):
    name: str
    address: str

    class Config(RootModel.Config):
        table_name: str = 'assets_asset'


class PlatForm(RootModel):
    name: str
    category: PlatformCategory = PlatformCategory.mysql

    class Config(RootModel.Config):
        table_name: str = 'assets_platform'


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
