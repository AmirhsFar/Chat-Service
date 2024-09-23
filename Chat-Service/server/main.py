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

APPS_DESCRIPTION = "The `Chat Service App` is a high-performance real-time "
APPS_DESCRIPTION += "messaging platform built using `FastAPI`, `Socket.io`, "
APPS_DESCRIPTION += "and `MongoDB`.\n\n It provides a robust and feature-rich "
APPS_DESCRIPTION += "environment for users to engage in both **group chats** "
APPS_DESCRIPTION += "and **private chats** with seamless real-time communication."
APPS_DESCRIPTION += "\n\n### **Key Features:**\n\n- **Real-Time Messaging**:\n\n"
APPS_DESCRIPTION += "Enjoy high-speed messaging powered by `FastAPI` and "
APPS_DESCRIPTION += "`Socket.io`, ensuring a responsive and real-time chat experience "
APPS_DESCRIPTION += "for all users.\n\n- **Group Chat**:\n\nUsers can create chat "
APPS_DESCRIPTION += "rooms, invite others, and manage join requests. Only after the "
APPS_DESCRIPTION += "room owner approves a request can users participate in group "
APPS_DESCRIPTION += "conversations.\n\n- **Private Chat**:\n\nUsers can initiate "
APPS_DESCRIPTION += "private one-on-one chats by simply selecting another user's "
APPS_DESCRIPTION += "username from a group chat session, creating a private room "
APPS_DESCRIPTION += "for more personal communication.\n\n- **Online Users**:\n\n"
APPS_DESCRIPTION += "View the list of online users in real-time, both in the "
APPS_DESCRIPTION += "*Your Chat Rooms* page and within each chat room, making "
APPS_DESCRIPTION += "it easy to see who's available to chat.\n\n- **Admin Panel**:"
APPS_DESCRIPTION += "\n\nIncludes a powerful admin panel that allows admin users "
APPS_DESCRIPTION += "to perform full **CRUD operations** on database resources, "
APPS_DESCRIPTION += "giving administrators complete control over users, chat rooms, "
APPS_DESCRIPTION += "join requests and other database schemas.\n\n"
APPS_DESCRIPTION += "\n\nBacked by the flexibility and performance of `FastAPI`, "
APPS_DESCRIPTION += "the real-time capabilities of `Socket.io`, and the scalability "
APPS_DESCRIPTION += "of `MongoDB`, the Chat Service App delivers a smooth and "
APPS_DESCRIPTION += "feature-rich chat experience that can handle a wide range of "
APPS_DESCRIPTION += "use cases, from casual group chats to more private, "
APPS_DESCRIPTION += "one-on-one messaging."

INITS_DESCRIPTION = "This set of APIs handle user management, "
INITS_DESCRIPTION += "authentication, and chat room operations within "
INITS_DESCRIPTION += "the chat service system. They handles a wide range "
INITS_DESCRIPTION += "of functionalities, including user sign-up, login, "
INITS_DESCRIPTION += "managing chat rooms, handling join requests, and more."

ADMIN_DESCRIPTION = "This set of APIs provide CRUD operations on database "
ADMIN_DESCRIPTION += "schemas for an admin panel. By using these APIs, "
ADMIN_DESCRIPTION += "the admin user can manage database instances easily."

tags_metadata = [
    {
        'name': 'inits',
        'description': INITS_DESCRIPTION
    },
    {
        'name': 'admin panel',
        'description': ADMIN_DESCRIPTION
    }
]


chat_service_app = FastAPI(
    title="Chat Service App",
    description=APPS_DESCRIPTION,
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
