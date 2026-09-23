# ==========================================================
# DIAGNÓSTICO: ESTUDIANTES CON padre/madre/tutor/
# informacion_linguistica GUARDADOS COMO ALGO DISTINTO A
# UN OBJETO (dict) — CAUSA DEL ERROR 500 EN
# /admin/api/estudiante/<codigo>
#
# Solo lee la base de datos, no modifica nada.
# ==========================================================

from config.database import db

CAMPOS_A_REVISAR = [
    "padre",
    "madre",
    "tutor",
    "informacion_linguistica"
]

estudiantes_con_problema = []

for estudiante in db.estudiantes.find({}):

    codigo = estudiante.get("_id", "???")
    nombre = estudiante.get("nombre", "(sin nombre)")

    campos_malos = []

    for campo in CAMPOS_A_REVISAR:

        valor = estudiante.get(campo)

        # None o ausente está bien (el código ya lo maneja).
        # Lo que rompe la API es cualquier valor presente
        # que NO sea un diccionario (típicamente un string).
        if valor is not None and not isinstance(valor, dict):

            campos_malos.append(
                f"{campo} = {valor!r} (tipo: {type(valor).__name__})"
            )

    if campos_malos:
        estudiantes_con_problema.append(
            (codigo, nombre, campos_malos)
        )


print("=" * 70)
print(f"Estudiantes revisados: {db.estudiantes.count_documents({})}")
print(f"Estudiantes con campos mal guardados: {len(estudiantes_con_problema)}")
print("=" * 70)

for codigo, nombre, campos_malos in estudiantes_con_problema:

    print(f"\n{codigo} — {nombre}")

    for detalle in campos_malos:
        print(f"    {detalle}")

if not estudiantes_con_problema:
    print("\nNo se encontró ningún estudiante con este problema.")
