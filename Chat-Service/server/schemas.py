"""
schemas.py

This module defines the database schema and data models used in the 
FastAPI project. These models are created using Pydantic BaseModels 
to structure and validate data. They define users, chat rooms, messages, 
and other entities in the application's database.

Classes:
    Token: Represents a JWT access token and its type.
    TokenData: Holds optional token-related data like email or username.
    UserModel: Represents the structure of a user in the system, including 
        attributes like email and password.
    UserCreate: Defines the structure required when creating a new user.
    UserShow: Represents a user object for displaying user information.
    UserUpdate: Defines the structure for updating user information.
    UserInDB: Extends UserModel to include ObjectId for MongoDB.
    ChatRoomCreate: Defines the structure for creating a new chat room.
    ChatRoomModel: Represents a chat room entity in the database, 
        including attributes like name and owner.
    ChatRoomShow: Represents a chat room object for display purposes.
    ChatRoomUpdate: Defines the structure for updating chat room information.
    JoinRequestCreate: Represents a user's request to join a chat room.
    JoinRequestModel: Represents a join request in the database, including 
        approval status and user information.
    JoinRequestShow: Displays a join request along with user and 
        chat room information.
    ChatRoomSessionModel: Represents a session in a chat room, including 
        timestamps and user details.
    ChatRoomSessionShow: Displays chat room session data.
    MessageType: Enum defining the type of messages (text, image, or file).
    MessageModel: Represents a message in a chat room, including user, 
        content, and timestamp.
"""

from datetime import datetime
from enum import Enum
from bson import ObjectId
from pydantic import (
    BaseModel,
    EmailStr,
    Field
)


