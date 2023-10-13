from gettext import gettext as _

from fastapi import APIRouter, Depends
from fastapi_pagination import Page, paginate
from pydantic import BaseModel

from apps.libs.db import QuerySet
from .. import models, serializers, params


router = APIRouter(tags=[_('Platform')])


@router.get(
    '/platforms/', summary=_('List platforms'),
    response_model=Page[models.PlatForm]
)
async def list_platforms(p: params.PlatformParams = Depends()) -> list[dict]:
    qs: QuerySet = await models.PlatForm.list(p)
    print(p)
    return paginate(qs.data(), p, length_function=lambda x: len(qs))


@router.post(
    '/platforms/', summary=_('Create platform'),
    response_model=models.PlatForm,
)
async def create_platform(instance: serializers.Platform) -> BaseModel:
    instance: BaseModel = await instance.save()
    return instance


@router.get(
    '/platforms/{platform_id}/', summary=_('Get platform')
)
async def get_platform() -> dict:
    pass


@router.delete(
    '/platforms/{platform_id}/', summary=_('Delete platform')
)
async def delete_platform() -> None:
    pass


@router.put(
    '/platforms/{platform_id}/',
    summary=_('Edit platform')
)
async def edit_platform(instance: serializers.Platform) -> BaseModel:
    instance = await instance.save()
    return instance

