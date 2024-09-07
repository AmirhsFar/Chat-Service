from .routers import users_router
from .routers import items_router
from .dependencies import get_query_token
from fastapi import (
    Depends,
    FastAPI
)

app = FastAPI(dependencies=[Depends(get_query_token)])
app.include_router(users_router)
app.include_router(items_router)

@app.get('/')
async def root():
    return {'message': 'Hello Bigger Applications!'}
