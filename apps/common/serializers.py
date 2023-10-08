from pydantic import BaseModel


class RootModelSerializer(BaseModel):
    async def save(self) -> BaseModel:
        instance: BaseModel = self.Config.model(**self.model_dump())
        return await instance.save()
