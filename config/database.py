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


# ==========================================================
# DIAGNÓSTICO DE CONEXIÓN
# ==========================================================

print("================================================")
print("🔌 CONEXIÓN MONGODB")
print("================================================")

print(
    "MONGO_URI EXISTE:",
    bool(MONGO_URI)
)

try:

    # ------------------------------------------------------
    # PROBAR CONEXIÓN
    # ------------------------------------------------------

    cliente.admin.command("ping")

    print("✅ MONGODB CONECTADO")

    # ------------------------------------------------------
    # BASE DE DATOS
    # ------------------------------------------------------

    print(
        "🗄️ BASE DE DATOS:",
        db.name
    )

    # ------------------------------------------------------
    # COLECCIONES
    # ------------------------------------------------------

    print(
        "📂 COLECCIONES:",
        db.list_collection_names()
    )

    # ------------------------------------------------------
    # TOTAL ASIGNACIONES
    # ------------------------------------------------------

    total_asignaciones = db.asignaciones_clase.count_documents({})

    print(
        "📚 TOTAL asignaciones_clase:",
        total_asignaciones
    )

    # ------------------------------------------------------
    # TOTAL DOC014
    # ------------------------------------------------------

    total_doc014 = db.asignaciones_clase.count_documents({
        "docente_id": "DOC014"
    })

    print(
        "🔎 TOTAL DOC014:",
        total_doc014
    )

    # ------------------------------------------------------
    # MOSTRAR ASIGNACIONES DE DOC014
    # ------------------------------------------------------

    print("------------------------------------------------")
    print("📚 ASIGNACIONES DE DOC014")
    print("------------------------------------------------")

    asignaciones_doc014 = db.asignaciones_clase.find({
        "docente_id": "DOC014"
    })

    for asignacion in asignaciones_doc014:

        print(
            "ID:",
            asignacion.get("_id"),
            "| CÓDIGO:",
            asignacion.get("asignatura_codigo"),
            "| NOMBRE:",
            asignacion.get("asignatura_nombre"),
            "| ACTIVO:",
            asignacion.get("activo")
        )

    print("------------------------------------------------")

except Exception as e:

    print(
        "❌ ERROR MONGODB:",
        e
    )


print("================================================")