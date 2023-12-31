from __future__ import annotations

import uuid

from typing import Optional
from gettext import gettext as _
from datetime import datetime

from pydantic import BaseModel, Field

from libs.db import DBManager, QuerySet


class RootModel(BaseModel, DBManager):
    id: uuid.UUID = Field(
        default_factory=lambda: uuid.uuid4(), title=_('ID')
    )
    create_time: datetime = Field(
        default_factory=lambda: datetime.now(), title=_('Create time'),
        json_schema_extra={'once': True}
    )
    update_time: datetime = Field(
        default_factory=lambda: datetime.now(), title=_('Update time'),
    )
    comment: str = Field(default='', title=_('Comment'))

    class Config:
        unique_fields: tuple = ('id',)
        foreign_fields: dict = {}
        index_fields: tuple = tuple()
        abstract: bool = False

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
        await self._save(data=self.model_dump(exclude=exclude_fields))
        return self

    @classmethod
    async def list(
            cls: 'RootModel', p: Optional[BaseModel] = None,
            extra_query: Optional[dict] = None, return_model: bool = False
    ) -> QuerySet | list:
        query = {} if p is None else p.model_dump(mode='json')
        if extra_query:
            query.update(extra_query)
        result: dict = await cls._list(query)
        if return_model:
            return [cls(**d) for d in result['data']] # noqa

        queryset: QuerySet = QuerySet(result, model=cls)
        return queryset

