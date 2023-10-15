import uuid

from gettext import gettext as _

from pydantic import Field

from common.serializers import RootModelSerializer
from .. import models


class Asset(RootModelSerializer):
    name: str = Field(title=_('Name'))
    address: str = Field(title=_('Address'))

    class Config:
        model = models.Asset
