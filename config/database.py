import os
from pymongo import MongoClient

# ==========================================================
# CONEXIÓN MONGODB ATLAS
# ==========================================================

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    MONGO_URI = (
        "mongodb+srv://ciemadmin:CiemAtlas2026"
        "@cluster0.olbd8g8.mongodb.net/CIEM"
        "?retryWrites=true&w=majority&appName=Cluster0"
    )

# ==========================================================
# CLIENTE MONGODB
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

print("------------------------------------")
print("📚 ASIGNATURAS DOC012:")

asignaturas_doc012 = list(
    db.asignaturas.find({"docente_id": "DOC012"})
)

print("CANTIDAD ENCONTRADA:", len(asignaturas_doc012))

for asignatura in asignaturas_doc012:
    print(
        asignatura.get("_id"),
        "|",
        asignatura.get("nombre"),
        "| GRADO:",
        asignatura.get("grado"),
        "| SECCIÓN:",
        asignatura.get("seccion")
    )

print("====================================")