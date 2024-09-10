from datetime import datetime
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from database import db
from utils import get_password_hash
from schemas import (
    UserModel,
    UserCreate,
    UserInDB,
    ChatRoomCreate,
    UserShow,
    UserUpdate,
    ChatRoomShow,
    ChatRoomUpdate,
    JoinRequestCreate,
    JoinRequestShow
)

async def create_user(user: UserCreate) -> UserModel:
    user_dict = user.model_dump()
    user_dict["is_online"] = False
    admin_count = await db.get_db().users.count_documents({
        "is_admin": True
    })
    user_dict["is_admin"] = admin_count == 0
    user_dict["password"] = get_password_hash(user_dict["password"])
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

async def get_user(user_id: str) -> UserShow | None:
    try:
        object_id = ObjectId(user_id)
    except Exception as exc:
        raise ValueError("Invalid user ID") from exc
    user = await db.get_db().users.find_one({'_id': object_id})
    if user:

        return UserShow(
            id=str(user['_id']),
            **{k: v for k, v in user.items() if k not in ('_id', 'id')}
        )
    
    return None

async def create_chat_room(
        chat_room: ChatRoomCreate, owner_id: str
) -> ChatRoomShow:
    chat_room_dict = chat_room.model_dump()
    chat_room_dict["created_at"] = datetime.now()
    chat_room_dict["last_activity"] = None
    chat_room_dict["owner"] = ObjectId(owner_id)
    
    result = await db.get_db().chat_rooms.insert_one(chat_room_dict)
    chat_room_dict["_id"] = str(result.inserted_id)

    try:
        object_id = ObjectId(owner_id)
    except Exception as exc:
        raise ValueError("Invalid user ID") from exc
    user = await db.get_db().users.find_one({'_id': object_id})
    owner = UserUpdate(**user)
    chat_room_dict['owner'] = owner

    return ChatRoomShow(**chat_room_dict)

async def get_user_chat_rooms(user_id: str) -> list[ChatRoomShow]:
    chat_rooms = await db.get_db().chat_rooms.find(
        {"owner": ObjectId(user_id)}
    ).to_list(None)

    return [ChatRoomShow(
        id=str(room['_id']),
        **{k: v for k, v in room.items() if k not in (
            '_id', 'id', 'owner'
        )}
                                ) for room in chat_rooms]

async def get_all_users() -> list[UserShow]:
    users = await db.get_db().users.find().to_list(None)

    return [UserShow(
        id=str(user['_id']),
        **{k: v for k, v in user.items() if k not in ('_id', 'id')}
                                ) for user in users]

async def update_user(user_id: str, update_data: UserUpdate) -> UserShow:
    if "username" in update_data:
        existing_user = await db.get_db().users.find_one({
            "username": update_data["username"],
            "_id": {"$ne": ObjectId(user_id)}
        })
        if existing_user:
            raise ValueError("Username already exists")

    if "email" in update_data:
        existing_user = await db.get_db().users.find_one({
            "email": update_data["email"],
            "_id": {"$ne": ObjectId(user_id)}
        })
        if existing_user:
            raise ValueError("Email already exists")

    result = await db.get_db().users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': update_data}
    )
    if result.modified_count == 0:
        raise ValueError("User not found or no changes made")
    updated_user = await get_user(user_id)

    return updated_user

async def delete_user(user_id: str) -> bool:
    user = await db.get_db().users.find_one({'_id': ObjectId(user_id)})
    if user and user.get('is_admin'):
        raise ValueError("Cannot delete admin user")

    await db.get_db().chat_rooms.delete_many({'owner': ObjectId(user_id)})
    result = await db.get_db().users.delete_one({'_id': ObjectId(user_id)})

    return result.deleted_count > 0

async def get_all_chat_rooms() -> list[ChatRoomShow]:
    chat_rooms = await db.get_db().chat_rooms.find().to_list(None)
    result_chat_rooms = []
    for room in chat_rooms:
        user = await db.get_db().users.find_one({
            '_id': room['owner']
        })
        owner = UserUpdate(**user)
        result_chat_rooms.append(
            ChatRoomShow(
                id=str(room['_id']),
                **{k: v for k, v in room.items() if k not in (
                    '_id', 'id', 'owner'
                )},
                owner=owner,
            )
        )

    return result_chat_rooms

async def get_chat_room(
        chat_room_id: str, is_group: bool
) -> ChatRoomShow | None:
    chat_room = await db.get_db().chat_rooms.find_one({
        '_id': ObjectId(chat_room_id),
        'is_group': is_group
    })

    if chat_room:
        user = await db.get_db().users.find_one({
            '_id': chat_room['owner']
        })
        owner = UserUpdate(**user)

        return ChatRoomShow(
            id=str(chat_room['_id']),
            **{k: v for k, v in chat_room.items() if k not in (
                '_id', 'id', 'owner'
            )},
            owner=owner
        )
    
    return None

async def update_chat_room(
        chat_room_id: str, update_data: ChatRoomUpdate
) -> ChatRoomShow:
    result = await db.get_db().chat_rooms.update_one(
        {'_id': ObjectId(chat_room_id)},
        {'$set': update_data}
    )
    if result.modified_count == 0:
        raise ValueError("Chat room not found or no changes made")
    updated_chat_room = await db.get_db().chat_rooms.find_one({
        '_id': ObjectId(chat_room_id)
    })

    return updated_chat_room

async def delete_chat_room(chat_room_id: str) -> bool:
    result = await db.get_db().chat_rooms.delete_one({
        '_id': ObjectId(chat_room_id)
    })

    return result.deleted_count > 0

async def create_join_request(
        join_request: JoinRequestCreate, user_id: str
) -> JoinRequestShow:
    join_req_dict = join_request.model_dump()
    chat_room_id = join_req_dict['chat_room_id']
    join_req_dict["user_id"] = ObjectId(user_id)
    join_req_dict["chat_room_id"] = ObjectId(chat_room_id)
    
    result = await db.get_db().join_requests.insert_one(join_req_dict)
    join_req_dict["_id"] = str(result.inserted_id)

    try:
        object_id = ObjectId(chat_room_id)
    except Exception as exc:
        raise ValueError("Invalid user ID") from exc
    chat_room = await db.get_db().chat_rooms.find_one({'_id': object_id})
    chat_room = ChatRoomCreate(**chat_room)
    join_req_dict['chat_room'] = chat_room

    try:
        object_id = ObjectId(user_id)
    except Exception as exc:
        raise ValueError("Invalid user ID") from exc
    user = await db.get_db().users.find_one({'_id': object_id})
    owner = UserUpdate(**user)
    join_req_dict['user'] = owner

    return JoinRequestShow(**join_req_dict)

async def get_all_join_requests() -> list[JoinRequestShow]:
    join_requests = await db.get_db().join_requests.find().to_list(None)
    result_join_requests = []
    for join_request in join_requests:
        user = await db.get_db().users.find_one({
            '_id': join_request['user_id']
        })
        chat_room = await db.get_db().chat_rooms.find_one({
            '_id': join_request['chat_room_id']
        })
        owner = UserUpdate(**user)
        room = ChatRoomCreate(**chat_room)
        result_join_requests.append(
            JoinRequestShow(
                id=str(join_request['_id']),
                **{k: v for k, v in join_request.items() if k not in (
                    '_id', 'id'
                )},
                user=owner,
                chat_room=room
            )
        )

    return result_join_requests
