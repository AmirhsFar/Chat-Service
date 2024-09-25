"""
operations.py

This module contains utility functions for handling users, chat rooms, 
sessions, and other operations within the FastAPI project. It interacts 
with MongoDB using the Motor library and provides a variety of 
functionalities, including user creation, chat room management, 
and session handling.
"""

from datetime import datetime
from bson import ObjectId
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
    """
    Creates a new user in the database.

    This function hashes the user's password, assigns admin privileges 
    if no other admin exists, and inserts the user into the database.

    Args:
        user (UserCreate): The user data to be inserted, including email, 
            username, and password.

    Returns:
        UserModel: The newly created user.
    """
    user_dict = user.model_dump()
    user_dict["is_online"] = False
    admin_count = await db.get_db().users.count_documents({
        "is_admin": True
    })
    user_dict["is_admin"] = admin_count == 0
    user_dict["password"] = get_password_hash(user_dict["password"])
    result = await db.get_db().users.insert_one(user_dict)
    user_dict["_id"] = str(result.inserted_id)

    return UserModel(**user_dict)


async def get_user_by_email(email: str) -> UserModel | None:
    """
    Retrieves a user from the database by email.

    Args:
        email (str): The email of the user to retrieve.

    Returns:
        UserModel | None: The user matching the email if found, 
            or None if not found.
    """
    user = await db.get_db().users.find_one({"email": email})
    if user:
        user_in_db = UserInDB(**user)

        return UserModel(
            id=str(user_in_db.id), **user_in_db.model_dump(exclude={'id'})
        )
    
    return None


async def get_user_by_username(username: str) -> UserModel | None:
    """
    Retrieves a user from the database by username.

    Args:
        username (str): The username of the user to retrieve.

    Returns:
        UserModel | None: The user matching the username if found, 
            or None if not found.
    """
    user = await db.get_db().users.find_one({"username": username})
    if user:
        user_in_db = UserInDB(**user)

        return UserModel(
            id=str(user_in_db.id), **user_in_db.model_dump(exclude={'id'})
        )
    
    return None


async def get_user(user_id: str) -> UserShow | None:
    """
    Retrieves a user from the database by their unique user ID.

    Args:
        user_id (str): The unique identifier (ObjectId) of the user.

    Returns:
        UserShow | None: A UserShow instance if the user is found, 
            or None if not found.
    """
    user = await db.get_db().users.find_one({'_id': ObjectId(user_id)})
    if user:

        return UserShow(
            id=str(user['_id']),
            **{k: v for k, v in user.items() if k not in ('_id', 'id')}
        )
    
    return None


async def create_session(user_id: str, chat_room_id: str):
    """
    Creates a new session for a user in a chat room.

    Args:
        user_id (str): The unique identifier of the user.
        chat_room_id (str): The unique identifier of the chat room.

    Returns:
        ChatRoomSessionModel: The newly created session for the user.
    """
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
    """
    Creates a new chat room in the database.

    Args:
        chat_room (ChatRoomCreate): The data for the new chat room, 
            including its name and group status.

    Returns:
        ChatRoomModel: The newly created chat room.
    """
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
    """
    Retrieves all chat rooms a user is part of.

    Args:
        user_id (str): The unique identifier of the user.

    Returns:
        list[ChatRoomShow]: A list of chat rooms the user is part of.
    """
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
    """
    Retrieves all users from the database.

    Returns:
        list[UserShow]: A list of all users in the database.
    """
    users = await db.get_db().users.find().to_list(None)

    return [UserShow(
        id=str(user['_id']),
        **{k: v for k, v in user.items() if k not in ('_id', 'id')}
                                ) for user in users]


