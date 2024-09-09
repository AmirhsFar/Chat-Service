import logging
from datetime import timedelta
from jose import (
    JWTError,
    jwt
)
from fastapi import (
    APIRouter,
    HTTPException,
    status,
    Depends
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
    ChatRoomCreate,
    ChatRoomModel
)
from operations import (
    create_user,
    get_user_by_email,
    get_user_by_username,
    create_chat_room,
    get_user_chat_rooms
)
from utils import (
    get_password_hash,
    verify_password,
    create_access_token,
    SECRET_KEY,
    ALGORITHM
)
# from redis_config import get_redis

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
    
    # redis = await get_redis()
    # is_blacklisted = await redis.get(f"blacklisted_token:{token}")
    # if is_blacklisted:
    #     raise credentials_exception
    
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
        
        hashed_password = get_password_hash(user.password)
        user_dict = user.model_dump()
        user_dict["password"] = hashed_password
        new_user = await create_user(UserCreate(**user_dict))
        logger.info(f"New user created: {new_user.email}")

        return new_user
    except ValueError as e:
        logger.error(f"Error during signup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e
    # except Exception as e:
    #     logger.error(f"Unexpected error during signup: {str(e)}")
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail="An unexpected error occurred"
    #     ) from e

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await get_user_by_email(form_data.username) or await get_user_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"email": user.email, "username": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

# @router.post("/logout")
# async def logout(current_user: UserModel = Depends(get_current_user), token: str = Depends(oauth2_scheme)):
#     redis = await get_redis()
#     await redis.set(f"blacklisted_token:{token}", "true", ex=ACCESS_TOKEN_EXPIRE_MINUTES * 60)
#     logger.info(f"User logged out: {current_user.email}")

#     return {"message": "Successfully logged out"}

@router.post("/chat_rooms", response_model=ChatRoomModel)
async def create_new_chat_room(chat_room: ChatRoomCreate, current_user: UserModel = Depends(get_current_user)):
    try:
        new_chat_room = await create_chat_room(chat_room, current_user.id)
        logger.info(f"New chat room created: {new_chat_room.name} by user: {current_user.email}")

        return new_chat_room
    except Exception as e:
        logger.error(f"Error creating chat room: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the chat room"
        ) from e

@router.get("/chat_rooms", response_model=list[ChatRoomModel])
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
