import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "meteo")

client = AsyncIOMotorClient(MONGO_URL)
db = client[MONGO_DB]

def observations_collection():
    return db["observations"]
