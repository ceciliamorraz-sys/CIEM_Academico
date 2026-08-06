import os
from pymongo import MongoClient
from urllib.parse import quote_plus


usuario_atlas = "ceciliamorraz_db_user"
password_atlas = quote_plus("CiemAtlas2026")


MONGO_URI = (
    f"mongodb+srv://{usuario_atlas}:{password_atlas}"
    "@cluster0.olbd8g8.mongodb.net/CIEM"
    "?retryWrites=true&w=majority&appName=Cluster0"
)


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