from gettext import gettext as _

from fastapi import Query
from fastapi_pagination.default import Params


class RootParams(Params):
    page: int = Query(1, ge=1, description=_('Page number'))
    size: int = Query(15, ge=1, le=100, description=_('Page size'))
