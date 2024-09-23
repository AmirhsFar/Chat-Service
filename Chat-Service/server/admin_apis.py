from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)
from schemas import (
    UserModel,
    UserCreate,
    UserShow,
    UserUpdate,
    ChatRoomShow,
    ChatRoomUpdate,
    JoinRequestShow,
    ChatRoomSessionShow,
    MessageModel
)
from operations import (
    get_user_by_username, get_user_by_email,
    get_all_users, get_user,
    create_user, update_user,
    delete_user, get_all_chat_rooms,
    get_chat_room, create_chat_room,
    update_chat_room, delete_chat_room,
    get_all_join_requests, get_all_chat_room_sessions,
    delete_join_request, delete_chat_room_session,
    get_messages, delete_all_messages
)
from inits_apis import get_current_user
from bson import ObjectId

router = APIRouter()


async def get_current_admin_user(
        current_user: UserModel = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can access this resource"
        )
    
    return current_user


@router.get("/users", response_model=list[UserShow])
async def admin_get_all_users(
    _: UserModel = Depends(get_current_admin_user)
):
    return await get_all_users()


@router.get("/users/{user_id}", response_model=UserShow)
async def admin_get_user(
    user_id: str, _: UserModel = Depends(get_current_admin_user)
):
    try:
        ObjectId(user_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        ) from exc
    
    user = await get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.post(
        "/users", response_model=UserShow,
        status_code=status.HTTP_201_CREATED
)
async def admin_create_user(
    user: UserCreate, _: UserModel = Depends(get_current_admin_user)
):
    existing_user = await get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    existing_user = await get_user_by_username(user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this username already exists"
        )
    
    return await create_user(user)


@router.patch("/users/{user_id}", response_model=UserShow)
async def admin_update_user(
    user_id: str,
    user_update: UserUpdate,
    _: UserModel = Depends(get_current_admin_user)
):
    try:
        ObjectId(user_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        ) from exc
    
    updated_user = await update_user(
        user_id, user_update.model_dump(exclude_unset=True)
    )

    return updated_user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_user(
    user_id: str, _: UserModel = Depends(get_current_admin_user)
):
    try:
        ObjectId(user_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        ) from exc

    deleted = await delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")


@router.get("/chat-rooms", response_model=list[ChatRoomShow])
async def admin_get_all_chat_rooms(
    _: UserModel = Depends(get_current_admin_user)
):
    return await get_all_chat_rooms()


@router.get("/chat-rooms/{chat_room_id}", response_model=ChatRoomShow)
async def admin_get_chat_room(
    chat_room_id: str, _: UserModel = Depends(get_current_admin_user)
):
    try:
        ObjectId(chat_room_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid chat room ID"
        ) from exc

    chat_room = await get_chat_room(chat_room_id, is_group=True)
    if not chat_room:
        raise HTTPException(
            status_code=404, detail="Chat room not found"
        )
    
    return chat_room


@router.get(
        "/chat-rooms/private/{private_chat_id}",
        response_model=ChatRoomShow
)
async def admin_get_private_chat(
    private_chat_id: str, _: UserModel = Depends(get_current_admin_user)
):
    try:
        ObjectId(private_chat_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid private chat room ID"
        ) from exc

    pv_chat = await get_chat_room(private_chat_id, is_group=False)
    if not pv_chat:
        raise HTTPException(
            status_code=404, detail="Private chat not found"
        )
    
    return pv_chat


@router.post(
        "/chat-rooms",
        status_code=status.HTTP_201_CREATED
)
async def admin_create_chat_room(
    chat_room: ChatRoomUpdate,
    is_group: bool,
    current_user: UserModel = Depends(get_current_admin_user)
):
    if is_group not in (True, False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid is_group status"
        )

    return await create_chat_room(chat_room, current_user.id, is_group)


@router.patch("/chat-rooms/{chat_room_id}", response_model=ChatRoomShow)
async def admin_update_chat_room(
    chat_room_id: str,
    chat_room_update: ChatRoomUpdate,
    _: UserModel = Depends(get_current_admin_user)
):
    try:
        ObjectId(chat_room_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid chat room ID"
        ) from exc

    updated_chat_room = await update_chat_room(
        chat_room_id,
        chat_room_update.model_dump(exclude_unset=True)
    )

    return updated_chat_room


@router.delete(
        "/chat-rooms/{chat_room_id}",
        status_code=status.HTTP_204_NO_CONTENT
)
async def admin_delete_chat_room(
    chat_room_id: str, _: UserModel = Depends(get_current_admin_user)
):
    try:
        ObjectId(chat_room_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid chat room ID"
        ) from exc

    deleted = await delete_chat_room(chat_room_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat room not found")


@router.get("/join-requests", response_model=list[JoinRequestShow])
async def admin_get_all_join_requests(
    _: UserModel = Depends(get_current_admin_user)
):
    return await get_all_join_requests()


@router.get("/chat-room-sessions", response_model=list[ChatRoomSessionShow])
async def admin_get_all_chat_room_sessions(
    _: UserModel = Depends(get_current_admin_user)
):
    return await get_all_chat_room_sessions()


@router.delete(
        "/chat-room-sessions/{chat_room_session_id}",
        status_code=status.HTTP_204_NO_CONTENT
)
async def admin_delete_chat_room_session(
    chat_room_session_id: str,
    _: UserModel = Depends(get_current_admin_user)
):
    try:
        ObjectId(chat_room_session_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid chat room session ID"
        ) from exc

    deleted = await delete_chat_room_session(chat_room_session_id)
    if not deleted:
        raise HTTPException(
            status_code=404, detail="Chat room session not found"
        )


@router.delete(
        "/join-requests/{join_request_id}",
        status_code=status.HTTP_204_NO_CONTENT
)
async def admin_delete_join_request(
    join_request_id: str, _: UserModel = Depends(get_current_admin_user)
):
    try:
        ObjectId(join_request_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid join request ID"
        ) from exc
    
    deleted = await delete_join_request(join_request_id)
    if not deleted:
        raise HTTPException(
            status_code=404, detail="Join request not found"
        )


@router.get('/messages', response_model=list[MessageModel])
async def read_messages(
    skip: int = 0, limit: int = 100,
    _: UserModel = Depends(get_current_user)
):
    messages = await get_messages(skip=skip, limit=limit)

    return messages


@router.delete("/clear_messages")
async def clear_messages(_: UserModel = Depends(get_current_user)):
    deleted_count = await delete_all_messages()
    if deleted_count > 0:

        return {"message": f"Deleted {deleted_count} messages"}
    else:
        raise HTTPException(status_code=404, detail="No messages found")
