from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from database import db
from fastapi import (
    FastAPI,
    HTTPException
)
from sockets import sio_app
import crud
import schemas

@asynccontextmanager
async def lifespan(_: FastAPI):
    # Startup
    await db.connect_db()
    yield
    # Shutdown
    await db.close_db()

app = FastAPI(lifespan=lifespan)
app.mount('/socket.io', app=sio_app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.post('/users', response_model=schemas.User, status_code=201)
async def create_user(user: schemas.UserCreate):
    found_user = await crud.get_user_by_email(user.email)
    if found_user:
        raise HTTPException(
            status_code=400, detail='Email already registered'
        )
    
    return await crud.create_user(user)

@app.get('/users', response_model=list[schemas.User])
async def read_users(skip: int = 0, limit: int = 100):
    users = await crud.get_users(skip=skip, limit=limit)

    return users

@app.get('/users/{user_id}', response_model=schemas.User)
async def read_user(user_id: str):
    db_user = await crud.get_user(user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail='User not found')
    
    return db_user

@app.post('/users/{user_id}/item', response_model=schemas.Item, status_code=201)
async def create_item_for_user(user_id: str, item: schemas.ItemCreate):

    return await crud.create_user_item(item=item, user_id=user_id)

@app.get('/items', response_model=list[schemas.Item])
async def read_items(skip: int = 0, limit: int = 100):
    items = await crud.get_items(skip=skip, limit=limit)

    return items

@app.get('/messages', response_model=list[schemas.MessageModel])
async def read_messages(skip: int = 0, limit: int = 100):
    messages = await crud.get_messages(skip=skip, limit=limit)

    return messages
