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
    ChatRoomModel,
    ChatRoomShow,
    ChatRoomUpdate,
    JoinRequestCreate,
    JoinRequestShow,
    ChatRoomSessionModel,
    ChatRoomSessionShow,
    MessageModel,
    MessageType
)
from fastapi import (
    HTTPException,
    status
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
    user = await db.get_db().users.find_one({'_id': ObjectId(user_id)})
    if user:

        return UserShow(
            id=str(user['_id']),
            **{k: v for k, v in user.items() if k not in ('_id', 'id')}
        )
    
    return None


async def create_session(user_id: str, chat_room_id: str):
    session_dict = {}
    session_dict["created_at"] = datetime.now()
    session_dict["last_seen"] = None
    session_dict["user_id"] = ObjectId(user_id)
    session_dict["chat_room_id"] = ObjectId(chat_room_id)

    result = await db.get_db().chat_room_sessions.insert_one(session_dict)
    session_dict["_id"] = str(result.inserted_id)
    user = await db.get_db().users.find_one({'_id': ObjectId(user_id)})
    chat_room = await db.get_db().chat_rooms.find_one({
        '_id': ObjectId(chat_room_id)
    })
    session_dict['user'] = UserUpdate(**user)
    session_dict['chat_room'] = ChatRoomCreate(**chat_room)

    return ChatRoomSessionShow(**session_dict)


async def create_chat_room(
        chat_room: ChatRoomUpdate, owner_id: str, is_group: bool
) -> dict:
    chat_room_dict = chat_room.model_dump()
    chat_room_dict["created_at"] = datetime.now()
    chat_room_dict['is_group'] = is_group
    chat_room_dict["last_activity"] = None
    creators_id = ObjectId(owner_id)
    chat_room_dict["owner"] = creators_id
    result = await db.get_db().chat_rooms.insert_one(chat_room_dict)
    chat_room_id = str(result.inserted_id)
    chat_room_dict["_id"] = chat_room_id
    user = await db.get_db().users.find_one({'_id': creators_id})
    owner = UserUpdate(**user)
    chat_room_dict['owner'] = owner

    session = await create_session(owner_id, chat_room_id)

    return {
        'chat_room': ChatRoomShow(**chat_room_dict),
        'session': session
    }


async def get_user_chat_rooms(user_id: str) -> list[ChatRoomShow]:
    chat_rooms = await db.get_db().chat_rooms.find(
        {"is_group": True, "owner": ObjectId(user_id)}
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
    await db.get_db().chat_room_sessions.delete_many({
        'user_id': ObjectId(user_id)
    })
    await db.get_db().join_requests.delete_many({
        'user_id': ObjectId(user_id)
    })
    await db.get_db().messages.delete_many({
        'user_id': user_id
    })
    result = await db.get_db().users.delete_one({'_id': ObjectId(user_id)})

    return result.deleted_count > 0


async def transform_chat_rooms(
        chat_rooms: list[dict]
) -> list[ChatRoomShow]:
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


async def get_all_chat_rooms() -> list[ChatRoomShow]:
    chat_rooms = await db.get_db().chat_rooms.find().to_list(None)
    tr_chat_rooms = await transform_chat_rooms(chat_rooms)

    return tr_chat_rooms


async def get_chat_room(
        chat_room_id: str, is_group: bool | None = None
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
    updated_chat_room["_id"] = str(updated_chat_room["_id"])
    owner = await db.get_db().users.find_one({
        "_id": updated_chat_room["owner"]
    })
    updated_chat_room["owner"] = UserUpdate(**owner)

    return ChatRoomShow(**updated_chat_room)


async def delete_chat_room(chat_room_id: str) -> bool:
    await db.get_db().chat_room_sessions.delete_many({
        'chat_room_id': ObjectId(chat_room_id)
    })
    await db.get_db().join_requests.delete_many({
        'chat_room_id': ObjectId(chat_room_id)
    })
    await db.get_db().messages.delete_many({
        'chat_room_id': chat_room_id
    })
    result = await db.get_db().chat_rooms.delete_one({
        '_id': ObjectId(chat_room_id)
    })

    return result.deleted_count > 0


async def create_join_request(
        join_request: JoinRequestCreate, user_id: str
) -> JoinRequestShow:
    join_req_dict = join_request.model_dump()

    try:
        requested_chat_rooms_id = ObjectId(join_req_dict["chat_room_id"])
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid chat room ID"
        ) from exc
    
    users_chat_room = await db.get_db().chat_rooms.find_one({
        '_id': requested_chat_rooms_id,
        'owner': ObjectId(user_id)
    })
    if users_chat_room:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot submit a request to join your own chat room!"
        )

    join_req_dict["approved"] = None
    join_req_dict["user_id"] = ObjectId(user_id)
    join_req_dict["chat_room_id"] = requested_chat_rooms_id
    existing_join_request = await db.get_db().join_requests.find_one({
        'user_id': join_req_dict["user_id"],
        'chat_room_id': join_req_dict["chat_room_id"]
    })
    if existing_join_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='You have submitted your request before'
        )
    
    result = await db.get_db().join_requests.insert_one(join_req_dict)
    join_req_dict["_id"] = str(result.inserted_id)

    chat_room = await db.get_db().chat_rooms.find_one({
        '_id': requested_chat_rooms_id
    })
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


