from pydantic import BaseModel

from common.query import RootParams
from assets.const import TASK_WORKER


class AssetParams(RootParams):
    pass


class TaskWorkerParamsNoPage(BaseModel):
    platform: str = TASK_WORKER


class AccountParams(RootParams):
    pass
