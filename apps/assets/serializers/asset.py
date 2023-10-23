import uuid

from gettext import gettext as _

from pydantic import Field

from assets.const import PlatformCategory
from assets.models import ProtocolItem
from common.serializers import RootModelSerializer
from .. import models


class Asset(RootModelSerializer):
    name: str = Field(title=_('Name'))
    address: str = Field(title=_('Address'))
    platform: PlatformCategory = PlatformCategory.mysql
    protocols: list[ProtocolItem] = Field(title=_('Protocol'))

    class Config:
        model = models.Asset


class Worker(RootModelSerializer):
    class Config:
        model = models.Worker


class Task(RootModelSerializer):
    asset_id: uuid.UUID = Field(title=_('Asset'))
    worker_id: uuid.UUID = Field(title=_('Worker'))

    class Config:
        model = models.Task
