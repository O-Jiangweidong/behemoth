import uuid

from typing import Optional
from gettext import gettext as _
from datetime import datetime

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

from apps.libs.db import DBManager


class RootModel(BaseModel, DBManager):
    id: uuid.UUID = Field(default_factory=lambda: uuid.uuid4(), title=_('ID'))
    create_time: datetime = Field(
        default_factory=lambda: datetime.now(), title=_('Create time'),
        json_schema_extra={'once': True}
    )
    update_time: datetime = Field(
        default_factory=lambda: datetime.now(), title=_('Update time'),
    )

    class Config:
        pass

    def _get_exclude_fields(self, instance: Optional['RootModel'] = None) -> set:
        exclude = set()
        for name, field in self.model_fields.items():
            extra = field.json_schema_extra
            if not extra:
                continue

            if extra.get('once') and instance:
                exclude.add(name)
        return exclude

    async def save(self) -> BaseModel:
        exclude_fields = self._get_exclude_fields()
        await self._save(
            data=jsonable_encoder(self, exclude=exclude_fields)
        )
        return self

    @classmethod
    async def list(cls) -> list[dict]:
        queryset: list[dict] = await cls._list()
        return queryset