async def transform_join_requests(
        join_requests: list[dict]
) -> list[JoinRequestShow]:
    result_join_requests = []
    for join_request in join_requests:
        user = await db.get_db().users.find_one({
            '_id': join_request['user_id']
        })
        chat_room = await db.get_db().chat_rooms.find_one({
            '_id': join_request['chat_room_id']
        })
        if user:
            owner = UserUpdate(**user)
        else:
            owner = None
        if chat_room:
            room = ChatRoomCreate(**chat_room)
        else:
            room = None
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


async def transform_sessions(
        sessions: list[dict]
) -> list[ChatRoomSessionShow]:
    result_sessions = []
    for session in sessions:
        user = await db.get_db().users.find_one({
            '_id': session['user_id']
        })
        chat_room = await db.get_db().chat_rooms.find_one({
            '_id': session['chat_room_id']
        })
        if user:
            owner = UserUpdate(**user)
        else:
            owner = None
        if chat_room:
            room = ChatRoomCreate(**chat_room)
        else:
            room = None
        result_sessions.append(
            ChatRoomSessionShow(
                id=str(session['_id']),
                **{k: v for k, v in session.items() if k not in (
                    '_id', 'id'
                )},
                user=owner,
                chat_room=room
            )
        )

    return result_sessions


async def get_all_join_requests() -> list[JoinRequestShow]:
    join_requests = await db.get_db().join_requests.find().to_list(None)
    tr_join_requests = await transform_join_requests(join_requests)

    return tr_join_requests


async def get_all_chat_room_sessions() -> list[ChatRoomSessionShow]:
    sessions = await db.get_db().chat_room_sessions.find().to_list(None)
    tr_sessions = await transform_sessions(sessions)

    return tr_sessions


async def delete_join_request(join_request_id: str) -> bool:
    result = await db.get_db().join_requests.delete_one({
        '_id': ObjectId(join_request_id)
    })

    return result.deleted_count > 0


async def delete_chat_room_session(chat_room_session_id: str) -> bool:
    result = await db.get_db().chat_room_sessions.delete_one({
        '_id': ObjectId(chat_room_session_id)
    })

    return result.deleted_count > 0


async def get_join_requests_by_chat_room_id(
        chat_room_id: str
) -> list[JoinRequestShow]:
    join_requests = await db.get_db().join_requests.find({
        'chat_room_id': ObjectId(chat_room_id)
    }).to_list(None)
    tr_join_requests = await transform_join_requests(join_requests)

    return tr_join_requests


async def get_join_requests_by_user_id(
        user_id: str
) -> list[JoinRequestShow]:
    join_requests = await db.get_db().join_requests.find({
        'user_id': ObjectId(user_id)
    }).to_list(None)
    tr_join_requests = await transform_join_requests(join_requests)

    return tr_join_requests


async def get_chat_room_details(chat_room_id: str) -> dict:
    chat_room = await db.get_db().chat_rooms.find_one({
        '_id': ObjectId(chat_room_id)
    })
    chat_room['_id'] = str(chat_room['_id'])
    chat_room['owner'] = str(chat_room['owner'])
    join_requests = await get_join_requests_by_chat_room_id(chat_room_id)

    return {
        'chat_room_details': ChatRoomModel(**chat_room),
        'chat_room_join_requests': join_requests
    }


