"""
main.py

This module is the entry point for the FastAPI-based chat service system. 
It sets up the application, mounts necessary static files, applies middleware, 
and includes routes for both the user-facing APIs and the admin panel. 
The chat service integrates WebSocket functionality via Socket.IO, enabling 
real-time communication between users.

Key Features:
- **Lifespan Management**: Manages startup and shutdown tasks such as 
    database connection and indexing of chat messages.
- **Static File Handling**: Mounts the `/uploads` directory to serve files 
    uploaded by users.
- **CORS Middleware**: Configures Cross-Origin Resource Sharing (CORS) 
    to allow requests from all origins.
- **Routers**:
    - **inits_router**: Handles user-facing API routes 
        (e.g., chat room creation, user management).
    - **admin_router**: Handles admin panel API routes, prefixed with 
        `/admin` for administrative tasks.
- **WebSocket Integration**: Mounts the Socket.IO app at `/socket.io` to 
    enable real-time messaging between users.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from database import db
from operations import load_descriptions
from inits_apis import router as inits_router
from admin_apis import router as admin_router
from sockets import sio_app


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Manages the startup and shutdown events of the FastAPI application.

    On startup, this function connects to the MongoDB database and creates 
    indexes for efficient message querying, such as indexing the `_id` and 
    `chat_room_id` fields in the `messages` collection. On shutdown, the 
    database connection is gracefully closed.

    Yields:
        None: This function yields control back to the application after 
        performing the necessary startup operations, and resumes at shutdown 
        to clean up resources.

    Startup Tasks:
        - Connects to MongoDB.
        - Creates indexes for the `messages` collection to optimize queries.
    
    Shutdown Tasks:
        - Closes the MongoDB database connection.
    """
    await db.connect_db()
    await db.get_db().messages.create_index("_id")
    await db.get_db().messages.create_index("chat_room_id")
    yield
    await db.close_db()


descriptions = load_descriptions('descriptions.txt')

tags_metadata = [
    {
        'name': 'inits',
        'description': descriptions['INITS_DESCRIPTION']
    },
    {
        'name': 'admin panel',
        'description': descriptions['ADMIN_DESCRIPTION']
    }
]


chat_service_app = FastAPI(
    title="Chat Service App",
    description=descriptions['APPS_DESCRIPTION'],
    version='1.0.0',
    contact={
        'name':'Amirhossein Farahani',
        'email': 'amirhosseinfarahani13@gmail.com'
    },
    openapi_tags=tags_metadata,
    lifespan=lifespan
)
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
