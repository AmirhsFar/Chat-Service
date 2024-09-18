from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from database import db
from datetime import timedelta
from fastapi.staticfiles import StaticFiles
from jose import (
    JWTError,
    jwt
)
from fastapi.security import (
    OAuth2PasswordRequestForm,
    OAuth2PasswordBearer
)
from fastapi import (
    FastAPI,
    HTTPException,
    status,
    Depends
)
from utils import (
    verify_password,
    create_access_token,
    SECRET_KEY,
    ALGORITHM
)
from sockets import sio_app
import crud
import schemas

@asynccontextmanager
async def lifespan(_: FastAPI):
    # Startup
    await db.connect_db()
    # Create indexes
    await db.get_db().messages.create_index("user_id")
    await db.get_db().messages.create_index("username")
    yield
    # Shutdown
    await db.close_db()

app = FastAPI(lifespan=lifespan)
app.mount('/socket.io', app=sio_app)
app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

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
        token_data = schemas.TokenData(email=email, username=username)
    except JWTError as exc:
        raise credentials_exception from exc
    user = await crud.get_user_by_email(email=token_data.email)
    if user is None:
        raise credentials_exception
    
    return user

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = await crud.get_user_by_email(form_data.username)
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

@app.get('/users/me', response_model=schemas.User)
async def read_users_me(
    current_user: schemas.User = Depends(get_current_user)
):
    return current_user

@app.post('/users', response_model=schemas.User, status_code=201)
async def create_user(user: schemas.UserCreate):
    found_user = await crud.get_user_by_email(user.email)
    if found_user:
        raise HTTPException(
            status_code=400, detail='Email already registered'
        )
    
    return await crud.create_user(user)

@app.get('/users', response_model=list[schemas.User])
async def read_users(
    skip: int = 0, limit: int = 100,
    _: schemas.User = Depends(get_current_user)
):
    users = await crud.get_users(skip=skip, limit=limit)

    return users

@app.get('/users/{user_id}', response_model=schemas.User)
async def read_user(
    user_id: str, _: schemas.User = Depends(get_current_user)
):
    db_user = await crud.get_user(user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail='User not found')
    
    return db_user

@app.post('/users/{user_id}/item', response_model=schemas.Item, status_code=201)
async def create_item_for_user(
    user_id: str, item: schemas.ItemCreate,
    _: schemas.User = Depends(get_current_user)
):

    return await crud.create_user_item(item=item, user_id=user_id)

@app.get('/items', response_model=list[schemas.Item])
async def read_items(
    skip: int = 0, limit: int = 100,
    _: schemas.User = Depends(get_current_user)
):
    items = await crud.get_items(skip=skip, limit=limit)

    return items

@app.get('/messages', response_model=list[schemas.MessageModel])
async def read_messages(
    skip: int = 0, limit: int = 100,
    _: schemas.User = Depends(get_current_user)
):
    messages = await crud.get_messages(skip=skip, limit=limit)

    return messages

@app.delete("/clear_messages")
async def clear_messages(_: schemas.User = Depends(get_current_user)):
    deleted_count = await crud.delete_all_messages()
    if deleted_count > 0:

        return {"message": f"Deleted {deleted_count} messages"}
    else:
        raise HTTPException(status_code=404, detail="No messages found")

@app.delete("/clear_users")
async def clear_users(_: schemas.User = Depends(get_current_user)):
    deleted_count = await crud.delete_all_users()
    if deleted_count > 0:

        return {"message": f"Deleted {deleted_count} users"}
    else:
        raise HTTPException(status_code=404, detail="No users found")

@app.delete("/clear_items")
async def clear_items(_: schemas.User = Depends(get_current_user)):
    deleted_count = await crud.delete_all_items()
    if deleted_count > 0:

        return {"message": f"Deleted {deleted_count} items"}
    else:
        raise HTTPException(status_code=404, detail="No items found")
