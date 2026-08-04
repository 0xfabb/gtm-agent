from pydantic import BaseModel, ConfigDict

class Chat(BaseModel):
    id: str
    