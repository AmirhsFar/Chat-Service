from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from database import db
from inits_apis import router as inits_router
from admin_apis import router as admin_router
from sockets import sio_app


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Startup
    await db.connect_db()
    await db.get_db().messages.create_index("_id")
    await db.get_db().messages.create_index("chat_room_id")
    yield
    # Shutdown
    await db.close_db()


chat_service_app = FastAPI(lifespan=lifespan)
chat_service_app.mount('/socket.io', app=sio_app)
chat_service_app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)
chat_service_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
chat_service_app.include_router(
    inits_router, tags=["inits"]
)
chat_service_app.include_router(
    admin_router, prefix='/admin', tags=['admin panel']
)
