from pydantic import BaseModel

from common.query import RootParams
from assets.const import WorkerCategory


class AssetParams(RootParams):
    pass


class WorkerParamsNoPage(BaseModel):
    platform: str = WorkerCategory.worker


class AccountParams(RootParams):
    pass
