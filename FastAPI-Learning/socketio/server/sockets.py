from socketio import (
    AsyncServer, ASGIApp
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

@sio_server.event
async def chat(sid, message):
    await sio_server.emit('chat', {'sid': sid, 'message': message})

@sio_server.event
async def disconnect(sid):
    print(f'{sid}: is disconnected')