async def update_user(user_id: str, update_data: UserUpdate) -> UserShow:
    """
    Updates the user's information in the database.

    This function checks if the new username or email already exists 
    in the database for another user before applying the updates. 
    It then updates the user's information in the database and returns 
    the updated user.

    Args:
        user_id (str): The unique identifier of the user to update.
        update_data (UserUpdate): The fields to update for the user 
            (e.g., username, email).

    Returns:
        UserShow: The updated user information.

    Raises:
        ValueError: If the username or email already exists, or if 
            no changes were made.
    """
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
    """
    Deletes a user from the database along with their associated 
    chat rooms and sessions.

    Admin users cannot be deleted. This function also deletes 
    the user's associated chat rooms, session data, join requests, 
    and messages.

    Args:
        user_id (str): The unique identifier of the user to delete.

    Returns:
        bool: True if the user was deleted, False otherwise.

    Raises:
        ValueError: If the user is an admin and cannot be deleted.
    """
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
    """
    Transforms a list of database chat room instances into a list of 
    ChatRoomShow instances.

    This function takes a list of raw chat room dictionaries 
    from the database, retrieves the owner of each room, and returns 
    a list of ChatRoomShow models with the necessary fields 
    populated for display.

    Args:
        chat_rooms (list[dict]): A list of chat room dictionaries 
            from the database.

    Returns:
        list[ChatRoomShow]: A list of transformed ChatRoomShow instances.
    """
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
    """
    Retrieves all chat rooms from the database.

    This function fetches all chat rooms from the database, transforms 
    them into ChatRoomShow models, and returns them.

    Returns:
        list[ChatRoomShow]: A list of all chat rooms in the database.
    """
    chat_rooms = await db.get_db().chat_rooms.find().to_list(None)
    tr_chat_rooms = await transform_chat_rooms(chat_rooms)

    return tr_chat_rooms


