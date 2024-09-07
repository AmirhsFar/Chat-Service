from bson.objectid import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException
from .database import (
    users_collection,
    items_collection
)
from .schemas import (
    User,
    UserCreate,
    Item,
    ItemCreate
)

def get_user(user_id: str):
    try:
        object_id = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    user = users_collection.find_one({'_id': object_id})
    if user:

        return User(id=str(user['_id']), **user)
    
    return None

def get_user_by_email(email: str):
    user = users_collection.find_one({'email': email})
    if user:

        return User(id=str(user['_id']), **user)
    
    return None

def get_users(skip: int = 0, limit: int = 100):
    users = users_collection.find().skip(skip).limit(limit)

    return [User(id=str(user['_id']), **user) for user in users]

def create_user(user: UserCreate):
    user_doc = user.model_dump()
    user_doc['is_active'] = True
    user_doc['items'] = []
    users_collection.insert_one(user_doc)
    try:

        return User(id=str(user_doc['_id']), **user_doc)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"IDs: {user_doc['_id']}")

def get_items(skip: int = 0, limit: int = 100):
    items = items_collection.find().skip(skip).limit(limit)

    return [Item(id=str(item['_id']), **item) for item in items]

def create_user_item(item: ItemCreate, user_id: str):
    item_doc = item.model_dump()
    item_doc['owner_id'] = ObjectId(user_id)
    items_collection.insert_one(item_doc)

    return Item(id=str(item_doc['_id']), **item_doc)
