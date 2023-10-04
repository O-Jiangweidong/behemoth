import jwt

from datetime import datetime, timedelta
from typing import Callable

from fastapi.requests import Request
from fastapi.responses import Response, JSONResponse
from starlette import status
from starlette.middleware.base import BaseHTTPMiddleware

from settings import settings


class TokenMiddleware(BaseHTTPMiddleware):
    TOKEN_EXPIRATION = timedelta(hours=24)

    async def _refresh_token(self, payload: dict) -> str:
        expiration = datetime.utcnow() + self.TOKEN_EXPIRATION
        payload['exp'] = expiration
        token = jwt.encode(payload, settings.APP.SECRET_KEY, 'HS256')
        return token

    async def dispatch(
            self, request: Request, call_next: Callable
    ) -> Response:
        token = request.headers.get('behemoth-token')
        if not token:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED, content={'message': 'Invalid token'}
            )
        try:
            payload = jwt.decode(token, settings.APP.SECRET_KEY, 'HS256')
        except jwt.exceptions.DecodeError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED, content={'message': 'Invalid token'}
            )

        # TODO 这里给request赋值一个user对象
        response = await call_next(request)
        return response