class Token(BaseModel):
    """
    Represents a JWT access token and its type.

    Attributes:
        access_token (str): The JWT access token.
        token_type (str): The type of the token (typically "Bearer").
    """
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
    Contains optional token-related data, such as 
    the user's email or username.

    Attributes:
        email (str | None): The email of the user.
        username (str | None): The username of the user.
    """
    email: str | None = None
    username: str | None = None


class UserModel(BaseModel):
    """
    Represents the structure of a user in the database.

    Attributes:
        id (str | None): The unique identifier for the user, mapped from 
            `_id` in MongoDB.
        email (EmailStr): The unique email of the user.
        username (str): The unique username of the user.
        password (str): The hashed password of the user.
        is_online (bool): Indicates whether the user is online.
        is_admin (bool): Indicates whether the user has admin privileges.
    """
    id: str | None = Field(alias="_id")
    email: EmailStr
    username: str
    password: str
    is_online: bool = False
    is_admin: bool = False

    class Config:
        """
        Sets UserModel class configurations.

        Variables:
            populate_by_name (bool): The status that is set to True, 
                which means that when a dictionary is passed to the 
                Pydantic model, the keys of the dictionary are 
                matched to the field names of the model.
            json_schema_extra (dict): The dictionary which shows the 
                user who utilizes the FastAPI swagger an example of 
                what the shape of input should be.
        """
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
    """
    Defines the structure required when creating a new user.

    Attributes:
        email (EmailStr): The email of the new user.
        username (str): The username of the new user.
        password (str): The password of the new user.
    """
    email: EmailStr
    username: str
    password: str

    class Config:
        """
        Sets UserModel class configurations.

        Variables:
            json_schema_extra (dict): The dictionary which shows the 
                user who utilizes the FastAPI swagger an example of 
                what the shape of input should be.
        """
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "password": "strongpassword"
            }
        }


class UserShow(BaseModel):
    """
    Represents a user object for displaying user information.

    Attributes:
        id (str): The unique identifier of the user, mapped from 
            `_id` in MongoDB.
        email (EmailStr): The email of the user.
        username (str): The username of the user.
        is_online (bool): Indicates whether the user is online.
    """
    id: str = Field(alias="_id")
    email: EmailStr
    username: str
    is_online: bool

    class Config:
        """
        Sets UserModel class configurations.

        Variables:
            populate_by_name (bool): The status that is set to True, 
                which means that when a dictionary is passed to the 
                Pydantic model, the keys of the dictionary are 
                matched to the field names of the model.
            json_schema_extra (dict): The dictionary which shows the 
                user who utilizes the FastAPI swagger an example of 
                what the shape of input should be.
        """
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
    """
    Defines the structure for updating user information.

    Attributes:
        username (str | None): The updated username, if provided.
        email (EmailStr | None): The updated email, if provided.
    """
    username: str | None = None
    email: EmailStr | None = None

    class Config:
        """
        Sets UserModel class configurations.

        Variables:
            json_schema_extra (dict): The dictionary which shows the 
                user who utilizes the FastAPI swagger an example of 
                what the shape of input should be.
        """
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "johndoe"
            }
        }


class UserInDB(UserModel):
    """
    Extends the `UserModel` to include an ObjectId for MongoDB.

    Attributes:
        id (ObjectId): The unique MongoDB ObjectId for the user.
    """
    id: ObjectId = Field(alias="_id")

    class Config:
        """
        Sets UserModel class configurations.

        Variables:
            arbitrary_types_allowed (bool): The status that is set to True, 
                which means that Pydantic gets more lenient. It will allow 
                values of any type to be assigned to fields.
        """
        arbitrary_types_allowed = True


class ChatRoomCreate(BaseModel):
    """
    Defines the structure for creating a new chat room.

    Attributes:
        name (str): The name of the chat room.
        is_group (bool): Whether the chat room is a group chat.
    """
    name: str
    is_group: bool = True


class ChatRoomModel(BaseModel):
    """
    Represents a chat room entity in the database.

    Attributes:
        id (str): The unique identifier of the chat room.
        name (str): The name of the chat room.
        created_at (datetime): The timestamp representing the 
            date and the time at which the chat room was created.
        is_group (bool): Whether the chat room is a group chat.
        last_activity (datetime | None): The timestamp of the last 
            activity in the chat room.
        owner (str): The ID of the owner of the chat room.
    """
    id: str = Field(alias="_id")
    name: str
    created_at: datetime
    is_group: bool
    last_activity: datetime | None
    owner: str

    class Config:
        """
        Sets UserModel class configurations.

        Variables:
            populate_by_name (bool): The status that is set to True, 
                which means that when a dictionary is passed to the 
                Pydantic model, the keys of the dictionary are 
                matched to the field names of the model.
            json_schema_extra (dict): The dictionary which shows the 
                user who utilizes the FastAPI swagger an example of 
                what the shape of input should be.
        """
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
    """
    Represents a chat room object for display purposes.

    Attributes:
        id (str): The unique identifier of the chat room.
        name (str): The name of the chat room.
        created_at (datetime): The timestamp representing the 
            date and the time at which the chat room was created.
        is_group (bool): Whether the chat room is a group chat.
        last_activity (datetime | None): The timestamp of the 
            last activity in the chat room.
        owner (UserUpdate | None): The owner of the chat room.
    """
    id: str = Field(alias="_id")
    name: str
    created_at: datetime
    is_group: bool
    last_activity: datetime | None = None
    owner: UserUpdate | None = None

    class Config:
        """
        Sets UserModel class configurations.

        Variables:
            populate_by_name (bool): The status that is set to True, 
                which means that when a dictionary is passed to the 
                Pydantic model, the keys of the dictionary are 
                matched to the field names of the model.
            json_schema_extra (dict): The dictionary which shows the 
                user who utilizes the FastAPI swagger an example of 
                what the shape of input should be.
        """
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
    """
    Defines the structure for updating a chat room's information.

    Attributes:
        name (str): The updated name of the chat room.
    """
    name: str

    class Config:
        """
        Sets UserModel class configurations.

        Variables:
            json_schema_extra (dict): The dictionary which shows the 
                user who utilizes the FastAPI swagger an example of 
                what the shape of input should be.
        """
        json_schema_extra = {
            "example": {
                "name": "General Chat"
            }
        }


class JoinRequestCreate(BaseModel):
    """
    Defines the structure for creating a request to join a chat room.

    Attributes:
        message (str | None): Optional message from the user requesting 
            to join the chat room.
        chat_room_id (str): The ID of the chat room the user wants to join.
    """
    message: str | None = None
    chat_room_id: str


class JoinRequestModel(BaseModel):
    """
    Represents a join request in the database.

    Attributes:
        id (str): The unique identifier of the join request.
        message (str | None): Optional message from the user requesting 
            to join the chat room.
        approved (bool | None): Whether the join request 
            has been approved or not.
        user_id (str): The ID of the user making the request.
        chat_room_id (str): The ID of the chat room the request is for.
    """
    id: str = Field(alias="_id")
    message: str | None = None
    approved: bool | None = None
    user_id: str
    chat_room_id: str

    class Config:
        """
        Sets UserModel class configurations.

        Variables:
            populate_by_name (bool): The status that is set to True, 
                which means that when a dictionary is passed to the 
                Pydantic model, the keys of the dictionary are 
                matched to the field names of the model.
            json_schema_extra (dict): The dictionary which shows the 
                user who utilizes the FastAPI swagger an example of 
                what the shape of input should be.
        """
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
    """
    Displays a join request along with user and chat room information.

    Attributes:
        id (str): The unique identifier of the join request.
        message (str | None): Optional message from the user requesting 
            to join the chat room.
        approved (bool | None): Whether the join request 
            has been approved or not.
        user (UserUpdate | None): The user making the join request.
        chat_room (ChatRoomCreate | None): The chat room to which 
            the user is requesting access.
    """
    id: str = Field(alias="_id")
    message: str | None = None
    approved: bool | None = None
    user: UserUpdate | None = None
    chat_room: ChatRoomCreate | None = None

    class Config:
        """
        Sets UserModel class configurations.

        Variables:
            populate_by_name (bool): The status that is set to True, 
                which means that when a dictionary is passed to the 
                Pydantic model, the keys of the dictionary are 
                matched to the field names of the model.
            json_schema_extra (dict): The dictionary which shows the 
                user who utilizes the FastAPI swagger an example of 
                what the shape of input should be.
        """
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
    """
    Represents a session in a chat room, tracking user activity.

    Attributes:
        id (str): The unique identifier of the session.
        created_at (datetime): The timestamp when the session was created.
        last_seen (datetime | None): The timestamp of 
            the user's last activity in the session.
        user_id (str): The ID of the user in the session.
        chat_room_id (str): The ID of the chat room 
            associated with the session.
    """
    id: str = Field(alias="_id")
    created_at: datetime
    last_seen: datetime | None = None
    user_id: str
    chat_room_id: str

    class Config:
        """
        Sets UserModel class configurations.

        Variables:
            populate_by_name (bool): The status that is set to True, 
                which means that when a dictionary is passed to the 
                Pydantic model, the keys of the dictionary are 
                matched to the field names of the model.
            json_schema_extra (dict): The dictionary which shows the 
                user who utilizes the FastAPI swagger an example of 
                what the shape of input should be.
        """
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
    """
    Displays chat room session data for viewing purposes.

    Attributes:
        id (str): The unique identifier of the session.
        created_at (datetime): The timestamp when the session was created.
        last_seen (datetime | None): The timestamp of the 
            user's last activity in the session.
        user (UserUpdate | None): The user participating in the session.
        chat_room (ChatRoomCreate | None): The chat room associated 
            with the session.
    """
    id: str = Field(alias="_id")
    created_at: datetime
    last_seen: datetime | None = None
    user: UserUpdate | None = None
    chat_room: ChatRoomCreate | None = None

    class Config:
        """
        Sets UserModel class configurations.

        Variables:
            populate_by_name (bool): The status that is set to True, 
                which means that when a dictionary is passed to the 
                Pydantic model, the keys of the dictionary are 
                matched to the field names of the model.
            json_schema_extra (dict): The dictionary which shows the 
                user who utilizes the FastAPI swagger an example of 
                what the shape of input should be.
        """
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
    """
    An enumeration of the types of messages that can be sent in a chat.

    Enum members:
        TEXT: A text message.
        IMAGE: An image message.
        FILE: A file message.
    """
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"


class MessageModel(BaseModel):
    """
    Represents a message in a chat room.

    Attributes:
        id (str): The unique identifier of the message.
        user_id (str): The ID of the user who sent the message.
        chat_room_id (str): The ID of the chat room where the 
            message was sent.
        username (str): The username of the sender.
        content (str): The content of the message.
        timestamp (datetime): The timestamp when the message was sent.
        message_type (MessageType): The type of message 
            (e.g., text, image, or file).
        file_name (str | None): The name of the file, 
            if the message is a file.
        file_path (str | None): The file path, if the message is a file.
    """
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
        """
        Converts the MessageModel instance into a dictionary with 
        ISO-formatted timestamp and message type.

        This method transforms the `timestamp` attribute into an ISO 8601 
        string and converts the `message_type` enum to its string value, 
        making the dictionary JSON serializable.

        Returns:
            dict: The MessageModel instance as a dictionary with 
                ISO-formatted `timestamp` and `message_type` values.
        """
        d = self.model_dump()
        d['timestamp'] = d['timestamp'].isoformat()
        d['message_type'] = d['message_type'].value
        
        return d
