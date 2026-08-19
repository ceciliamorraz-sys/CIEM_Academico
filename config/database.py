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
print("\n")
print("==============================================")
print("🔎 TODAS LAS ASIGNATURAS")
print("==============================================")

todas = list(
    db.asignaturas.find({})
)

print("TOTAL ASIGNATURAS EN MONGO:", len(todas))

for a in todas:

    print(
        "ID:", a.get("_id"),
        "| NOMBRE:", a.get("nombre"),
        "| GRADO:", a.get("grado"),
        "| SECCIÓN:", a.get("seccion"),
        "| DOCENTE_ID:", a.get("docente_id")
    )

print("==============================================")
# ==========================================================
# CORREGIR ASIGNATURAS DE EVERT
# ==========================================================

ids_evert = [
    "EDFPRE3A",
    "EDF5GraA",
    "EDF6GraA",
    "EDF1AñoA"
]

resultado = db.asignaturas.update_many(
    {
        "_id": {
            "$in": ids_evert
        },
        "docente_id": "012"
    },
    {
        "$set": {
            "docente_id": "DOC012"
        }
    }
)

print("========================================")
print("🔧 CORRECCIÓN DE ASIGNATURAS DE EVERT")
print("========================================")
print("DOCUMENTOS MODIFICADOS:", resultado.modified_count)
print("========================================")