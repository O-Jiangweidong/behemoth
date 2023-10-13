import uuid

from gettext import gettext as _

from pydantic import Field

from apps.common.serializers import RootModelSerializer
from apps.common.fields import EncryptedField
from .. import models


class Asset(RootModelSerializer):
    name: str = Field(title=_('Name'))
    address: str = Field(title=_('Address'))

    class Config:
        model = models.Asset
