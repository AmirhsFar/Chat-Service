"""
database.py

This module establishes a connection between the FastAPI server and the 
MongoDB database using Motor (async driver for MongoDB). It contains the 
`Database` class that provides methods to connect to the MongoDB server, 
retrieve the database instance, and close the connection.

Classes:
    Database: Handles connection to the MongoDB database using Motor.
"""

import logging
import os
from urllib.parse import quote_plus
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class Database:
    """
    A class to manage the connection between the FastAPI application 
    and MongoDB database.
    
    Attributes:
        client (AsyncIOMotorClient | None): The MongoDB client used 
        for the connection.
        db (AsyncIOMotorClient | None): The MongoDB database instance.

    Methods:
        connect_db: Establishes a connection to the MongoDB server and 
        initializes the database instance.
        close_db: Closes the connection to the MongoDB server.
        get_db: Returns the current MongoDB database instance or raises 
        an exception if not initialized.
    """

    client: AsyncIOMotorClient | None = None
    db: AsyncIOMotorClient | None = None

    @classmethod
    async def connect_db(cls):
        """
    Connects to the MongoDB server and sets the `client` and `db` attributes.

    This method attempts to establish a connection to the MongoDB server
    located at the configured host and port, and it initializes the `client`
    and `db` attributes with the database specified by the `MONGO_DB`
    environment variable (default is `chat_service`).

    The MongoDB user and password are retrieved from the Docker secrets
    specified by the `MONGO_USER_FILE` and `MONGO_PASSWORD_FILE` environment
    variables, respectively.

    If the connection fails, a `ConnectionFailure` exception is raised.

    Raises:
        ConnectionFailure: If unable to establish a connection to the
            MongoDB server.
    """
        try:
            mongo_user = os.getenv("MONGO_USER")
            if mongo_user is None:
                with open(
                    "/run/secrets/mongo_user", "r", encoding="utf-8"
                ) as f:
                    mongo_user = f.read().strip()

            mongo_password = os.getenv("MONGO_PASSWORD")
            if mongo_password is None:
                with open(
                    "/run/secrets/mongo_password", "r", encoding="utf-8"
                ) as f:
                    mongo_password = f.read().strip()

            mongo_host = os.getenv("MONGO_HOST", "localhost")
            mongo_port = os.getenv("MONGO_PORT", "27017")
            mongo_db = os.getenv("MONGO_DB", "chat_service")

            mongo_user_escaped = quote_plus(mongo_user)
            mongo_password_escaped = quote_plus(mongo_password)
            mongo_uri = f"mongodb://{mongo_user_escaped}:"
            mongo_uri += f"{mongo_password_escaped}@{mongo_host}:"
            mongo_uri += f"{mongo_port}/{mongo_db}?authSource=admin"

            cls.client = AsyncIOMotorClient(mongo_uri)
            cls.db = cls.client[mongo_db]
            await cls.client.admin.command('ismaster')
            logger.info("Connected to MongoDB")
        except ConnectionFailure:
            logger.error("Failed to connect to MongoDB")
            raise

    @classmethod
    async def close_db(cls):
        """
        Closes the connection to the MongoDB server.

        This method checks if a MongoDB client exists. If so, it 
        closes the connection and logs the closure. If there is no 
        active connection, no action is taken.
        """
        if cls.client:
            cls.client.close()
            logger.info("Closed MongoDB connection")

    @classmethod
    def get_db(cls):
        """
        Retrieves the current MongoDB database instance.
        
        This method returns the `db` attribute, which holds the MongoDB 
        database instance. 
        If the database connection has not been established 
        (i.e., `connect_db()` was not called), it raises a `ConnectionFailure` 
        with a relevant error message.

        Returns:
            AsyncIOMotorClient: The MongoDB database instance.

        Raises:
            ConnectionFailure: If the database is not initialized 
            (i.e., `connect_db()` was not called).
        """
        if cls.db is None:
            exception_message = "Database is not initialized. "
            exception_message += "Call connect_db() first."
            raise ConnectionFailure(exception_message)
        
        return cls.db


db = Database()
