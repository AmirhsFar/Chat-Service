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
    update_user_online_status_db
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
async def connect(sid, environ, auth):
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

        await sio_server.save_session(sid, {
            'user_id': str(user.id), 'email': email,
            'username': username, 'chat_room_id': chat_room_id
        })
        await update_user_online_status_db(str(user.id), True)
        print(f'{username}: is connected')
        await sio_server.enter_room(sid, chat_room_id)
        await sio_server.emit(
            'join', {'username': username, 'email': email},
            room=chat_room_id
        )
        recent_messages = await get_recent_messages(chat_room_id)
        await sio_server.emit('initial_messages', [
            message.dict_with_iso_timestamp() for message in recent_messages
        ], to=sid)
    except JWTError:
        return False


@sio_server.event
async def chat(sid, data):
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
    session = await sio_server.get_session(sid)
    user_id = session.get('user_id')
    chat_room_id = session.get('chat_room_id')

    if user_id and chat_room_id:
        await update_user_online_status_db(user_id, False)
        await update_chat_room_session_last_seen(user_id, chat_room_id)
        await sio_server.leave_room(sid, chat_room_id)
    
    print(f'{session["username"]}: is disconnected')
