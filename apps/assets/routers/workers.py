from gettext import gettext as _
from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from fastapi_pagination import Page, create_page

from assets.const import WorkerCategory
from common.utils import random_string
from libs.db import QuerySet
from libs.pools.worker import WorkerPool
from .. import models, serializers, params


router = APIRouter(tags=[_('Worker')])


@router.post(
    '/workers/', summary=_('Create worker'),
    response_model=models.Worker,
)
async def create_worker(instance: serializers.Worker) -> BaseModel:
    instance: BaseModel = await instance.save()
    await WorkerPool().add_worker(instance)
    return instance


@router.get(
    '/workers/', summary=_('List workers'),
    response_model=Page[models.Worker]
)
async def list_workers(p: params.AssetParams = Depends()) -> Any:
    qs: QuerySet = await models.Worker.list(
        p, extra_query={'platform': WorkerCategory.worker}
    )
    return create_page(qs.data, len(qs), p)


@router.post(
    '/workers/tasks/', summary=_('Create worker task'),
    response_model=models.Worker,
)
async def create_worker_task(instance: serializers.Task) -> BaseModel:
    instance: BaseModel = await instance.save()
    # TODO 这里观察下 instance返回的资产中是id还是一个对象，如果是对象就可以节省一次查询
    task_instance = serializers.TaskInstance(
        id=instance.id, asset=models.Asset.list(extra_query={'asset_id': instance.asset_id}),
        encryption_key=random_string(length=32, upper=False),
    )
    await WorkerPool().work(task_instance)
    return instance
