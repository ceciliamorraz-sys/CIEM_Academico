import os
from pymongo import MongoClient

# ==========================================================
# CONEXIÓN
# ==========================================================

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    MONGO_URI = (
        "mongodb+srv://ciemadmin:CiemAtlas2026"
        "@cluster0.olbd8g8.mongodb.net/CIEM"
        "?retryWrites=true&w=majority&appName=Cluster0"
    )

cliente = MongoClient(
    MONGO_URI,
    tls=True,
    serverSelectionTimeoutMS=30000
)

db = cliente["CIEM"]

print("==============================================")
print("🔄 MIGRACIÓN DE ASIGNATURAS")
print("==============================================")


# ==========================================================
# COLECCIONES
# ==========================================================

coleccion_actual = db.asignaturas

catalogo = db.asignaturas_catalogo

asignaciones = db.asignaciones_clase


# ==========================================================
# 1. LEER ASIGNATURAS ACTUALES
# ==========================================================

registros = list(
    coleccion_actual.find({})
)

print(
    "📚 REGISTROS ACTUALES:",
    len(registros)
)


# ==========================================================
# 2. CREAR CATÁLOGO DE ASIGNATURAS
# ==========================================================

catalogo_creado = 0


for registro in registros:

    codigo = str(
        registro.get("codigo", "")
    ).strip().upper()

    nombre = str(
        registro.get("nombre", "")
    ).strip()

    if not codigo:
        continue

    # Si ya existe, no lo duplicamos
    existente = catalogo.find_one({
        "_id": codigo
    })

    if existente:
        continue

    documento_catalogo = {

        "_id": codigo,

        "codigo": codigo,

        "nombre": nombre,

        "activo": True
    }

    catalogo.insert_one(
        documento_catalogo
    )

    catalogo_creado += 1

    print(
        "✅ CATÁLOGO:",
        codigo,
        "|",
        nombre
    )


# ==========================================================
# 3. CREAR ASIGNACIONES DE CLASE
# ==========================================================

asignaciones_creadas = 0


for registro in registros:

    asignacion_id = registro.get("_id")

    if asignacion_id is None:
        continue

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
    # EVITAR DUPLICADOS
    # ======================================================

    existente = asignaciones.find_one({
        "_id": asignacion_id
    })

    if existente:
        print(
            "⚠️ YA EXISTE:",
            asignacion_id
        )

        continue


    # ======================================================
    # NUEVA ASIGNACIÓN
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

    asignaciones_creadas += 1


    print(
        "✅ ASIGNACIÓN:",
        asignacion_id,
        "|",
        codigo,
        "|",
        grado,
        "|",
        seccion,
        "|",
        docente_id
    )


# ==========================================================
# 4. RESUMEN
# ==========================================================

print("")
print("==============================================")
print("📊 MIGRACIÓN TERMINADA")
print("==============================================")

print(
    "ASIGNATURAS EN CATÁLOGO:",
    catalogo.count_documents({})
)

print(
    "NUEVAS ASIGNATURAS CREADAS:",
    catalogo_creado
)

print(
    "ASIGNACIONES DE CLASE:",
    asignaciones.count_documents({})
)

print(
    "NUEVAS ASIGNACIONES CREADAS:",
    asignaciones_creadas
)

print("==============================================")


# ==========================================================
# 5. MOSTRAR CATÁLOGO
# ==========================================================

print("")
print("==============================================")
print("📚 CATÁLOGO")
print("==============================================")


for materia in catalogo.find({}).sort(
    "codigo",
    1
):

    print(
        materia.get("codigo"),
        "|",
        materia.get("nombre"),
        "| ACTIVA:",
        materia.get("activo")
    )


# ==========================================================
# 6. MOSTRAR ASIGNACIONES
# ==========================================================

print("")
print("==============================================")
print("👨‍🏫 ASIGNACIONES DE CLASE")
print("==============================================")


for asignacion in asignaciones.find({}).sort(
    "docente_id",
    1
):

    print(
        asignacion.get("_id"),
        "|",
        asignacion.get("asignatura_codigo"),
        "|",
        asignacion.get("asignatura_nombre"),
        "|",
        asignacion.get("grado"),
        "|",
        asignacion.get("seccion"),
        "| DOCENTE:",
        asignacion.get("docente_id")
    )


print("")
print("==============================================")
print("✅ NO SE ELIMINÓ NINGÚN REGISTRO")
print("==============================================")