from gettext import gettext as _

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from .. import models, serializers, params


router = APIRouter(tags=[_('Asset')])


@router.get('/assets/', summary=_('List assets'))
async def list_assets(p: params.PlatformParams = Depends()) -> list[dict]:
    pass


@router.post(
    '/assets/', summary=_('Create asset'),
    response_model=models.Asset,
)
async def create_asset(instance: serializers.Asset) -> BaseModel:
    instance: BaseModel = await instance.save()
    return instance
