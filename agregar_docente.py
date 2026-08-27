from config.database import db


# ==========================================================
# DOCENTES QUE DEBEN TENER ACCESO
# ==========================================================

docentes = [
    {
        "_id": "USR007",
        "usuario": "daniela",
        "password": "1234",
        "rol": "docente",
        "docente_id": "DOC007",
        "activo": True
    },
    {
        "_id": "USR009",
        "usuario": "anielka",
        "password": "1234",
        "rol": "docente",
        "docente_id": "DOC009",
        "activo": True
    },
    {
        "_id": "USR010",
        "usuario": "erlin",
        "password": "1234",
        "rol": "docente",
        "docente_id": "DOC010",
        "activo": True
    },
    {
        "_id": "USR011",
        "usuario": "carla",
        "password": "1234",
        "rol": "docente",
        "docente_id": "DOC011",
        "activo": True
    }
]


# ==========================================================
# INSERTAR / ACTUALIZAR
# ==========================================================

for docente in docentes:

    resultado = db.usuarios.update_one(
        {
            "_id": docente["_id"]
        },
        {
            "$set": docente
        },
        upsert=True
    )

    if resultado.upserted_id:
        print(
            "CREADO:",
            docente["usuario"],
            "→",
            docente["docente_id"]
        )
    elif resultado.modified_count:
        print(
            "ACTUALIZADO:",
            docente["usuario"],
            "→",
            docente["docente_id"]
        )
    else:
        print(
            "YA EXISTÍA:",
            docente["usuario"],
            "→",
            docente["docente_id"]
        )


# ==========================================================
# VERIFICACIÓN
# ==========================================================

print()
print("==============================================")
print("DOCENTES DISPONIBLES")
print("==============================================")

for usuario in [
    "daniela",
    "anielka",
    "erlin",
    "carla"
]:

    u = db.usuarios.find_one({
        "usuario": usuario
    })

    print(
        usuario,
        "→",
        u
    )

print("==============================================")