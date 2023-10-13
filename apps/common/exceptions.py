from gettext import gettext as _

from fastapi.requests import Request
from fastapi import FastAPI
from fastapi.exceptions import ValidationException
from fastapi.responses import JSONResponse
from pydantic_core._pydantic_core import ValidationError  # noqa
from starlette import status


async def already_exist_exception_handler(
        request: Request, error: ValidationException
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error.errors()
    )


async def validation_exception_handler(
        request: Request, error: ValidationError
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
    app.add_exception_handler(ValidationException, already_exist_exception_handler)
    app.add_exception_handler(Exception, exception_handler)
