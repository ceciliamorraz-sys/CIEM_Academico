import os
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    MONGO_URI = (
        "mongodb+srv://ciemadmin:CiemAtlas2026"
        "@cluster0.olbd8g.mongodb.net/CIEM"
        "?retryWrites=true&w=majority&appName=Cluster0"
    )

cliente = MongoClient(
    MONGO_URI,
    tls=True,
    serverSelectionTimeoutMS=30000
)

db = cliente["CIEM"]

print("\n========================================")
print("PRUEBA REAL DE COLECCIÓN clase")
print("========================================")

print("\nTOTAL DOCUMENTOS EN clase:")

print(
    db.clase.count_documents({})
)

print("\n========================================")
print("BUSCANDO DOC014")
print("========================================")

resultado = list(
    db.clase.find({
        "docente_id": "DOC014"
    })
)

print(
    "TOTAL DOC014:",
    len(resultado)
)

for clase in resultado:

    print("----------------------------------------")

    print("ID:", clase.get("_id"))

    print(
        "ASIGNATURA_ID:",
        clase.get("asignatura_id")
    )

    print(
        "CODIGO:",
        clase.get("codigo_asignatura")
    )

    print(
        "ASIGNATURA:",
        clase.get("asignatura")
    )

    print(
        "DOCENTE_ID:",
        clase.get("docente_id")
    )

    print(
        "DOCENTE:",
        clase.get("docente")
    )

    print(
        "NIVEL:",
        clase.get("nivel")
    )

    print(
        "GRADO:",
        clase.get("grado")
    )

    print(
        "SECCION:",
        clase.get("seccion")
    )

    print(
        "ESTADO:",
        clase.get("estado")
    )

print("\n========================================")
print("PRUEBA DOC014 + ESTADO ACTIVA")
print("========================================")

resultado_activa = list(
    db.clase.find({
        "docente_id": "DOC014",
        "estado": "Activa"
    })
)

print(
    "TOTAL:",
    len(resultado_activa)
)

for clase in resultado_activa:

    print(
        clase.get("asignatura_id"),
        "|",
        clase.get("codigo_asignatura"),
        "|",
        clase.get("asignatura"),
        "|",
        clase.get("grado"),
        "|",
        clase.get("seccion")
    )

print("\n========================================")