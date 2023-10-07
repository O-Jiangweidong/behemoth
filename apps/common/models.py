import uuid

from typing import Optional
from gettext import gettext as _
from datetime import datetime

from pydantic import BaseModel, Field

from apps.libs.db import DBManager


class RootModel(BaseModel, DBManager):
    id: uuid.UUID = Field(default_factory=lambda: uuid.uuid4().hex, title=_('ID'))
    create_time: datetime = Field(
        default_factory=lambda: datetime.now(), title=_('Create time'),
        json_schema_extra={'once': True}
    )
    update_time: datetime = Field(
        default_factory=lambda: datetime.now(), title=_('Update time'),
    )

    class Config:
        pass

    def _filtration(self, instance: Optional['RootModel'] = None) -> 'RootModel':
        for name, field in self.model_fields.items():
            extra = field.json_schema_extra
            if not extra:
                continue

            if extra.get('once'):
                if instance:
                    setattr(self, name, getattr(instance, name))
                else:
                    setattr(self, name, field.default_factory())
        return self

    def save(self) -> 'RootModel':
        self._filtration()
        return self

