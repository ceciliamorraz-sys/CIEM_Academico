import os
from pymongo import MongoClient


# =====================================
# CONEXIÓN MONGODB ATLAS
# =====================================

import os
from pymongo import MongoClient


# =====================================
# CONEXIÓN MONGODB ATLAS
# =====================================

MONGO_URI = os.getenv("MONGO_URI")


# Desarrollo local
# Si no existe variable de entorno usa esta conexión
if not MONGO_URI:
    MONGO_URI = "mongodb+srv://ciemadmin:CiemAtlas2026@cluster0.olbd8g8.mongodb.net/CIEM?retryWrites=true&w=majority&appName=Cluster0"


cliente = MongoClient(
    MONGO_URI,
    tls=True,
    serverSelectionTimeoutMS=30000
)


# =====================================
# BASE DE DATOS CIEM
# =====================================

db = cliente["CIEM"]
print("====================================")
print("🔎 VERIFICACIÓN BASE CIEM")
print("BASE:", db.name)

print("BUSCAR USUARIO alma:")
print(
    db.estudiantes.find_one({
        "usuario": "alma"
    })
)

print("BUSCAR ID 001:")
print(
    db.estudiantes.find_one({
        "_id": "001"
    })
)

print("TOTAL ESTUDIANTES:")
print(
    db.estudiantes.count_documents({})
)

print("====================================")




print("========== MONGODB ==========")
print("BASE:", db.name)

try:
    print("HOSTS:", cliente.nodes)
    print("COLECCIONES:", db.list_collection_names())
except Exception as e:
    print("ERROR:", e)

print("=============================")
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