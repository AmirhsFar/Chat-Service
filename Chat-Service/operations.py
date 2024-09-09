from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from database import db
from datetime import datetime
from schemas import (
    UserModel,
    UserCreate,
    UserInDB,
    ChatRoomCreate,
    ChatRoomModel
)

async def create_user(user: UserCreate) -> UserModel:
    user_dict = user.model_dump()
    user_dict["is_online"] = False
    user_dict["is_admin"] = False
    try:
        result = await db.get_db().users.insert_one(user_dict)
        user_dict["_id"] = str(result.inserted_id)

        return UserModel(**user_dict)
    except DuplicateKeyError as exc:
        raise ValueError("User with this email already exists") from exc

async def get_user_by_email(email: str) -> UserModel | None:
    user = await db.get_db().users.find_one({"email": email})
    if user:
        user_in_db = UserInDB(**user)

        return UserModel(
            id=str(user_in_db.id), **user_in_db.model_dump(exclude={'id'})
        )
    
    return None

async def get_user_by_username(username: str) -> UserModel | None:
    user = await db.get_db().users.find_one({"username": username})
    if user:
        user_in_db = UserInDB(**user)

        return UserModel(
            id=str(user_in_db.id), **user_in_db.model_dump(exclude={'id'})
        )
    
    return None

async def get_user(user_id: str) -> UserModel | None:
    try:
        object_id = ObjectId(user_id)
    except Exception as exc:
        raise ValueError("Invalid user ID") from exc
    user = await db.get_db().users.find_one({'_id': object_id})
    if user:
        user_in_db = UserInDB(**user)

        return UserModel(
            id=str(user_in_db.id), **user_in_db.model_dump(exclude={'id'})
        )
    
    return None

async def create_chat_room(
        chat_room: ChatRoomCreate, owner_id: str
) -> ChatRoomModel:
    chat_room_dict = chat_room.model_dump()
    chat_room_dict["created_at"] = datetime.now()
    chat_room_dict["last_activity"] = None
    chat_room_dict["owner"] = ObjectId(owner_id)
    
    result = await db.get_db().chat_rooms.insert_one(chat_room_dict)
    chat_room_dict["_id"] = str(result.inserted_id)
    chat_room_dict["owner"] = owner_id

    return ChatRoomModel(**chat_room_dict)

async def get_user_chat_rooms(user_id: str) -> list[ChatRoomModel]:
    chat_rooms = await db.get_db().chat_rooms.find(
        {"owner": ObjectId(user_id)}
    ).to_list(None)

    return [ChatRoomModel(
        id=str(room['_id']),
        **{k: v for k, v in room.items() if k not in ('_id', 'owner')},
        owner=str(room['owner'])
                                ) for room in chat_rooms]
