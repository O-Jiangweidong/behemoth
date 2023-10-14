import base64

from typing import Any

from pydantic.annotated_handlers import GetCoreSchemaHandler
from pydantic_core import core_schema
from cryptography.fernet import Fernet

from apps.settings import settings


# 创建密码加密上下文
def get_secret_key() -> bytes:
    secret_key: str = settings.APP.SECRET_KEY
    format_key: str = (secret_key + '=' * (32 - len(secret_key) % 32))[:32]
    return base64.urlsafe_b64encode(format_key.encode())


cipher = Fernet(get_secret_key())


class EncryptedField(str):
    def __init__(self, secret_value: str) -> None:
        self._secret_value: str = cipher.encrypt(secret_value.encode()).decode()

    def __str__(self) -> str:
        return self._secret_value

    def __repr__(self) -> str:
        return self.__str__()

    @classmethod
    def __get_pydantic_core_schema__(
            cls, source: type[Any], handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:

        # def serialize(value: str, info: core_schema.SerializationInfo) -> str:
        #     这里序列化的时候转为明文
        #     return value

        s = core_schema.union_schema(
            [
                core_schema.is_instance_schema(source),
                core_schema.no_info_after_validator_function(
                    source, core_schema.str_schema(),
                ),
            ],
            # serialization=core_schema.plain_serializer_function_ser_schema(
            #     serialize,
            #     info_arg=True,
            #     return_schema=core_schema.str_schema(),
            #     when_used='json',
            # ),
        )
        return s
