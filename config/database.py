import os
from pymongo import MongoClient

MONGO_URI = os.environ.get("MONGO_URI")

cliente = MongoClient(
    MONGO_URI,
    tls=True,
    serverSelectionTimeoutMS=30000
)

db = cliente["CIEM_Academico"]