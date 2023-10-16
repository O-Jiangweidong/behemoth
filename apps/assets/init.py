# 这里的所有函数在项目启动的时候都会执行一次

from assets.params import TaskWorkerParamsNoPage
from assets.models import TaskWorker
from libs.db import QuerySet
from libs.pools.worker import TaskWorkerPool


async def init_task_worker_pool() -> None:
    _params: TaskWorkerParamsNoPage = TaskWorkerParamsNoPage()
    task_workers: list = await TaskWorker.list(_params, return_model=True)
    for worker in task_workers:
        await TaskWorkerPool().add_task_worker(worker)
