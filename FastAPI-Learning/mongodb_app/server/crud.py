from datetime import datetime
from bson.objectid import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException
from database import db
from schemas import (
    User,
    UserCreate,
    Item,
    ItemCreate,
    MessageModel
)

async def get_user(user_id: str):
    try:
        object_id = ObjectId(user_id)
    except InvalidId as e:
        raise HTTPException(
            status_code=400, detail="Invalid user ID"
        ) from e
    user = await db.get_db().users.find_one({'_id': object_id})
    if user:
    
        return User(id=str(user['_id']), **user)
    
    return None

async def get_user_by_email(email: str):
    user = await db.get_db().users.find_one({'email': email})
    if user:
    
        return User(id=str(user['_id']), **user)
    
    return None

async def get_users(skip: int = 0, limit: int = 100):
    users = await db.get_db().users.find().skip(skip).limit(limit).to_list(None)

    return [User(id=str(user['_id']), **user) for user in users]

async def create_user(user: UserCreate):
    user_doc = user.model_dump()
    user_doc['is_active'] = True
    user_doc['items'] = []
    await db.get_db().users.insert_one(user_doc)
    try:

        return User(id=str(user_doc['_id']), **user_doc)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"IDs: {user_doc['_id']}"
        ) from e

async def get_items(skip: int = 0, limit: int = 100):
    items = await db.get_db().items.find().skip(skip).limit(limit).to_list(None)

    return [Item(id=str(item['_id']), **item) for item in items]

async def create_user_item(item: ItemCreate, user_id: str):
    item_doc = item.model_dump()
    item_doc['owner_id'] = ObjectId(user_id)
    await db.get_db().items.insert_one(item_doc)

    return Item(id=str(item_doc['_id']), **item_doc)

async def create_message(sid: str, content: str):
    message_doc = {
        "user_id": sid,
        "content": content,
        "timestamp": datetime.now()
    }
    result = await db.get_db().messages.insert_one(message_doc)
    message_doc["id"] = str(result.inserted_id)

    return MessageModel(**message_doc)

async def get_recent_messages(limit: int = 50, before_id: str = None):
    query = {}
    if before_id:
        query["_id"] = {"$lt": ObjectId(before_id)}
    
    messages = await db.get_db().messages.find(query).sort(
        "_id", -1
    ).limit(limit).to_list(None)

    return [
        MessageModel(
            id=str(msg["_id"]),
            user_id=msg["user_id"],
            content=msg["content"],
            timestamp=msg["timestamp"]
        ) for msg in messages
    ][::-1]

async def get_messages(skip: int = 0, limit: int = 100):
    msgs = await db.get_db().messages.find().skip(skip).limit(limit).to_list(None)

    return [
        MessageModel(
            id=str(msg["_id"]),
            user_id=msg["user_id"],
            content=msg["content"],
            timestamp=msg["timestamp"]
        ) for msg in msgs
    ]
