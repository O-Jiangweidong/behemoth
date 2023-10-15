from gettext import gettext as _

from fastapi import APIRouter, Depends
from fastapi_pagination import Page, paginate
from pydantic import BaseModel

from libs.db import QuerySet
from .. import models, serializers, params


router = APIRouter(tags=[_('Account')])


@router.get(
    '/accounts/', summary=_('List accounts'),
    response_model=Page[models.Account]
)
async def list_accounts(p: params.AccountParams = Depends()) -> list[dict]:
    qs: QuerySet = await models.Account.list(p)
    return paginate(qs.data(), p, length_function=lambda x: len(qs))


@router.post(
    '/accounts/', summary=_('Create account'),
    response_model=models.Account, response_model_exclude={'password'}
)
async def create_account(instance: serializers.Account) -> BaseModel:
    instance: BaseModel = await instance.save()
    return instance


@router.get(
    '/accounts/{account_id}/', summary=_('Get account')
)
async def get_account() -> dict:
    pass


@router.delete(
    '/accounts/{account_id}/', summary=_('Delete account')
)
async def delete_account() -> None:
    pass


@router.put(
    '/accounts/{account_id}/', summary=_('Edit account')
)
async def edit_account(instance: serializers.Account) -> BaseModel:
    instance: BaseModel = await instance.save()
    return instance

