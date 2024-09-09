import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient | None = None
    db: AsyncIOMotorClient | None = None

    @classmethod
    async def connect_db(cls):
        try:
            cls.client = AsyncIOMotorClient("mongodb://localhost:27017")
            cls.db = cls.client.chat_service
            await cls.client.admin.command('ismaster')
            logger.info("Connected to MongoDB")
        except ConnectionFailure:
            logger.error("Failed to connect to MongoDB")
            raise

    @classmethod
    async def close_db(cls):
        if cls.client:
            cls.client.close()
            logger.info("Closed MongoDB connection")

    @classmethod
    def get_db(cls):
        if cls.db is None:
            raise ConnectionFailure("Database is not initialized. Call connect_db() first.")
        
        return cls.db

db = Database()
