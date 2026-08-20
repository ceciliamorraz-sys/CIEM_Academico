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
# ASIGNATURAS DOC012
# ==========================================================

print("------------------------------------")
print("📚 ASIGNATURAS DOC012:")

asignaturas_doc012 = list(
    db.asignaturas.find({"docente_id": "DOC012"})
)

print(
    "CANTIDAD ENCONTRADA:",
    len(asignaturas_doc012)
)

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
print("")
print("==============================================")
print("🔎 TODAS LAS ASIGNATURAS")
print("==============================================")


todas = list(
    db.asignaturas.find({})
)

print(
    "TOTAL ASIGNATURAS EN MONGO:",
    len(todas)
)

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
print(
    "DOCUMENTOS MODIFICADOS:",
    resultado.modified_count
)
print("========================================")


# ==========================================================
# CÓDIGOS ÚNICOS DE ASIGNATURAS
# ==========================================================

print("")
print("==============================================")
print("📚 CÓDIGOS ÚNICOS DE ASIGNATURAS")
print("==============================================")

codigos = db.asignaturas.distinct("codigo")

for codigo in sorted(codigos):

    print(
        codigo
    )

print("==============================================")

print(
    "TOTAL CÓDIGOS:",
    len(codigos)
)


# ==========================================================
# CREAR CATÁLOGO DE ASIGNATURAS
# ==========================================================

print("")
print("==============================================")
print("📚 CREANDO CATÁLOGO DE ASIGNATURAS")
print("==============================================")

catalogo = db.asignaturas_catalogo

registros = db.asignaturas.find({})


for registro in registros:

    codigo = str(
        registro.get("codigo", "")
    ).strip().upper()

    nombre = str(
        registro.get("nombre", "")
    ).strip()

    if not codigo or not nombre:
        continue


    # ======================================================
    # VERIFICAR SI YA EXISTE
    # ======================================================

    existe = catalogo.find_one({
        "_id": codigo
    })

    if existe:
        continue


    # ======================================================
    # CREAR ASIGNATURA EN CATÁLOGO
    # ======================================================

    catalogo.insert_one({

        "_id": codigo,

        "codigo": codigo,

        "nombre": nombre,

        "activo": True
    })

    print(
        "✅ AGREGADO:",
        codigo,
        "|",
        nombre
    )


# ==========================================================
# MOSTRAR CATÁLOGO FINAL
# ==========================================================

print("")
print("==============================================")
print("📚 CATÁLOGO FINAL")
print("==============================================")


for asignatura in catalogo.find({}).sort(
    "codigo",
    1
):

    print(
        asignatura.get("codigo"),
        "|",
        asignatura.get("nombre"),
        "| ACTIVA:",
        asignatura.get("activo")
    )


print(
    "TOTAL:",
    catalogo.count_documents({})
)

print("==============================================")


# ==========================================================
# CREAR ASIGNACIONES DE CLASE
# ==========================================================

print("")
print("==============================================")
print("👨‍🏫 CREANDO ASIGNACIONES DE CLASE")
print("==============================================")


asignaciones = db.asignaciones_clase

registros = db.asignaturas.find({})

creadas = 0
existentes = 0


for registro in registros:

    # ======================================================
    # ID DE LA ASIGNACIÓN
    # ======================================================

    asignacion_id = registro.get("_id")

    if asignacion_id is None:
        continue


    # ======================================================
    # DATOS DE LA ASIGNATURA
    # ======================================================

    codigo = str(
        registro.get("codigo", "")
    ).strip().upper()

    nombre = str(
        registro.get("nombre", "")
    ).strip()

    nivel = str(
        registro.get("nivel", "")
    ).strip()

    grado = str(
        registro.get("grado", "")
    ).strip()

    seccion = str(
        registro.get("seccion", "")
    ).strip()


    # ======================================================
    # DATOS DEL DOCENTE
    # ======================================================

    docente_id = str(
        registro.get("docente_id", "")
    ).strip().upper()

    docente_nombre = str(
        registro.get("docente_nombre", "")
    ).strip()

    tipo_docente = registro.get(
        "tipo_docente",
        "docente"
    )

    activo = registro.get(
        "activo",
        True
    )


    # ======================================================
    # VERIFICAR SI YA EXISTE
    # ======================================================

    existe = asignaciones.find_one({
        "_id": asignacion_id
    })

    if existe:

        existentes += 1

        print(
            "⚠️ YA EXISTE:",
            asignacion_id
        )

        continue


    # ======================================================
    # CREAR ASIGNACIÓN
    # ======================================================

    nueva_asignacion = {

        "_id": asignacion_id,

        "asignatura_codigo": codigo,

        "asignatura_nombre": nombre,

        "nivel": nivel,

        "grado": grado,

        "seccion": seccion,

        "docente_id": docente_id,

        "docente_nombre": docente_nombre,

        "tipo_docente": tipo_docente,

        "activo": activo
    }


    asignaciones.insert_one(
        nueva_asignacion
    )

    creadas += 1


    print(
        "✅",
        asignacion_id,
        "|",
        codigo,
        "|",
        nombre,
        "|",
        nivel,
        "|",
        grado,
        "|",
        seccion,
        "|",
        docente_id
    )


# ==========================================================
# RESUMEN DE MIGRACIÓN
# ==========================================================

print("")
print("==============================================")
print("📊 ASIGNACIONES CREADAS")
print("==============================================")


print(
    "NUEVAS:",
    creadas
)

print(
    "YA EXISTÍAN:",
    existentes
)

print(
    "TOTAL EN BD:",
    asignaciones.count_documents({})
)

print("==============================================")


# ==========================================================
# MOSTRAR ASIGNACIONES DE EVERT
# ==========================================================

print("")
print("==============================================")
print("🔎 ASIGNACIONES DE DOC012")
print("==============================================")


for asignacion in asignaciones.find({

    "docente_id": "DOC012",

    "activo": True

}).sort(
    "grado",
    1
):

    print(
        asignacion.get("_id"),
        "|",
        asignacion.get("asignatura_codigo"),
        "|",
        asignacion.get("asignatura_nombre"),
        "|",
        asignacion.get("nivel"),
        "|",
        asignacion.get("grado"),
        "|",
        asignacion.get("seccion"),
        "|",
        asignacion.get("docente_id")
    )


print("==============================================")

# ==========================================================
# REVISAR DOCENTES
# ==========================================================

print("")
print("==============================================")
print("👨‍🏫 DOCENTES REGISTRADOS EN MONGODB")
print("==============================================")

docentes = list(
    db.docentes.find({})
)

print("TOTAL DOCENTES:", len(docentes))
print("")

for docente in docentes:

    print(
        "ID:",
        docente.get("_id"),
        "| CÓDIGO:",
        docente.get("codigo"),
        "| NOMBRE:",
        docente.get("nombre"),
        "| TIPO:",
        docente.get("tipo_docente")
    )

print("==============================================")

# ==========================================================
# 🔎 REVISAR ESTRUCTURA DE ASIGNACIONES
# ==========================================================

print("")
print("==============================================")
print("🔎 ESTRUCTURA DE ASIGNACIONES_CLASE")
print("==============================================")

for asignacion in db.asignaciones_clase.find({}).limit(5):

    print("----------------------------------------------")
    print(asignacion)

print("==============================================")