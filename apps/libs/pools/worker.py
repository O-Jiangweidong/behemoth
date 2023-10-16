from assets.models import TaskWorker
from utils import singleton, get_logger


logger = get_logger()


@singleton
class TaskWorkerPool(object):
    def __init__(self) -> None:
        self._task_workers: list[TaskWorker] = []

    async def get_task_workers(self) -> list[TaskWorker]:
        return self._task_workers

    async def add_task_worker(self, worker: TaskWorker) -> None:
        logger.debug(f'add： {worker}')
        self._task_workers.append(worker)

    async def pre_run(self) -> None:
        """检查发布机状态是否可用"""
        pass

    async def send_file(self) -> None:
        pass

    async def run(self) -> None:
        pass

    async def post_run(self) -> None:
        pass

    async def work(self) -> None:
        await self.pre_run()
        await self.send_file()
        await self.run()
        await self.post_run()
