"""
inits_apis.py

This module defines the main FastAPI APIs for user management, 
authentication, and chat room operations within the chat service system. 
It handles a wide range of functionalities, including user sign-up, login, 
managing chat rooms, handling join requests, and more.

### Key Endpoints:

1. **User Management:**
    - **/signup (POST)**: Allows new users to sign up by providing email, 
        username, and password.
    - **/token (POST)**: Logs in a user using their email or username and 
        password, and returns a JWT token.
    - **/refresh-token (POST)**: Refreshes a user's JWT access token.
    - **/user/online-status (PUT)**: Updates the authenticated user's 
        online status (online/offline).
    - **/users/me (GET)**: Retrieves the authenticated user's 
        profile information.

2. **Private Chat Operations:**
    - **/pv-chat-room (POST)**: Creates a private chat room between the 
        authenticated user and another user, returning the chat room details 
        and chat sessions for both users.
    - **/pv-online-users (GET)**: Retrieves the list of online users with 
        whom the authenticated user has private chats (returns a list of usernames).

3. **Group and Chat Room Management:**
    - **/chat-rooms (POST)**: Creates a new chat room for the 
        authenticated user (group chat).
    - **/chat-rooms (GET)**: Retrieves a list of chat rooms that the 
        authenticated user is a part of.
    - **/search-chat-rooms (GET)**: Searches for a 
        specific chat room by its ID.
    - **/chat-room/{chat_room_id} (GET)**: Retrieves the details of 
        a specific chat room by its ID.
    - **/delete-chat-room (DELETE)**: Deletes a chat room owned by 
        the authenticated user.

4. **Join Requests:**
    - **/join-request (POST)**: Submits a request to join a chat room.
    - **/join-request-details (GET)**: Retrieves details of a join request 
        for a chat room owned by the authenticated user.
    - **/handle-join-request (POST)**: Approves or disapproves a 
        join request for the authenticated user's chat room.

5. **Chat Room Details and Online Users:**
    - **/user/submitted-chat-rooms (POST)**: Retrieves chat rooms that the 
        authenticated user has submitted or joined, 
        filtered by group/private status.
    - **/chat-room-details (GET)**: Retrieves detailed information about 
        a chat room owned by the authenticated user.

Each endpoint handles authentication and validation, ensuring that users 
can only access or modify resources they have permissions for, such as 
chat rooms or join requests.
"""

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
    """
    Retrieves the currently authenticated user based on the 
    provided JWT token.

    This function decodes the JWT token provided in the `Authorization` 
    header, extracts the user's email and username, and retrieves the 
    user from the database. If the token is invalid or the user does not 
    exist, an HTTP exception is raised.

    Args:
        token (str): The JWT token provided in the Authorization header.

    Returns:
        UserModel: The authenticated user's details.

    Raises:
        HTTPException (401): If the token is invalid or 
            the user cannot be found.
    """
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
    """
    Creates a new user account.

    This endpoint allows a new user to sign up for the chat service by 
    providing an email, username, and password. It ensures that the email 
    and username are unique before creating the account. If either the 
    email or username already exists, an error is returned.

    Request Body (UserCreate):
    *   **email (str)**: The email address of the user. Must be a valid email.
    *   **username (str)**: The unique username chosen by the user.
    *   **password (str)**: The password chosen by the user. Will be stored 
            in hashed form.

    Response (UserModel):
    *   **id (str | None)**: The unique ID of the user in the database.
    *   **email (str)**: The user's email address.
    *   **username (str)**: The user's chosen username.
    *   **is_online (bool)**: Indicates whether the user is currently online. 
            Default is False.
    *   **is_admin (bool)**: Indicates whether the user has admin privileges. 
            Default is False.

    Raises:
    -   *HTTPException (400)*: If the email or username is already in use, 
            or if there is an error creating the user.
    """
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
        log_message = f"New user created: {new_user.email}"
        logger.info(log_message)

        return new_user
    except ValueError as e:
        log_message = f"Error during signup: {str(e)}"
        logger.error(log_message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Authenticates a user and generates an access token.

    This endpoint allows a user to log in using either their email 
    or username, and their password. If the credentials are correct, 
    a JWT access token is returned, which can be used for authenticated 
    requests. The token expires after a set amount of time 
    (30 minutes by default).

    Request Body (OAuth2PasswordRequestForm):
    *   **username (str)**: The user's email or username.
    *   **password (str)**: The user's password.

    Response (Token):
    *   **access_token (str)**: The JWT access token.
    *   **token_type (str)**: The type of the token (typically "bearer").

    Raises:
    -   *HTTPException (401)*: If the username/email or 
            password is incorrect.
    """
    user = await get_user_by_email(form_data.username) or \
            await get_user_by_username(form_data.username)
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
    """
    Refreshes the JWT access token for the currently authenticated user.

    This endpoint generates a new access token for the authenticated user 
    using their existing credentials. The token is refreshed with a new 
    expiration time (30 minutes by default).

    Request Body (Depends on `get_current_user`):
    *   No additional input is required, as the user's credentials are 
            validated by `get_current_user()`.

    Response (Token):
    *   **access_token (str)**: The new JWT access token.
    *   **token_type (str)**: The type of the token (typically "bearer").

    Raises:
    -   *HTTPException (401)*: If the user is not authenticated or 
            the token is invalid.
    """
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
    """
    Creates a new chat room for the authenticated user.

    This endpoint allows the user to create a new chat room with
    a specified name. The created chat room is automatically 
    set as a group chat.

    Request Body (ChatRoomUpdate):
    *   **name (str)**: The name of the new chat room.

    Response (ChatRoomShow):
    *   **id (str)**: The unique identifier of the chat room.
    *   **name (str)**: The name of the chat room.
    *   **created_at (datetime)**: The timestamp when the chat room 
            was created.
    *   **is_group (bool)**: Indicates whether the chat room is a 
            group chat. Always True for this endpoint.
    *   **last_activity (datetime | None)**: The timestamp of the 
            last activity in the chat room.
    *   **owner (UserUpdate | None)**: The owner of the chat room.

    Raises:
    -   *HTTPException (400)*: If an invalid request is made.
    """
    new_chat_room = await create_chat_room(
        chat_room, current_user.id, True
    )

    return new_chat_room


@router.get("/chat-rooms", response_model=list[ChatRoomShow])
async def get_my_chat_rooms(
    current_user: UserModel = Depends(get_current_user)
):
    """
    Retrieves all chat rooms that the authenticated user is part of.

    This endpoint returns a list of chat rooms that the current user 
    is a member of, including the chat room's name, creation date, 
    and last activity.

    Response (list[ChatRoomShow]):
    *   **id (str)**: The unique identifier of the chat room.
    *   **name (str)**: The name of the chat room.
    *   **created_at (datetime)**: The timestamp when the chat room 
            was created.
    *   **is_group (bool)**: Indicates whether the chat room 
            is a group chat.
    *   **last_activity (datetime | None)**: The timestamp of the 
            last activity in the chat room.
    *   **owner (UserUpdate | None)**: The owner of the chat room.

    Raises:
    -   *HTTPException (401)*: If the user is unauthorized to 
            view the chat rooms.
    """
    chat_rooms = await get_user_chat_rooms(current_user.id)

    return chat_rooms


@router.get(
        "/search-chat-rooms",
        response_model=ChatRoomShow
)
async def search_chat_rooms(
    chat_room_id: str, _: UserModel = Depends(get_current_user)
):
    """
    Searches for a specific chat room by its ID.

    This endpoint allows the user to search for a chat room using 
    its unique identifier. If the chat room is found, the details 
    of the chat room are returned.

    Query Parameters:
    *   **chat_room_id (str)**: The unique identifier of the chat room.

    Response (ChatRoomShow):
    *   **id (str)**: The unique identifier of the chat room.
    *   **name (str)**: The name of the chat room.
    *   **created_at (datetime)**: The timestamp when the chat room 
            was created.
    *   **is_group (bool)**: Indicates whether the chat room is a 
            group chat.
    *   **last_activity (datetime | None)**: The timestamp of the 
            last activity in the chat room.
    *   **owner (UserUpdate | None)**: The owner of the chat room.

    Raises:
    -   *HTTPException (400)*: If the provided chat room ID is invalid.
    -   *HTTPException (404)*: If the chat room is not found.
    """
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat room not found"
        )
    
    return chat_room


@router.post("/join-request", response_model=JoinRequestShow)
async def submit_join_request(
    join_request: JoinRequestCreate,
    current_user: UserModel = Depends(get_current_user)
):
    """
    Submits a request to join a chat room.

    This endpoint allows a user to submit a join request for a specific 
    chat room. The user must provide the ID of the chat room they 
    want to join.

    Request Body (JoinRequestCreate):
    *   **message (str | None)**: An optional message that the user can 
            submit with the join request.
    *   **chat_room_id (str)**: The unique identifier of the chat room 
            the user wants to join.

    Response (JoinRequestShow):
    *   **id (str)**: The unique identifier of the join request.
    *   **message (str | None)**: The message submitted with the 
            join request, if any.
    *   **approved (bool | None)**: Indicates whether the join request 
            has been approved. Defaults to None.
    *   **user (UserUpdate | None)**: The user who submitted the join request.
    *   **chat_room (ChatRoomCreate | None)**: The chat room that 
            the join request is for.

    Raises:
    -   *HTTPException (400)*: If the join request fails.
    """
    new_join_request = await create_join_request(
        join_request, current_user.id
    )

    return new_join_request


@router.get('/chat-room-details')
async def my_chat_room_details(
    chat_room_id: str,
    current_user: UserModel = Depends(get_current_user)
):
    """
    Retrieves the details of a chat room owned by the authenticated user.

    This endpoint allows the user to view the details of a chat room that 
    they own. If the chat room does not belong to the user, 
    an error is returned.

    Query Parameters:
    *   **chat_room_id (str)**: The unique identifier of the chat room.

    Response (dict):
    -   A dictionary containing the chat room details and any associated 
        join requests.

    Raises:
    -   HTTPException (400): If the provided chat room ID is invalid.
    -   HTTPException (401): If the user is not the owner of the chat room.
    """
    try:
        ObjectId(chat_room_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid chat room ID"
        ) from exc

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
    """
    Deletes a chat room owned by the authenticated user.

    This endpoint allows a user to delete a chat room they own. If the 
    user attempts to delete a chat room that they do not own, 
    an error is returned.

    Query Parameters:
    *   **chat_room_id (str)**: The unique identifier of the 
            chat room to delete.

    Raises:
    -   *HTTPException (400)*: If the chat room ID is invalid.
    -   *HTTPException (401)*: If the user is not the owner of the chat room.
    -   *HTTPException (404)*: If the chat room is not found.
    """
    try:
        ObjectId(chat_room_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid chat room ID"
        ) from exc

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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat room not found"
        )


@router.get('/join-request-details', response_model=JoinRequestShow)
async def get_join_request_details(
    join_request_id: str,
    current_user: UserModel = Depends(get_current_user)
):
    """
    Retrieves the details of a join request for a chat room 
    owned by the user.

    This endpoint allows the owner of a chat room to view the details 
    of a join request submitted for their chat room. If the user attempts 
    to view the join request for a chat room they do not own, 
    an error is returned.

    Query Parameters:
    *   **join_request_id (str)**: The unique identifier of the join request.

    Response (JoinRequestShow):
    *   **id (str)**: The unique identifier of the join request.
    *   **message (str | None)**: An optional message provided by the user 
            in the join request.
    *   **approved (bool | None)**: Indicates whether the join request 
            has been approved.
    *   **user (UserUpdate | None)**: The user who submitted the join request.
    *   **chat_room (ChatRoomCreate | None)**: The chat room associated 
            with the join request.

    Raises:
    -   *HTTPException (400)*: If the join request ID is invalid.
    -   *HTTPException (401)*: If the user is not the owner of the chat room 
            associated with the join request.
    -   *HTTPException (404)*: If the join request or chat room is not found.
    """
    try:
        ObjectId(join_request_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid join request ID"
        ) from exc

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
    """
    Handles the approval or disapproval of a join request for a chat room.

    This endpoint allows the owner of a chat room to approve or disapprove 
    a join request submitted for their chat room. Once a request has been 
    handled, it cannot be changed again.

    Request Body:
    *   **join_request_id (str)**: The unique identifier of the join request.
    *   **approval_status (bool)**: Whether to approve (True) or disapprove 
            (False) the join request.

    Raises:
    -   *HTTPException (400)*: If the join request ID is invalid or if the 
            request is already handled.
    -   *HTTPException (401)*: If the user is not the owner of the chat room.
    -   *HTTPException (404)*: If the join request or chat room is not found.
    """
    try:
        ObjectId(join_request_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid join request ID"
        ) from exc
    if approval_status not in (True, False):
        raise ValueError("Invalid approval status")

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
    """
    Retrieves the authenticated user's details.

    This endpoint allows the authenticated user to retrieve their own 
    profile information, including their email, username, online status, 
    and admin status.

    Response (UserModel):
    *   **id (str | None)**: The unique identifier of the user.
    *   **email (str)**: The user's email address.
    *   **username (str)**: The user's chosen username.
    *   **password (str)**: The user's hashed password.
    *   **is_online (bool)**: Indicates whether the user is currently online.
    *   **is_admin (bool)**: Indicates whether the user has admin privileges.
    """
    return current_user


@router.post(
        "/user/submitted-chat-rooms",
        response_model=list[ChatRoomShow]
)
async def get_users_submitted_chat_rooms(
    current_user: UserModel = Depends(get_current_user),
    request: dict = Body(...)
):
    """
    Retrieves chat rooms that the authenticated user is a member of, 
    based on group status.

    This endpoint allows the user to retrieve a list of chat rooms 
    they have submitted or joined, filtered by whether the chat room 
    is a group chat or a private chat.

    Request Body:
    *   **is_group (bool)**: True to retrieve group chat rooms, 
            False to retrieve private chat rooms.

    Response (list[ChatRoomShow]):
    *   **id (str)**: The unique identifier of the chat room.
    *   **name (str)**: The name of the chat room.
    *   **created_at (datetime)**: The timestamp when the 
            chat room was created.
    *   **is_group (bool)**: Indicates whether the chat room 
            is a group chat.
    *   **last_activity (datetime | None)**: The timestamp of 
            the last activity in the chat room.
    *   **owner (UserUpdate | None)**: The owner of the chat room.

    Raises:
    -   *HTTPException (400)*: If the `is_group` status is invalid.
    """
    is_group = request.get('is_group', None)
    if is_group not in (True, False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid is_group status"
        )

    chat_rooms = await retrieve_users_chat_rooms(current_user.id, is_group)

    return chat_rooms


@router.put("/user/online-status")
async def update_user_online_status(
    is_online: bool = Body(...),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Updates the online status of the authenticated user.

    This endpoint allows the user to update their online status 
    (either online or offline).

    Request Body:
    *   **is_online (bool)**: True if the user is online, 
            False if the user is offline.

    Response:
    *   **message (str)**: A success message indicating the user's 
            online status has been updated.

    Raises:
    -   *HTTPException (400)*: If the `is_online` status is not True or False.
    """
    if is_online not in (True, False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user online status"
        )
    await update_user_online_status_db(current_user.id, is_online)
    
    return {"message": "User online status updated successfully"}


@router.post("/pv-chat-room")
async def create_pv_chat_room(
    request: dict = Body(...),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Creates a private chat room between the authenticated user 
    and another user.

    This endpoint allows the user to create a private chat room between 
    themselves and another specified user by their user ID. The response 
    contains the details of the private chat room and 
    the chat sessions for both users.

    Request Body:
    *   **addressed_users_id (str)**: The unique identifier of 
            the other user in the private chat.

    Response (dict):
    *   **chat_room**: The details of the private chat room, including ID, 
            name, and other metadata.
    *   **requesters_session**: The chat session for the user who initiated 
            the private chat.
    *   **addresseds_session**: The chat session for the user being invited 
            to the private chat.

    Raises:
    -   *HTTPException (400)*: If the provided user ID is invalid.
    """
    addressed_users_id = request.get("addressed_users_id")
    try:
        ObjectId(addressed_users_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        ) from exc

    new_chat_room = await create_pv_chat(
        current_user.id, addressed_users_id
    )

    return new_chat_room


@router.get("/chat-room/{chat_room_id}", response_model=ChatRoomShow)
async def chat_room_details(
    chat_room_id: str,
    _: UserModel = Depends(get_current_user)
):
    """
    Retrieves the details of a specific chat room by its ID.

    This endpoint allows the user to retrieve the details of a chat room, 
    including whether it is a group or private chat, based on 
    the provided chat room ID.

    Path Parameters:
    *   **chat_room_id (str)**: The unique identifier of the chat room.

    Response (ChatRoomShow):
    *   **id (str)**: The unique identifier of the chat room.
    *   **name (str)**: The name of the chat room.
    *   **created_at (datetime)**: The timestamp when the chat room was created.
    *   **is_group (bool)**: Indicates whether the chat room is a group chat.
    *   **last_activity (datetime | None)**: The timestamp of the 
            last activity in the chat room.
    *   **owner (UserUpdate | None)**: The owner of the chat room.

    Raises:
    -   *HTTPException (400)*: If the chat room ID is invalid.
    -   *HTTPException (404)*: If the chat room is not found.
    """
    try:
        ObjectId(chat_room_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid chat room ID"
        ) from exc

    chat_room = await get_chat_room(chat_room_id, True)
    if not chat_room:
        chat_room = await get_chat_room(chat_room_id, False)
        if not chat_room:
            raise HTTPException(
                status_code=404, detail="Chat room not found"
            )
    
    return chat_room


@router.get("/pv-online-users")
async def get_pv_chats_online_users(
    current_user: UserModel = Depends(get_current_user)
):
    """
    Retrieves a list of online users with whom the 
    authenticated user has private chats.

    This endpoint allows the user to retrieve the usernames of 
    other users with whom they have private chats and 
    who are currently online.

    Response:
    *   **list[str]**: A list of usernames of online users in 
            the authenticated user's private chats.
    """
    return await get_online_users_pv(current_user.id)
