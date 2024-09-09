from bson import ObjectId
from datetime import datetime
from pydantic import (
    BaseModel,
    EmailStr,
    Field
)


class UserModel(BaseModel):
    id: str | None = Field(alias="_id")
    email: EmailStr
    username: str
    password: str
    is_online: bool = False
    is_admin: bool = False

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "password": "strongpassword",
                "is_online": False,
                "is_admin": False
            }
        }


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str


class UserInDB(UserModel):
    id: ObjectId = Field(alias="_id")

    class Config:
        arbitrary_types_allowed = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None
    username: str | None = None


class ChatRoomCreate(BaseModel):
    name: str
    is_group: bool = True


class ChatRoomModel(BaseModel):
    id: str = Field(alias="_id")
    name: str
    created_at: datetime
    is_group: bool
    last_activity: datetime | None
    owner: str

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": "60d5ecb54c4f5b5c3c7e9b1a",
                "name": "General Chat",
                "created_at": "2023-06-25T12:00:00",
                "is_group": True,
                "last_activity": "2023-06-25T14:30:00",
                "owner": "60d5ecb54c4f5b5c3c7e9b1b"
            }
        }
