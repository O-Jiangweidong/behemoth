import uuid

from gettext import gettext as _

from pydantic import Field

from assets.const import PlatformCategory, TASK_WORKER
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


class TaskWorker(Asset):
    platform: str = TASK_WORKER

    class Config:
        model = models.TaskWorker

