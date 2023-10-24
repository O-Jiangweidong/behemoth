import uuid

from gettext import gettext as _
from typing import Optional

from pydantic import Field

from common.serializers import RootModelSerializer
from .. import models


class Task(RootModelSerializer):
    asset_id: uuid.UUID = Field(title=_('Asset'))
    worker_id: uuid.UUID = Field(title=_('Worker'))

    class Config:
        model = models.Task


class TaskInstance(RootModelSerializer):
    asset: models.Asset
    worker: Optional[models.Worker] = None
    encryption_key: str
