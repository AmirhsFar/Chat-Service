from pydantic import BaseModel
from datetime import datetime


class ItemBase(BaseModel):
    title: str
    description: str | None = None


class ItemCreate(ItemBase):
    pass


class Item(ItemBase):
    id: str


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: str
    is_active: bool
    items: list[Item]


class MessageModel(BaseModel):
    id: str
    user_id: str
    content: str
    timestamp: datetime

    def dict_with_iso_timestamp(self):
        d = self.model_dump()
        d['timestamp'] = d['timestamp'].isoformat()
        return d
