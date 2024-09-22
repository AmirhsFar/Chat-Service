import logging
from datetime import timedelta
from database import db
from bson import ObjectId
from jose import (
    JWTError,
    jwt
)
from fastapi import (
    APIRouter,
    HTTPException,
    status,
    Depends,
    Body
)
from fastapi.security import (
    OAuth2PasswordRequestForm,
    OAuth2PasswordBearer
)
from schemas import (
    UserCreate,
    UserModel,
    TokenData,
    Token,
    ChatRoomUpdate,
    ChatRoomShow,
    JoinRequestCreate,
    JoinRequestShow
)
from operations import (
    create_user,
    get_user_by_email,
    get_user_by_username,
    create_chat_room,
    get_user_chat_rooms,
    get_chat_room,
    create_join_request,
    get_chat_room_details,
    delete_chat_room,
    get_join_request,
    handle_request,
    retrieve_users_chat_rooms,
    update_user_online_status_db,
    create_pv_chat,
    rooms_online_users,
    get_online_users_pv
)
from utils import (
    verify_password,
    create_access_token,
    SECRET_KEY,
    ALGORITHM
)

router = APIRouter()
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

ACCESS_TOKEN_EXPIRE_MINUTES = 30


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("email")
        username: str = payload.get("username")
        if email is None or username is None:
            raise credentials_exception
        token_data = TokenData(email=email, username=username)
    except JWTError as exc:
        raise credentials_exception from exc
    user = await get_user_by_email(email=token_data.email)
    if user is None:
        raise credentials_exception
    
    return user


@router.post(
        "/signup",
        response_model=UserModel,
        status_code=status.HTTP_201_CREATED
)
async def signup(user: UserCreate):
    try:
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
        
        user_dict = user.model_dump()
        new_user = await create_user(UserCreate(**user_dict))
        logger.info(f"New user created: {new_user.email}")

        return new_user
    except ValueError as e:
        logger.error(f"Error during signup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = await get_user_by_email(form_data.username) or await get_user_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"email": user.email, "username": user.username},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/refresh-token", response_model=Token)
async def refresh_access_token(
    current_user: UserModel = Depends(get_current_user)
):
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "email": current_user.email,
            "username": current_user.username
        },
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/chat-rooms")
async def create_new_chat_room(
    chat_room: ChatRoomUpdate,
    current_user: UserModel = Depends(get_current_user)
):
    try:
        new_chat_room = await create_chat_room(chat_room, current_user.id, True)
        chat_room_dict = chat_room.model_dump()
        logger.info(
            f"New chat room created: {chat_room_dict['name']} by user: {current_user.email}"
        )

        return new_chat_room
    except Exception as e:
        logger.error(f"Error creating chat room: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the chat room"
        ) from e


@router.get("/chat-rooms", response_model=list[ChatRoomShow])
async def get_my_chat_rooms(current_user: UserModel = Depends(get_current_user)):
    try:
        chat_rooms = await get_user_chat_rooms(current_user.id)

        return chat_rooms
    except Exception as e:
        logger.error(f"Error fetching chat rooms: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching chat rooms"
        ) from e


@router.get(
        "/search-chat-rooms",
        response_model=ChatRoomShow
)
async def search_chat_rooms(
    chat_room_id: str, _: UserModel = Depends(get_current_user)
):
    chat_room = await get_chat_room(chat_room_id, is_group=True)
    if not chat_room:
        raise HTTPException(
            status_code=404, detail="Chat room not found"
        )
    
    return chat_room


@router.post("/join-request", response_model=JoinRequestShow)
async def submit_join_request(
    join_request: JoinRequestCreate,
    current_user: UserModel = Depends(get_current_user)
):
    new_join_request = await create_join_request(
        join_request, current_user.id
    )
    logger.info(
        f"New join request submitted by user: {current_user.email}"
    )

    return new_join_request


@router.get('/chat-room-details')
async def my_chat_room_details(
    chat_room_id: str, current_user: UserModel = Depends(get_current_user)
):
    chat_room = await db.get_db().chat_rooms.find_one({
        '_id': ObjectId(chat_room_id), 'owner': ObjectId(current_user.id)
    })
    if not chat_room:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not allowed to see other users' chat rooms"
        )
    
    return await get_chat_room_details(chat_room_id)


