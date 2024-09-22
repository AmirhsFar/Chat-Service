from datetime import datetime
from enum import Enum
from bson import ObjectId
from pydantic import (
    BaseModel,
    EmailStr,
    Field
)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None
    username: str | None = None


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
                "id": "60d5ecb54c4f5b5c3c7e9b1a",
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

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "password": "strongpassword"
            }
        }


class UserShow(BaseModel):
    id: str = Field(alias="_id")
    email: EmailStr
    username: str
    is_online: bool

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": "60d5ecb54c4f5b5c3c7e9b1a",
                "email": "user@example.com",
                "username": "johndoe",
                "is_online": False
            }
        }


class UserUpdate(BaseModel):
    username: str | None = None
    email: EmailStr | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "johndoe"
            }
        }


class UserInDB(UserModel):
    id: ObjectId = Field(alias="_id")

    class Config:
        arbitrary_types_allowed = True


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


class ChatRoomShow(BaseModel):
    id: str = Field(alias="_id")
    name: str
    created_at: datetime
    is_group: bool
    last_activity: datetime | None = None
    owner: UserUpdate | None = None

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": "60d5ecb54c4f5b5c3c7e9b1a",
                "name": "General Chat",
                "created_at": "2023-06-25T12:00:00",
                "is_group": True,
                "last_activity": "2023-06-25T14:30:00",
                "owner": {
                    "email": "user@example.com",
                    "username": "johndoe"
                }
            }
        }


class ChatRoomUpdate(BaseModel):
    name: str

    class Config:
        json_schema_extra = {
            "example": {
                "name": "General Chat"
            }
        }


class JoinRequestCreate(BaseModel):
    message: str | None = None
    chat_room_id: str


class JoinRequestModel(BaseModel):
    id: str = Field(alias="_id")
    message: str | None = None
    approved: bool | None = None
    user_id: str
    chat_room_id: str

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": "60d5rgb54c4f5b5c3c7e9b1a",
                "message": "Please approve my request",
                "approved": True,
                "user_id": "60d5ecb54c4f5b5c3c7e9b1b",
                "chat_room_id": "81a5ecb54c4f5n5c3e7o9b2u"
            }
        }


class JoinRequestShow(BaseModel):
    id: str = Field(alias="_id")
    message: str | None = None
    approved: bool | None = None
    user: UserUpdate | None = None
    chat_room: ChatRoomCreate | None = None

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": "60d5rgb54c4f5b5c3c7e9b1a",
                "message": "Please approve my request",
                "approved": True,
                "user": {
                    "email": "user@example.com",
                    "username": "johndoe"
                },
                "chat_room": {
                    "name": "General Chat",
                    "is_group": True,
                }
            }
        }


class ChatRoomSessionModel(BaseModel):
    id: str = Field(alias="_id")
    created_at: datetime
    last_seen: datetime | None = None
    user_id: str
    chat_room_id: str

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": "60d5elo54c4f5s5c9u7e9b1v",
                "created_at": "2023-06-25T12:00:00",
                "last_seen": "2023-07-12T14:45:00",
                "user_id": "60d5ecb54c4f5b5c3c7e9b1b",
                "chat_room_id": "93d5ecb54l4f5b5k3b7e9p3f"
            }
        }


class ChatRoomSessionShow(BaseModel):
    id: str = Field(alias="_id")
    created_at: datetime
    last_seen: datetime | None = None
    user: UserUpdate | None = None
    chat_room: ChatRoomCreate | None = None

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": "60d5elo54c4f5s5c9u7e9b1v",
                "created_at": "2023-06-25T12:00:00",
                "last_seen": "2023-07-12T14:45:00",
                "user": {
                    "email": "user@example.com",
                    "username": "johndoe"
                },
                "chat_room": {
                    "name": "General Chat",
                    "is_group": True,
                }
            }
        }


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"


class MessageModel(BaseModel):
    id: str
    user_id: str
    chat_room_id: str
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
