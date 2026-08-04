import os
from pymongo import MongoClient

MONGO_URI = os.environ.get("MONGO_URI")

cliente = MongoClient(MONGO_URI)

db = cliente["CIEM"]