async def get_join_request(join_request_id: str) -> JoinRequestShow:
    join_request = await db.get_db().join_requests.find_one({
        '_id': ObjectId(join_request_id)
    })
    join_request['_id'] = str(join_request['_id'])

    user = await db.get_db().users.find_one({
        '_id': ObjectId(join_request['user_id'])
    })
    chat_room = await db.get_db().chat_rooms.find_one({
        '_id': ObjectId(join_request['chat_room_id'])
    })
    if user:
        join_request['user'] = UserUpdate(**user)
    else:
        join_request['user'] = None
    if chat_room:
        join_request['chat_room'] = ChatRoomCreate(**chat_room)
    else:
        join_request['chat_room'] = None
    
    return JoinRequestShow(**join_request)


async def handle_request(
        join_request_id: str, approval_status: bool
) -> dict:
    result = await db.get_db().join_requests.update_one(
        {'_id': ObjectId(join_request_id)},
        {'$set': {'approved': approval_status}}
    )

    if result.modified_count == 1:
        statuss = "Join request approved successfully."
    else:
        statuss = "Join request not found or update failed."

    if approval_status:
        join_request = await db.get_db().join_requests.find_one({
            '_id': ObjectId(join_request_id)
        })
        user = await db.get_db().users.find_one({
            '_id': join_request['user_id']
        })
        chat_room = await db.get_db().chat_rooms.find_one({
            '_id': join_request['chat_room_id']
        })
        session = await create_session(
            str(user['_id']), str(chat_room['_id'])
        )
    else:
        session = "No session made"
        statuss = "Join request disapproved successfully."

    return {"status": statuss, "session": session}


async def create_message(
        user_id: str, chat_room_id: str, username: str,
        content: str, message_type: MessageType,
        file_name: str = None, file_path: str = None
):
    message_doc = {
        "user_id": user_id,
        "chat_room_id": chat_room_id,
        "username": username,
        "content": content,
        "timestamp": datetime.now(),
        "message_type": message_type,
        "file_name": file_name,
        "file_path": file_path
    }
    result = await db.get_db().messages.insert_one(message_doc)
    message_doc["id"] = str(result.inserted_id)

    return MessageModel(**message_doc)


async def get_recent_messages(
    chat_room_id: str, limit: int = 50, before_id: str = None
):
    query = {'chat_room_id': chat_room_id}
    if before_id:
        query["_id"] = {"$lt": ObjectId(before_id)}
    
    messages = await db.get_db().messages.find(query).sort(
        "_id", -1
    ).limit(limit).to_list(None)

    return [
        MessageModel(
            id=str(msg["_id"]),
            user_id=msg["user_id"],
            chat_room_id=msg["chat_room_id"],
            username=msg["username"],
            content=msg["content"],
            timestamp=msg["timestamp"],
            message_type=msg["message_type"],
            file_name=msg["file_name"],
            file_path=msg["file_path"]
        ) for msg in messages
    ][::-1]


async def get_messages(skip: int = 0, limit: int = 100):
    msgs = await db.get_db().messages.find().skip(skip)\
                .limit(limit).to_list(None)

    return [
        MessageModel(
            id=str(msg["_id"]),
            user_id=msg["user_id"],
            chat_room_id=msg["chat_room_id"],
            username=msg["username"],
            content=msg["content"],
            timestamp=msg["timestamp"],
            message_type=msg["message_type"],
            file_name=msg["file_name"],
            file_path=msg["file_path"]
        ) for msg in msgs
    ]


async def delete_all_messages():
    result = await db.get_db().messages.delete_many({})

    return result.deleted_count


async def transform_chat_room_session_to_chat_room(
        chat_room_session: ChatRoomSessionModel,
        is_group: bool
) -> ChatRoomShow | None:
    chat_room = await db.get_db().chat_rooms.find_one({
        "_id": ObjectId(chat_room_session.chat_room_id),
        "is_group": is_group
    })
    if not chat_room:

        return None

    chat_room_owner = await db.get_db().users.find_one({
        "_id": ObjectId(chat_room['owner'])
    })
    owner_data = UserUpdate(
        **chat_room_owner
    ) if chat_room_owner else None

    return ChatRoomShow(
        id=str(chat_room['_id']),
        name=chat_room['name'],
        created_at=chat_room['created_at'],
        is_group=is_group,
        last_activity=chat_room.get('last_activity'),
        owner=owner_data
    )


