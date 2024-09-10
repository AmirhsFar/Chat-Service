from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)
from schemas import (
    UserModel,
    UserCreate,
    ChatRoomCreate,
    UserShow,
    UserUpdate,
    ChatRoomShow,
    ChatRoomUpdate,
    JoinRequestShow
)
from operations import (
    get_user_by_username, get_user_by_email,
    get_all_users, get_user,
    create_user, update_user,
    delete_user, get_all_chat_rooms,
    get_chat_room, create_chat_room,
    update_chat_room, delete_chat_room,
    get_all_join_requests
)
from inits_apis import get_current_user

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
    user = await get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
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
        updated_user = await update_user(
            user_id, user_update.model_dump(exclude_unset=True)
        )

        return updated_user
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_user(
    user_id: str, _: UserModel = Depends(get_current_admin_user)
    ):
    try:
        deleted = await delete_user(user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="User not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

@router.get("/chat-rooms", response_model=list[ChatRoomShow])
async def admin_get_all_chat_rooms(
    _: UserModel = Depends(get_current_admin_user)
):
    return await get_all_chat_rooms()

@router.get("/chat-rooms/{chat_room_id}", response_model=ChatRoomShow)
async def admin_get_chat_room(
    chat_room_id: str, _: UserModel = Depends(get_current_admin_user)
):
    chat_room = await get_chat_room(chat_room_id, is_group=True)
    if not chat_room:
        raise HTTPException(status_code=404, detail="Chat room not found")
    
    return chat_room

@router.get(
        "/chat-rooms/private/{private_chat_id}",
        response_model=ChatRoomShow
)
async def admin_get_private_chat(
    private_chat_id: str, _: UserModel = Depends(get_current_admin_user)
):
    pv_chat = await get_chat_room(private_chat_id, is_group=False)
    if not pv_chat:
        raise HTTPException(
            status_code=404, detail="Private chat not found"
        )
    
    return pv_chat

@router.post(
        "/chat-rooms",
        response_model=ChatRoomShow,
        status_code=status.HTTP_201_CREATED
)
async def admin_create_chat_room(
    chat_room: ChatRoomCreate,
    current_user: UserModel = Depends(get_current_admin_user)
):
    return await create_chat_room(chat_room, current_user.id)

@router.patch("/chat-rooms/{chat_room_id}", response_model=ChatRoomShow)
async def admin_update_chat_room(
    chat_room_id: str,
    chat_room_update: ChatRoomUpdate,
    _: UserModel = Depends(get_current_admin_user)
):
    try:
        updated_chat_room = await update_chat_room(
            chat_room_id,
            chat_room_update.model_dump(exclude_unset=True)
        )

        return updated_chat_room
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

@router.delete(
        "/chat-rooms/{chat_room_id}",
        status_code=status.HTTP_204_NO_CONTENT
)
async def admin_delete_chat_room(
    chat_room_id: str, _: UserModel = Depends(get_current_admin_user)
):
    deleted = await delete_chat_room(chat_room_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat room not found")

@router.get("/join-requests", response_model=list[JoinRequestShow])
async def admin_get_all_join_requests(
    _: UserModel = Depends(get_current_admin_user)
):
    return await get_all_join_requests()
