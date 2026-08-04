import os
from pymongo import MongoClient

cliente = MongoClient(os.environ.get("MONGO_URI"))

db = cliente["CIEM"]