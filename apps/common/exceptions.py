from __future__ import annotations

from gettext import gettext as _

from elastic_transport import ConnectionTimeout
from fastapi.requests import Request
from fastapi import FastAPI
from fastapi.exceptions import ValidationException
from fastapi.responses import JSONResponse
from pydantic_core._pydantic_core import ValidationError  # noqa
from starlette import status


class WorkerException(ValidationException):
    pass


async def es_connect_timeout_handler(
        request: Request, error: ConnectionTimeout
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_408_REQUEST_TIMEOUT,
        content={'error': _('Elasticsearch query times out')}
    )


async def validation_exception_handler(
        request: Request, error: ValidationError | ValidationException
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={'error': error.errors()}
    )


async def exception_handler(
        request: Request, error: Exception
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            'error': _('Server error')
        }
    )


def register_exceptions(app: FastAPI) -> None:
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationException, validation_exception_handler)
    app.add_exception_handler(ConnectionTimeout, es_connect_timeout_handler)
    app.add_exception_handler(Exception, exception_handler)
