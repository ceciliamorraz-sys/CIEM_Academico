import os
from pymongo import MongoClient


# =====================================
# CONEXIÓN MONGODB ATLAS
# =====================================

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise Exception("MONGO_URI no está configurada en Render")


cliente = MongoClient(
    MONGO_URI,
    tls=True,
    serverSelectionTimeoutMS=30000
)


# Base de datos CIEM
db = cliente["CIEM"]


# =====================================
# PRUEBA DE CONEXIÓN
# =====================================

try:

    cliente.admin.command("ping")

    print("====================================")
    print("✅ CONECTADO A MONGODB ATLAS")
    print("BASE ACTUAL:", db.name)

    print("COLECCIONES:")
    print(db.list_collection_names())

    print("------------------------------------")
    print("TOTAL USUARIOS:", db.usuarios.count_documents({}))

    print("DOCUMENTOS USUARIOS:")

    for usuario in db.usuarios.find(
        {},
        {
            "_id": 1,
            "usuario": 1,
            "rol": 1
        }
    ):
        print(usuario)

    print("====================================")


except Exception as e:

    print("❌ ERROR MONGODB:", e)