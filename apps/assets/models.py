from common.models import RootModel

from .const import PlatformCategory


class Test(RootModel):
    pass


class Asset(RootModel):
    name: str
    address: str

    class Config:
        table_name: str = 'assets_asset'


class PlatForm(RootModel):
    name: str
    category: PlatformCategory = PlatformCategory.mysql

    class Config:
        table_name: str = 'assets_platform'

