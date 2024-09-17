from socketio import (
    AsyncServer, ASGIApp
)
from crud import (
    create_message,
    get_recent_messages
)

sio_server = AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=[]
)

sio_app = ASGIApp(
    socketio_server=sio_server,
    socketio_path='socket.io'
)

@sio_server.event
async def connect(sid, _, __):
    print(f'{sid}: is connected')
    await sio_server.emit('join', {'sid': sid})
    recent_messages = await get_recent_messages()
    await sio_server.emit('initial_messages', [
        message.dict_with_iso_timestamp() for message in recent_messages
    ], to=sid)

@sio_server.event
async def chat(sid, message):
    new_message = await create_message(sid, message)
    message_dict = new_message.dict_with_iso_timestamp()
    await sio_server.emit('chat', {'message': message_dict})

@sio_server.event
async def get_more_messages(sid, data):
    older_messages = await get_recent_messages(
        before_id=data['oldest_message_id']
    )
    await sio_server.emit('more_messages', [
        message.dict_with_iso_timestamp() for message in older_messages
    ], to=sid)

@sio_server.event
async def disconnect(sid):
    print(f'{sid}: is disconnected')