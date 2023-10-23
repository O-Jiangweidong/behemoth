from gettext import gettext as _
from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from fastapi_pagination import Page, create_page

from libs.db import QuerySet
from .. import models, serializers, params


router = APIRouter(tags=[_('Asset')])


@router.get(
    '/assets/', summary=_('List assets'),
    response_model=Page[models.Asset]
)
async def list_assets(request: Request, p: params.AssetParams = Depends()) -> Any:
    qs: QuerySet = await models.Asset.list(p)
    return create_page(qs.data, len(qs), p)


@router.post(
    '/assets/', summary=_('Create asset'),
    response_model=models.Asset,
)
async def create_asset(instance: serializers.Asset) -> BaseModel:
    instance: BaseModel = await instance.save()
    return instance
