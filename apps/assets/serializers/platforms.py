from common.serializers import RootModelSerializer
from .. import models
from ..const import PlatformCategory


class Platform(RootModelSerializer):
    name: str
    category: PlatformCategory = PlatformCategory.mysql

    class Config:
        model = models.PlatForm