async def get_chat_room(
        chat_room_id: str, is_group: bool | None = None
) -> ChatRoomShow | None:
    """
    Retrieves a single chat room from the database by its ID.

    Args:
        chat_room_id (str): The unique identifier of the chat room.

    Returns:
        ChatRoomShow | None: The chat room if found, or None if not found.
    """
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
    """
    Updates a chat room's information in the database.

    Args:
        chat_room_id (str): The unique identifier of the chat room to update.
        update_data (ChatRoomUpdate): The fields to update for the chat room.

    Returns:
        ChatRoomShow: The updated chat room information.

    Raises:
        ValueError: If no changes were made or the chat room was not found.
    """
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
    """
    Deletes a chat room from the database by its ID.

    This function deletes the chat room's associated 
    session data, join requests, and messages alongside 
    the chat room itself.

    Args:
        chat_room_id (str): The unique identifier of the 
            chat room to delete.

    Returns:
        bool: True if the chat room was deleted, False otherwise.
    """
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
    """
    Creates a new join request for a user to join a specific chat room.

    This function handles the logic for creating a request for a user to 
    join a chat room. It first validates the provided chat room ID and 
    user ID, ensures that the user is not requesting to join their own 
    chat room, and checks for existing requests from the same user for 
    the same chat room. If all checks pass, the request is inserted 
    into the database.

    Args:
        join_request (JoinRequestCreate): The data for the join request, 
            including a message and the chat room ID.
        user_id (str): The unique identifier of the user submitting the request.

    Returns:
        JoinRequestShow: The newly created join request, including the 
            associated user and chat room details.

    Raises:
        HTTPException: 
            - If the provided chat room ID is invalid.
            - If the provided user ID is invalid.
            - If the user tries to submit a join request to their own 
                chat room.
            - If the user has already submitted a join request 
                to the same chat room.
    """
    join_req_dict = join_request.model_dump()

    try:
        requested_chat_rooms_id = ObjectId(join_req_dict["chat_room_id"])
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid chat room ID"
        ) from exc
    try:
        object_id = ObjectId(user_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
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

    user = await db.get_db().users.find_one({'_id': object_id})
    owner = UserUpdate(**user)
    join_req_dict['user'] = owner

    return JoinRequestShow(**join_req_dict)


async def transform_join_requests(
        join_requests: list[dict]
) -> list[JoinRequestShow]:
    """
    Transforms a list of raw join request dictionaries from the database 
    into a list of JoinRequestShow instances. This includes fetching and 
    associating the related user and chat room for each join request.

    Args:
        join_requests (list[dict]): A list of raw join request dictionaries.

    Returns:
        list[JoinRequestShow]: A list of JoinRequestShow instances with 
            user and chat room data.
    """
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
    """
    Transforms a list of raw session dictionaries from the database into 
    a list of ChatRoomSessionShow instances. This includes fetching and 
    associating the related user and chat room for each session.

    Args:
        sessions (list[dict]): A list of raw session dictionaries.

    Returns:
        list[ChatRoomSessionShow]: A list of ChatRoomSessionShow instances 
            with user and chat room data.
    """
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
    """
    Retrieves all join requests from the database, transforms them into 
    JoinRequestShow instances, and returns them.

    Returns:
        list[JoinRequestShow]: A list of all join requests in the database.
    """
    join_requests = await db.get_db().join_requests.find().to_list(None)
    tr_join_requests = await transform_join_requests(join_requests)

    return tr_join_requests


async def get_all_chat_room_sessions() -> list[ChatRoomSessionShow]:
    """
    Retrieves all chat room sessions from the database, transforms them 
    into ChatRoomSessionShow instances, and returns them.

    Returns:
        list[ChatRoomSessionShow]: A list of all chat room 
            sessions in the database.
    """
    sessions = await db.get_db().chat_room_sessions.find().to_list(None)
    tr_sessions = await transform_sessions(sessions)

    return tr_sessions


async def delete_join_request(join_request_id: str) -> bool:
    """
    Deletes a join request from the database by its ID.

    Args:
        join_request_id (str): The unique identifier of the 
            join request to delete.

    Returns:
        bool: True if the join request was deleted, False otherwise.
    """
    result = await db.get_db().join_requests.delete_one({
        '_id': ObjectId(join_request_id)
    })

    return result.deleted_count > 0


async def delete_chat_room_session(chat_room_session_id: str) -> bool:
    """
    Deletes a chat room session from the database by its ID.

    Args:
        chat_room_session_id (str): The unique identifier of the 
            chat room session to delete.

    Returns:
        bool: True if the chat room session was deleted, False otherwise.
    """
    result = await db.get_db().chat_room_sessions.delete_one({
        '_id': ObjectId(chat_room_session_id)
    })

    return result.deleted_count > 0


async def get_join_requests_by_chat_room_id(
        chat_room_id: str
) -> list[JoinRequestShow]:
    """
    Retrieves all join requests for a specific chat room by its ID, 
    transforms them into JoinRequestShow instances, and returns them.

    Args:
        chat_room_id (str): The unique identifier of the chat room.

    Returns:
        list[JoinRequestShow]: A list of join requests for 
            the specified chat room.
    """
    join_requests = await db.get_db().join_requests.find({
        'chat_room_id': ObjectId(chat_room_id)
    }).to_list(None)
    tr_join_requests = await transform_join_requests(join_requests)

    return tr_join_requests


async def get_join_requests_by_user_id(
        user_id: str
) -> list[JoinRequestShow]:
    """
    Retrieves all join requests submitted by a specific user by 
    their ID, transforms them into JoinRequestShow instances, 
    and returns them.

    Args:
        user_id (str): The unique identifier of the user.

    Returns:
        list[JoinRequestShow]: A list of join requests submitted 
            by the specified user.
    """
    join_requests = await db.get_db().join_requests.find({
        'user_id': ObjectId(user_id)
    }).to_list(None)
    tr_join_requests = await transform_join_requests(join_requests)

    return tr_join_requests


async def get_chat_room_details(chat_room_id: str) -> dict:
    """
    Retrieves detailed information about a specific chat room by its ID.

    This function fetches a chat room by its unique identifier, transforms 
    the chat room into a ChatRoomModel instance, and retrieves any 
    associated join requests for the room.

    Args:
        chat_room_id (str): The unique identifier of the chat room.

    Returns:
        dict: A dictionary containing:
            - 'chat_room_details': The chat room details as a 
                ChatRoomModel instance.
            - 'chat_room_join_requests': A list of join requests 
                for the chat room.
    """
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
    """
    Retrieves a join request by its ID and includes related user and 
    chat room information.

    This function fetches a join request, associates it with the user 
    and chat room details, and returns the join request 
    as a JoinRequestShow instance.

    Args:
        join_request_id (str): The unique identifier of the join request.

    Returns:
        JoinRequestShow: The join request with associated user 
            and chat room details.
    """
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
    """
    Handles the approval or disapproval of a join request.

    If the join request is approved, a session is created for the user 
    in the chat room. Otherwise, the request is marked as disapproved, 
    and no session is created.

    Args:
        join_request_id (str): The unique identifier of the join request.
        approval_status (bool): True to approve the request, 
            False to disapprove.

    Returns:
        dict: A dictionary containing:
            - 'statuss': The approval/disapproval status message.
            - 'session': The session object if approved, or a message 
                indicating no session was created.
    """
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
    """
    Creates a new message in the specified chat room.

    This function inserts a message into the chat room with optional file 
    details and returns the newly created message as a MessageModel instance.

    Args:
        user_id (str): The unique identifier of the user sending the message.
        chat_room_id (str): The unique identifier of the chat room.
        username (str): The username of the user.
        content (str): The content of the message.
        message_type (MessageType): The type of message (text, image, file).
        file_name (str, optional): The name of the file if applicable. 
            Defaults to None.
        file_path (str, optional): The file path if applicable. 
            Defaults to None.

    Returns:
        MessageModel: The newly created message.
    """
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
    """
    Retrieves recent messages from a chat room 
    with an optional limit and pagination.

    This function fetches the most recent messages from the specified 
    chat room and returns them as a list of MessageModel instances. 
    Optionally, messages before a specific message ID can be 
    retrieved for pagination.

    Args:
        chat_room_id (str): The unique identifier of the chat room.
        limit (int, optional): The maximum number of messages 
            to retrieve. Defaults to 50.
        before_id (str, optional): The ID of the message to 
            paginate from. Defaults to None.

    Returns:
        list[MessageModel]: A list of recent messages from 
            the chat room.
    """
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
    """
    Retrieves messages from the database with optional pagination.

    Args:
        skip (int, optional): The number of messages to skip 
            for pagination. Defaults to 0.
        limit (int, optional): The maximum number of messages 
            to retrieve. Defaults to 100.

    Returns:
        list[MessageModel]: A list of messages from the database.
    """
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
    """
    Deletes all messages from the database.

    Returns:
        int: The number of messages that were deleted.
    """
    result = await db.get_db().messages.delete_many({})

    return result.deleted_count


async def transform_chat_room_session_to_chat_room(
        chat_room_session: ChatRoomSessionModel,
        is_group: bool
) -> ChatRoomShow | None:
    """
    Transforms a chat room session model into a ChatRoomShow instance.

    This function fetches the associated chat room and user details, 
    and transforms the session into a ChatRoomShow model 
    if the chat room exists.

    Args:
        chat_room_session (ChatRoomSessionModel): The chat room session 
            to transform.
        is_group (bool): Whether the chat room is a group chat or not.

    Returns:
        ChatRoomShow | None: The transformed ChatRoomShow instance if 
            the chat room exists, or None if not found.
    """
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
    """
    Retrieves all chat rooms that a user is a part of.

    This function fetches all chat room sessions for a given user and 
    transforms them into a list of ChatRoomShow instances, 
    sorted by the chat room's last activity.

    Args:
        user_id (str): The unique identifier of the user.
        is_group (bool): Whether the chat rooms being retrieved 
            are group chats.

    Returns:
        list[ChatRoomShow]: A list of chat rooms the user is part of, 
            sorted by the last activity.
    """
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
    """
    Updates a user's online status in the database.

    This function sets the `is_online` status for the user in the database. 
    If no user is found or the status is the same as the previous one, 
    an HTTPException is raised.

    Args:
        user_id (str): The unique identifier of the user.
        is_online (bool): The user's new online status 
            (True for online, False for offline).

    Returns:
        dict: The updated user document.

    Raises:
        HTTPException: If the user is not found or the status was already 
            set to the same value.
    """
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
    """
    Updates the last seen timestamp for a user in a specific chat room session.

    Args:
        user_id (str): The unique identifier of the user.
        chat_room_id (str): The unique identifier of the chat room.

    Returns:
        None: This function does not return any data.
    """
    await db.get_db().chat_room_sessions.update_one(
        {
            "user_id": ObjectId(user_id),
            "chat_room_id": ObjectId(chat_room_id)
        },
        {"$set": {"last_seen": datetime.now()}}
    )


async def update_chat_room_last_activity(chat_room_id, timestamp):
    """
    Updates the last activity timestamp for a specific chat room.

    Args:
        chat_room_id (str): The unique identifier of the chat room.
        timestamp (datetime): The timestamp to set as the last activity.

    Returns:
        None: This function does not return any data.
    """
    await db.get_db().chat_rooms.update_one(
        {"_id": ObjectId(chat_room_id)},
        {"$set": {"last_activity": timestamp}}
    )


async def create_pv_chat(
    requester_user_id: str, addressed_user_id: str
) -> dict:
    """
    Creates a private (PV) chat between two users.

    This function creates a private chat room for two users 
    (requester and addressed) and initializes chat sessions for both. 
    It returns the chat room details and session information.

    Args:
        requester_user_id (str): The unique identifier of 
            the user who initiated the chat.
        addressed_user_id (str): The unique identifier of 
            the user being invited to the chat.

    Returns:
        dict: A dictionary containing:
            - 'chat_room': The details of the private chat room.
            - 'requesters_session': The chat session for the requester.
            - 'addresseds_session': The chat session for the addressed user.
    """
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
    """
    Retrieves a list of online users with whom the requester user 
    has private chats.

    This function performs the following steps:
    1. Retrieves all chat room sessions for the requester (`user_id`).
    2. Filters for chat rooms that are private.
    3. Retrieves the online users in those private chat rooms, 
        excluding the requester.

    Args:
        user_id (str): The unique identifier of the user making the request.

    Returns:
        list: A list of usernames of online users with whom the requester 
            has private chats.
    """
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
    """
    Retrieves a list of online users in a specific chat room, 
    excluding the requester.

    This function performs the following steps:
    1. Retrieves all chat room sessions for the specified chat room.
    2. For each session, checks if the associated user is online 
        and excludes the requester from the results.
    3. Returns a list of usernames of online users in the chat room.

    Args:
        user_id (str): The unique identifier of the user making the request.
        chat_room_id (str): The unique identifier of the chat room to check.

    Returns:
        list: A list of usernames of online users in the specified 
            chat room, excluding the requester.
    """
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


def load_descriptions(file_path):
    """
    Loads application descriptions from a text file and returns them as a dictionary.

    The text file is expected to contain multiple sections, each starting with a key 
    (such as 'APPS_DESCRIPTION', 'INITS_DESCRIPTION', 'ADMIN_DESCRIPTION') followed 
    by a colon and a space, and then the corresponding description text. Each section 
    is separated by two newlines.

    Args:
        file_path (str): The path to the text file containing the descriptions.

    Returns:
        dict: A dictionary with keys as the description titles (e.g., 'APPS_DESCRIPTION') 
              and values as the corresponding description text.
    """
    descriptions = {}
    with open(file_path, 'r', encoding="utf-8") as f:
        content = f.read().strip()
        sections = content.split('\n\n\n')
        for section in sections:
            try:
                key, value = section.split(': ', 1)
                descriptions[key] = value
            except ValueError as exc:
                print(f"Error parsing section: {section}")
                raise ValueError(
                    "Descriptions file is not formatted correctly."
                ) from exc
    
    return descriptions
