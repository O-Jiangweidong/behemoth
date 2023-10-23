import jwt
import time

from gettext import gettext as _
from datetime import datetime, timedelta
from typing import Callable

from fastapi.requests import Request
from fastapi.responses import Response, JSONResponse
from starlette import status
from starlette.middleware.base import BaseHTTPMiddleware

from settings import settings


class TokenMiddleware(BaseHTTPMiddleware):
    token_expiration: timedelta = timedelta(hours=1)
    url_whitelist: tuple = ('/docs', '/favicon.ico', '/openapi.json')

    async def _refresh_token(self, payload: dict) -> str:
        expiration: int = int((datetime.utcnow() + self.token_expiration).timestamp())
        # 这里添加额外的用户信息
        payload['expire_timestamp'] = expiration
        token = jwt.encode(payload, settings.APP.SECRET_KEY, 'HS256')
        return token

    async def dispatch(
            self, request: Request, call_next: Callable
    ) -> Response:
        if request.url.path not in self.url_whitelist:
            token = request.headers.get('behemoth-token')
            if not token:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED, content={'message': _('Token not found')}
                )
            try:
                payload: dict = jwt.decode(token, settings.APP.SECRET_KEY, 'HS256')
                if payload['expire_timestamp'] > int(time.time()):
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED, content={'message': _('Token has expired')}
                    )
            except jwt.exceptions.DecodeError:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED, content={'message': _('Invalid token')}
                )

        # TODO 这里给request赋值一个user对象
        response = await call_next(request)
        # TODO Token如果要失效了，记得及时续期
        return response
