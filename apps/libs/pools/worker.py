from difflib import SequenceMatcher
from gettext import gettext as _
from typing import Optional

from fastapi.exceptions import ValidationException

from assets.models import Worker, Asset
from common.utils import singleton, get_logger


logger = get_logger()


@singleton
class WorkerPool(object):
    def __init__(self) -> None:
        self._workers: dict[str, dict[str, Worker]] = {}
        self._default_workers: dict[str, Worker] = {}
        self._running_workers: dict[str, Worker] = {}
        self._useless_workers: dict[str, Worker] = {}

    async def __get_workers(self) -> list[Worker]:
        default_workers: list = list(self._default_workers.values())
        other_workers: list = list(self._workers.values())
        return other_workers + default_workers

    async def add_worker(self, worker: Worker) -> None:
        logger.debug(f'Add a worker： {worker}({worker.tag})')
        if worker.tag:
            self._workers[worker.tag][worker.name] = worker
        else:
            self._default_workers[worker.name] = worker

    async def __select_worker(self, asset: Asset) -> Optional[Worker]:
        worker: Optional[Worker] = None
        if not asset.tag:
            all_workers: list[Worker] = await self.__get_workers()
            __, worker = all_workers.pop() if len(all_workers) > 0 else None
        else:
            # 根据标签选择工作机
            minimum_ratio: float = 0
            for tag in self._workers.keys():
                ratio: float = SequenceMatcher(None, asset.tag, tag).ratio()
                if ratio <= minimum_ratio:
                    continue

                minimum_ratio = ratio
                if workers := self._workers.get(tag):
                    __, worker = workers.popitem()
                else:
                    break

            if worker is None and not self._default_workers:
                __, worker = self._default_workers.popitem()

        return worker

    async def __get_valid_worker(self, asset: Asset) -> Worker:
        while True:
            # 根据资产属性选择一个工作机
            worker: Optional[Worker] = await self.__select_worker(asset)
            if not worker:
                raise ValidationException({
                    'worker': _('Not found a valid worker')
                })
            # 检查工作机是否可连接
            connectivity: bool = await worker.test_connectivity()
            if not connectivity:
                self._useless_workers[str(worker.id)] = worker
            else:
                self._running_workers[str(asset.id)] = worker
                break
        return worker

    async def __pre_run(self, asset: Asset) -> Worker:
        worker: Worker = await self.__get_valid_worker(asset)
        return worker

    @staticmethod
    async def __run(worker: Worker, asset: Asset) -> None:
        # TODO create task
        await worker.run()

    async def __post_run(self, asset: Asset) -> None:
        worker: Worker = self._running_workers.pop(str(asset.id))
        await self.add_worker(worker)

    async def work(self, asset: Asset) -> None:
        worker: Worker = await self.__pre_run(asset)
        try:
            await self.__run(worker, asset)
        except Exception as err:
            logger.error(f'{asset} work failed: {err}')
        finally:
            await self.__post_run(asset)
