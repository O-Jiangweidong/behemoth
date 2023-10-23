# 这里的所有函数在项目启动的时候都会执行一次

from assets.params import WorkerParamsNoPage
from assets.models import Worker
from libs.db import QuerySet
from libs.pools.worker import WorkerPool


async def init_worker_pool() -> None:
    _params: WorkerParamsNoPage = WorkerParamsNoPage()
    workers: list = await Worker.list(_params, return_model=True)
    for worker in workers:
        await WorkerPool().add_worker(worker)
