import os
from pymongo import MongoClient

MONGO_URI = os.environ.get("MONGO_URI")

cliente = MongoClient(
    MONGO_URI,
    tls=True,
    serverSelectionTimeoutMS=30000
)

db = cliente["CIEM"]

try:
    cliente.admin.command("ping")
    print("====================================")
    print("✅ CONECTADO A MONGODB ATLAS")
    print("BASE ACTUAL:", db.name)
    print("====================================")
except Exception as e:
    print("❌ ERROR MONGODB:", e)