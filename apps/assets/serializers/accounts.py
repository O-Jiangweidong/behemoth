import uuid

from gettext import gettext as _
from typing import Optional

from pydantic import Field

from common.serializers import RootModelSerializer
from .. import models


class Account(RootModelSerializer):
    name: str = Field(title=_('Name'))
    username: str = Field(title=_('Username'))
    password: Optional[str] = None
    asset_id: uuid.UUID

    class Config:
        model = models.Account