async def retrieve_users_chat_rooms(
        user_id: str, is_group: bool
) -> list[ChatRoomShow]:
    chat_room_sessions = await db.get_db().chat_room_sessions.find({
        "user_id": ObjectId(user_id)
    }).to_list(None)
    if not chat_room_sessions:
        
        return []

    chat_rooms = []
    for session in chat_room_sessions:
        session["_id"] = str(session["_id"])
        session["user_id"] = user_id
        session["chat_room_id"] = str(session["chat_room_id"])
        chat_room_session = ChatRoomSessionModel(**session)
        chat_room = await transform_chat_room_session_to_chat_room(
            chat_room_session,
            is_group
        )
        if chat_room:
            chat_rooms.append(chat_room)
    
    chat_rooms_sorted = sorted(
        chat_rooms,
        key=lambda room: room.last_activity or datetime.min,
        reverse=True
    )

    return chat_rooms_sorted


async def update_user_online_status_db(user_id: str, is_online: bool):
    result = await db.get_db().users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_online": is_online}}
    )
    if result.modified_count == 0:
        message = "User not found or has been "
        message += "updated with the same status before"
        raise HTTPException(
            status_code=404,
            detail=message
        )
    
    return await db.get_db().users.find_one({"_id": ObjectId(user_id)})


async def update_chat_room_session_last_seen(user_id, chat_room_id):
    await db.get_db().chat_room_sessions.update_one(
        {
            "user_id": ObjectId(user_id),
            "chat_room_id": ObjectId(chat_room_id)
        },
        {"$set": {"last_seen": datetime.now()}}
    )


async def update_chat_room_last_activity(chat_room_id, timestamp):
    await db.get_db().chat_rooms.update_one(
        {"_id": ObjectId(chat_room_id)},
        {"$set": {"last_activity": timestamp}}
    )


async def create_pv_chat(
    requester_user_id: str, addressed_user_id: str
) -> dict:
    requester = await db.get_db().users.find_one({
        "_id": ObjectId(requester_user_id)
    })
    addressed = await db.get_db().users.find_one({
        "_id": ObjectId(addressed_user_id)
    })
    rooms_name = f"{requester['username']} - {addressed['username']} PV Chat"
    pv_chat_room = await create_chat_room(
        ChatRoomUpdate(name=rooms_name),
        requester_user_id,
        False
    )
    chat_room_dict = pv_chat_room['chat_room'].model_dump()
    addressed_session = await create_session(
        addressed_user_id, chat_room_dict['id']
    )

    return {
        "chat_room": chat_room_dict,
        "requesters_session": pv_chat_room['session'],
        "addresseds_session": addressed_session
    }


async def get_online_users_pv(user_id: str) -> list:
    chat_room_sessions = await db.get_db().chat_room_sessions.find({
        "user_id": ObjectId(user_id)
    }).to_list(None)
    if not chat_room_sessions:
        
        return []

    usernames = []
    for session in chat_room_sessions:
        session["_id"] = str(session["_id"])
        session["user_id"] = user_id
        chat_room_id = session["chat_room_id"]
        session["chat_room_id"] = str(chat_room_id)
        chat_room_session = ChatRoomSessionModel(**session)
        chat_room = await transform_chat_room_session_to_chat_room(
            chat_room_session, False
        )
        if chat_room:
            other_session = await db.get_db().chat_room_sessions.find_one({
                "chat_room_id": chat_room_id,
                "user_id": {"$ne": ObjectId(user_id)}
            })
            other_user = await db.get_db().users.find_one({
                "_id": other_session["user_id"],
                "is_online": True
            })
            if other_user:
                usernames.append(other_user["username"])

    return usernames


async def rooms_online_users(user_id: str, chat_room_id: str) -> list:
    chat_rooms_sessions = await db.get_db().chat_room_sessions.find({
        "chat_room_id": ObjectId(chat_room_id)
    }).to_list(None)

    usernames = []
    for session in chat_rooms_sessions:
        users_id = session["user_id"]
        if user_id != str(users_id):
            user = await db.get_db().users.find_one({
                "_id": users_id,
                "is_online": True
            })
            if user:
                usernames.append(user["username"])

    return usernames
