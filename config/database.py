import os
from pymongo import MongoClient

# ==========================================================
# CONEXIÓN MONGODB ATLAS
# ==========================================================

MONGO_URI = os.getenv("MONGO_URI")

# ----------------------------------------------------------
# CONEXIÓN LOCAL / DESARROLLO
# ----------------------------------------------------------

if not MONGO_URI:
    MONGO_URI = (
        "mongodb+srv://ciemadmin:CiemAtlas2026"
        "@cluster0.olbd8g8.mongodb.net/CIEM"
        "?retryWrites=true&w=majority&appName=Cluster0"
    )

# ==========================================================
# CREAR CLIENTE MONGODB
# ==========================================================

cliente = MongoClient(
    MONGO_URI,
    tls=True,
    serverSelectionTimeoutMS=30000
)

# ==========================================================
# BASE DE DATOS
# ==========================================================

db = cliente["CIEM"]

# ==========================================================
# PRUEBA DE CONEXIÓN
# ==========================================================

try:

    cliente.admin.command("ping")

    print("====================================")
    print("✅ CONECTADO A MONGODB ATLAS")
    print("====================================")

    print("BASE ACTUAL:", db.name)

    print("------------------------------------")
    print("📂 COLECCIONES:")
    print(db.list_collection_names())

    print("------------------------------------")
    print("📊 TOTAL ESTUDIANTES:")

    total_estudiantes = db.estudiantes.count_documents({})

    print(total_estudiantes)

    print("====================================")

except Exception as e:

    print("====================================")
    print("❌ ERROR DE CONEXIÓN MONGODB")
    print("====================================")

    print(type(e).__name__)
    print(e)

    print("====================================")