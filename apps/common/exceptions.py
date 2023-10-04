from gettext import gettext as _

from fastapi.requests import Request
from fastapi.responses import JSONResponse
from starlette import status

from apps.main import app


@app.exception_handler(Exception)
async def exception_handler(
        request: Request, error: Exception
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            'message': _('Server error')
        }
    )
