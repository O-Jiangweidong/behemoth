from pydantic import BaseModel


class RootModelSerializer(BaseModel):
    def save(self) -> BaseModel:
        instance: BaseModel = self.Config.model(**self.model_dump())
        return instance.save()