@router.delete('/delete-chat-room', status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_chat_room(
    chat_room_id: str, current_user: UserModel = Depends(get_current_user)
):
    my_chat_room = await db.get_db().chat_rooms.find_one({
        '_id': ObjectId(chat_room_id), 'owner': ObjectId(current_user.id)
    })
    chat_room = await db.get_db().chat_rooms.find_one({
        '_id': ObjectId(chat_room_id)
    })
    if not my_chat_room and chat_room:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not allowed to delete other users' chat rooms"
        )

    deleted = await delete_chat_room(chat_room_id)
    if not deleted:
        raise HTTPException(
            status_code=404, detail="Chat room not found"
        )


@router.get('/join-request-details', response_model=JoinRequestShow)
async def get_join_request_details(
    join_request_id: str,
    current_user: UserModel = Depends(get_current_user)
):
    try:
        join_request = await db.get_db().join_requests.find_one({
            '_id': ObjectId(join_request_id)
        })
        requested_chat_room = await db.get_db().chat_rooms.find_one({
            '_id': join_request['chat_room_id']
        })
        requested_chat_room_owner = await db.get_db().users.find_one({
            '_id': requested_chat_room['owner']
        })
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Join request not found'
        ) from e
    
    if current_user.id != str(requested_chat_room_owner['_id']):
        message = "You are not allowed to access "
        message += "the request details of other users' chat rooms"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message
        )

    return await get_join_request(join_request_id)


@router.post('/handle-join-request')
async def handle_join_request(
    join_request_id: str = Body(...), approval_status: bool = Body(...),
    current_user: UserModel = Depends(get_current_user)
):
    try:
        join_request = await db.get_db().join_requests.find_one({
            '_id': ObjectId(join_request_id)
        })
        requested_chat_room = await db.get_db().chat_rooms.find_one({
            '_id': join_request['chat_room_id']
        })
        requested_chat_room_owner = await db.get_db().users.find_one({
            '_id': requested_chat_room['owner']
        })
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Join request not found'
        ) from e
    
    if current_user.id != str(requested_chat_room_owner['_id']):
        message = "You are not allowed to approve the join requests "
        message += "submitted for other users' chat rooms"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message
        )
    
    if join_request['approved'] is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This join request is handled already"
        )

    return await handle_request(join_request_id, approval_status)


@router.get('/users/me', response_model=UserModel)
async def read_users_me(
    current_user: UserModel = Depends(get_current_user)
):
    return current_user


@router.post("/user/submitted-chat-rooms", response_model=list[ChatRoomShow])
async def get_users_submitted_chat_rooms(
    current_user: UserModel = Depends(get_current_user),
    request: dict = Body(...)
):
    is_group = request.get('is_group')
    chat_rooms = await retrieve_users_chat_rooms(current_user.id, is_group)

    return chat_rooms


@router.put("/user/online-status")
async def update_user_online_status(
    is_online: bool = Body(...),
    current_user: UserModel = Depends(get_current_user)
):
    await update_user_online_status_db(current_user.id, is_online)
    
    return {"message": "User online status updated successfully"}


@router.post("/pv-chat-room")
async def create_pv_chat_room(
    request: dict = Body(...),
    current_user: UserModel = Depends(get_current_user)
):
    addressed_users_id = request.get("addressed_users_id")
    new_chat_room = await create_pv_chat(
        current_user.id, addressed_users_id
    )
    logger.info(
        f"New pv chat created by: {current_user.email}"
    )

    return new_chat_room


@router.get("/chat-room/{chat_room_id}", response_model=ChatRoomShow)
async def chat_room_details(
    chat_room_id: str,
    _: UserModel = Depends(get_current_user)
):
    chat_room = await get_chat_room(chat_room_id)
    if not chat_room:
        raise HTTPException(
            status_code=404, detail="Chat room not found"
        )
    
    return chat_room


@router.get("/rooms-online-users")
async def get_rooms_online_users(
    chat_room_id: str,
    current_user: UserModel = Depends(get_current_user)
):
    return await rooms_online_users(current_user.id, chat_room_id)


@router.get("/pv-online-users")
async def get_pv_chats_online_users(
    current_user: UserModel = Depends(get_current_user)
):
    return await get_online_users_pv(current_user.id)
