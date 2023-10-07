from gettext import gettext as _

from fastapi import APIRouter


router = APIRouter(tags=[_('assets')])


@router.get('/assets/', summary=_('List assets'))
async def list_assets() -> list[dict]:
    pass
