import uuid

from pydantic import BaseModel, ConfigDict, Field


class Asset(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={'table_name': 'assets_asset'}
    )

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
