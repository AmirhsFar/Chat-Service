"""
sockets.py

This module handles real-time chat functionality using Socket.IO for 
the FastAPI application. It includes event handlers for connecting users, 
sending messages, retrieving older messages, and handling user disconnections. 
The module enables users to have real-time messaging in chat rooms and ensures 
that their online status and activity in chat rooms are updated accordingly.

Events:
    - connect: Handles user connection, updating online status, retrieving 
        chat room users and messages.
    - chat: Handles sending and saving messages (text, images, files) 
        to chat rooms.
    - get_more_messages: Retrieves and sends older messages 
        when the user scrolls up.
    - disconnect: Handles user disconnection, updating their 
        online status and leaving the chat room.
"""

import os
import aiofiles
from jose import (
    JWTError,
    jwt
)
from socketio import (
    AsyncServer, ASGIApp
)
from utils import (
    SECRET_KEY, ALGORITHM
)
from operations import (
    create_message,
    get_recent_messages,
    get_user_by_email,
    update_chat_room_session_last_seen,
    update_chat_room_last_activity,
    update_user_online_status_db,
    rooms_online_users
)
from schemas import MessageType

UPLOAD_DIR = "uploads"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

sio_server = AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=[]
)

sio_app = ASGIApp(
    socketio_server=sio_server,
    socketio_path='socket.io'
)


@sio_server.event
async def connect(sid, _, auth):
    """
    Handles a user's connection to the Socket.IO server.

    This function authenticates the user using a JWT token passed in the 
    `auth` parameter, retrieves the user's details from the database, 
    updates their online status, and sends them the list of online users 
    in the chat room as well as the recent messages. The user is also 
    added to the chat room, and their join event is emitted to other 
    online users in the room.

    Args:
        sid (str): The session ID for the connected user.
        auth (dict): The authentication data containing the JWT token 
            and chat room ID.

    Returns:
        bool: Returns False if authentication fails, otherwise allows 
            the connection to proceed.
    """
    try:
        if not auth:
            raise JWTError("No authentication details provided")
        token = auth.get('token')
        if not token:
            raise JWTError("No token provided")
        chat_room_id = auth.get('chat_room_id')
        if not chat_room_id:
            raise JWTError("No chat room ID provided")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("email")
        username = payload.get("username")
        if not email or not username:
            raise JWTError("Invalid token")
        user = await get_user_by_email(email)
        if not user:
            raise JWTError("User not found")
        user_id = str(user.id)
        await sio_server.save_session(sid, {
            'user_id': user_id, 'email': email,
            'username': username, 'chat_room_id': chat_room_id
        })
        await update_user_online_status_db(user_id, True)
        print(f'{username}: is connected')
        await sio_server.enter_room(sid, chat_room_id)
        await sio_server.emit(
            'join', {'username': username, 'email': email},
            room=chat_room_id
        )
        online_users = await rooms_online_users(user_id, chat_room_id)
        recent_messages = await get_recent_messages(chat_room_id)
        await sio_server.emit('online_users', online_users, to=sid)
        await sio_server.emit('initial_messages', [
            message.dict_with_iso_timestamp() for message in recent_messages
        ], to=sid)
    except JWTError:

        return False


@sio_server.event
async def chat(sid, data):
    """
    Handles sending a new message to a chat room.

    This function processes the incoming message (text, image, or file), 
    saves it to the database, and emits the message to all users in the 
    chat room. If the message contains a file, the file is saved locally 
    in the `uploads` directory.

    Args:
        sid (str): The session ID for the user sending the message.
        data (dict): The message data containing the content, message type, 
            and optional file details.
    """
    session = await sio_server.get_session(sid)
    user_id = session['user_id']
    chat_room_id = session['chat_room_id']
    username = session['username']

    message_type = MessageType(data['message_type'])
    content = data['content']
    file_name = data.get('file_name')
    file_path = None

    if message_type != MessageType.TEXT:
        file_path = os.path.join(UPLOAD_DIR, file_name)
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(data['file'])

    new_message = await create_message(
        user_id, chat_room_id, username,
        content, message_type, file_name, file_path
    )
    await update_chat_room_last_activity(
        chat_room_id, new_message.timestamp
    )
    await sio_server.emit('chat', {
        'message': new_message.dict_with_iso_timestamp()
    }, room=chat_room_id)


@sio_server.event
async def get_more_messages(sid, data):
    """
    Retrieves older messages for a chat room when the user 
    does some action (e.g. scrolls up) to load more messages.

    This function fetches older messages from the database, starting from 
    the message before the `oldest_message_id` provided, and sends them to 
    the requesting user.

    Args:
        sid (str): The session ID for the user requesting more messages.
        data (dict): The data containing the ID of 
            the oldest message already loaded.
    """
    session = await sio_server.get_session(sid)
    chat_room_id = session['chat_room_id']
    older_messages = await get_recent_messages(
        chat_room_id,
        before_id=data['oldest_message_id']
    )
    await sio_server.emit('more_messages', [
        message.dict_with_iso_timestamp() for message in older_messages
    ], to=sid)


@sio_server.event
async def disconnect(sid):
    """
    Handles the disconnection of a user from the chat room.

    This function updates the user's online status, marks their 
    chat room session's last seen time, and removes them from the chat room. 
    The user's departure is emitted to the other users in the chat room.

    Args:
        sid (str): The session ID for the disconnecting user.
    """
    session = await sio_server.get_session(sid)
    user_id = session.get('user_id')
    chat_room_id = session.get('chat_room_id')
    username = session['username']

    if user_id and chat_room_id:
        await update_user_online_status_db(user_id, False)
        await update_chat_room_session_last_seen(user_id, chat_room_id)
        await sio_server.leave_room(sid, chat_room_id)
        await sio_server.emit(
            'leave', {'username': username}, room=chat_room_id
        )
    print(f'{session["username"]}: is disconnected')
