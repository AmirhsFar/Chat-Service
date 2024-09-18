from datetime import datetime
from pydantic import BaseModel, EmailStr
from enum import Enum


class ItemBase(BaseModel):
    title: str
    description: str | None = None


class ItemCreate(ItemBase):
    pass


class Item(ItemBase):
    id: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None
    username: str | None = None


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str


class User(UserCreate):
    id: str
    is_online: bool = False
    items: list[Item]


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"


class MessageModel(BaseModel):
    id: str
    user_id: str
    username: str
    content: str
    timestamp: datetime
    message_type: MessageType
    file_name: str | None = None
    file_path: str | None = None

    def dict_with_iso_timestamp(self):
        d = self.model_dump()
        d['timestamp'] = d['timestamp'].isoformat()
        d['message_type'] = d['message_type'].value
        
        return d
