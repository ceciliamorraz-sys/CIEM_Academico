# ==========================================================
# MIGRACIÓN: RELLENAR asignatura_nombre Y docente_nombre
# EN NOTAS EXISTENTES
# ==========================================================
#
# Las notas guardadas ANTES del fix de guardar_notas() solo
# tienen "asignatura_id" (ObjectId como string) y "docente"
# (usuario de login) — no el nombre real de la asignatura ni
# del docente. Por eso el dashboard del estudiante mostraba
# el texto genérico "Asignatura" en vez del nombre real.
#
# Este script recorre TODAS las notas que les falte alguno
# de los dos campos, busca el dato real en "asignaciones_clase"
# (por asignatura_id) y en "docentes" (por docente_id, o si no,
# por el campo "docente" = usuario), y actualiza el documento.
#
# Es seguro correrlo varias veces: solo toca notas donde el
# campo todavía no existe o está vacío.
#
# USO:
#   python migrar_notas_nombres.py
# ==========================================================

from bson import ObjectId

from config.database import db


def _buscar_asignacion(asignatura_id):

    if not asignatura_id:
        return None

    ids_busqueda = [asignatura_id]

    try:
        ids_busqueda.append(ObjectId(asignatura_id))
    except Exception:
        pass

    asignacion = db.asignaciones_clase.find_one({
        "_id": {"$in": ids_busqueda}
    })

    if asignacion:
        return asignacion

    # ------------------------------------------------
    # LEGACY: notas viejas guardaron un CÓDIGO de
    # asignatura (ej. "INF02A") en vez del ObjectId
    # de asignaciones_clase.
    # ------------------------------------------------

    asignacion = db.asignaciones_clase.find_one({
        "asignatura_codigo": asignatura_id
    })

    if asignacion:
        return asignacion

    # ------------------------------------------------
    # ÚLTIMO RECURSO: la asignación de clase ya no
    # existe, pero el código puede seguir en el
    # catálogo de asignaturas (viejo o nuevo) — ya
    # sea como "codigo" o como el _id del documento.
    # ------------------------------------------------

    for coleccion in ("asignaturas", "asignaturas_catalogo"):

        catalogo = db[coleccion].find_one({
            "$or": [
                {"codigo": asignatura_id},
                {"_id": asignatura_id},
            ]
        })

        if catalogo and catalogo.get("nombre"):

            return {
                "asignatura_nombre": catalogo["nombre"]
            }

    return None


def _buscar_docente(docente_id, usuario):

    docente = None

    if docente_id:

        codigo_limpio = docente_id.replace(
            "DOC", ""
        ).strip()

        posibles_codigos = list(dict.fromkeys([
            docente_id,
            codigo_limpio,
            "DOC" + codigo_limpio
        ]))

        docente = db.docentes.find_one({
            "codigo": {"$in": posibles_codigos}
        })

    if not docente and usuario:

        docente = db.docentes.find_one({
            "usuario": usuario
        })

    return docente


def migrar():

    print("==========================================")
    print("🔧 MIGRANDO NOMBRES EN NOTAS")
    print("==========================================")

    filtro = {
        "$or": [
            {"asignatura_nombre": {"$exists": False}},
            {"asignatura_nombre": ""},
            {"docente_nombre": {"$exists": False}},
            {"docente_nombre": ""},
        ]
    }

    notas = list(db.notas.find(filtro))

    print("📋 NOTAS A REVISAR:", len(notas))
    print("==========================================")

    actualizadas = 0
    sin_asignatura = 0
    sin_docente = 0

    for nota in notas:

        cambios = {}

        # ------------------------------------------------
        # ASIGNATURA
        # ------------------------------------------------

        if not nota.get("asignatura_nombre"):

            asignacion = _buscar_asignacion(
                nota.get("asignatura_id")
            )

            if asignacion and asignacion.get("asignatura_nombre"):

                cambios["asignatura_nombre"] = asignacion["asignatura_nombre"]

            else:

                sin_asignatura += 1

                print(
                    "⚠️ Sin asignación encontrada para nota",
                    nota.get("_id"),
                    "| asignatura_id:",
                    nota.get("asignatura_id")
                )

        # ------------------------------------------------
        # DOCENTE
        # ------------------------------------------------

        if not nota.get("docente_nombre"):

            docente = _buscar_docente(
                nota.get("docente_id"),
                nota.get("docente")
            )

            if docente and docente.get("nombre"):

                cambios["docente_nombre"] = docente["nombre"]

            else:

                sin_docente += 1

                print(
                    "⚠️ Sin docente encontrado para nota",
                    nota.get("_id"),
                    "| docente_id:",
                    nota.get("docente_id"),
                    "| docente (usuario):",
                    nota.get("docente")
                )

        # ------------------------------------------------
        # GUARDAR CAMBIOS
        # ------------------------------------------------

        if cambios:

            db.notas.update_one(
                {"_id": nota["_id"]},
                {"$set": cambios}
            )

            actualizadas += 1

    print("==========================================")
    print("✅ NOTAS ACTUALIZADAS:", actualizadas)
    print("⚠️ SIN ASIGNATURA ENCONTRADA:", sin_asignatura)
    print("⚠️ SIN DOCENTE ENCONTRADO:", sin_docente)
    print("==========================================")


if __name__ == "__main__":
    migrar()
