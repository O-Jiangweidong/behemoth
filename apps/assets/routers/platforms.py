from gettext import gettext as _
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from .. import models, serializers


router = APIRouter(tags=[_('platform')])


@router.get(
    '/platforms/', summary=_('List platforms'),
    response_model=List[models.PlatForm]
)
async def list_platforms() -> list[dict]:
    platforms: list[dict] = await models.PlatForm.list()
    return platforms


@router.post(
    '/platforms/', summary=_('Create platform'),
    response_model=models.PlatForm,
)
async def create_platform(instance: serializers.Platform) -> BaseModel:
    instance: BaseModel = await instance.save()
    return instance


@router.get(
    '/platforms/{platform_id}/',
    summary=_('Get platform')
)
async def get_platform() -> dict:
    pass


@router.delete(
    '/platforms/{platform_id}/',
    summary=_('Delete platform')
)
async def delete_platform() -> None:
    pass


@router.put(
    '/platforms/{platform_id}/',
    summary=_('Edit platform')
)
async def edit_platform(instance: serializers.Platform) -> BaseModel:
    instance = instance.save()
    return instance

