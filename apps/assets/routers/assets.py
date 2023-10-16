from gettext import gettext as _
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from fastapi_pagination import Page, create_page

from assets.const import TASK_WORKER
from libs.db import QuerySet
from libs.pools.worker import TaskWorkerPool
from .. import models, serializers, params


router = APIRouter(tags=[_('Asset')])


@router.get(
    '/assets/', summary=_('List assets'),
    response_model=Page[models.Asset]
)
async def list_assets(p: params.AssetParams = Depends()) -> Any:
    qs: QuerySet = await models.Asset.list(p)
    return create_page(qs.data, len(qs), p)


@router.post(
    '/assets/', summary=_('Create asset'),
    response_model=models.Asset,
)
async def create_asset(instance: serializers.Asset) -> BaseModel:
    instance: BaseModel = await instance.save()
    return instance


@router.post(
    '/task-workers/', summary=_('Create task worker'),
    response_model=models.TaskWorker,
)
async def create_task_worker(instance: serializers.TaskWorker) -> BaseModel:
    instance: BaseModel = await instance.save()
    await TaskWorkerPool().add_task_worker(instance)
    return instance


@router.get(
    '/task-workers/', summary=_('List task workers'),
    response_model=Page[models.TaskWorker]
)
async def list_task_workers(p: params.AssetParams = Depends()) -> Any:
    qs: QuerySet = await models.TaskWorker.list(
        p, extra_query={'platform': TASK_WORKER}
    )
    return create_page(qs.data, len(qs), p)

