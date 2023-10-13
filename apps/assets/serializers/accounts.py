import uuid

from gettext import gettext as _
from typing import Optional

from pydantic import Field

from apps.common.serializers import RootModelSerializer
from apps.common.fields import EncryptedField
from .. import models


class Account(RootModelSerializer):
    name: str = Field(title=_('Name'))
    username: str = Field(title=_('Username'))
    password: Optional[EncryptedField] = None
    asset_id: uuid.UUID

    class Config:
        model = models.Account
