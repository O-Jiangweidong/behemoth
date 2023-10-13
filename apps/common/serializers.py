import uuid

from gettext import gettext as _

from pydantic import BaseModel, Field


class RootModelSerializer(BaseModel):
    id: uuid.UUID = Field(
        default_factory=lambda: uuid.uuid4(), title=_('ID'),
    )

    async def save(self) -> BaseModel:
        instance: BaseModel = self.Config.model(**self.model_dump())
        return await instance.save()
