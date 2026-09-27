"""
sincronizar_local_a_atlas.py

Copia TODAS las colecciones de tu MongoDB local (la que tiene ya
aplicadas todas las correcciones: cuentas de madres, padre/tutor,
asignaciones de clase, etc.) hacia tu base en MongoDB Atlas (la
que usa Render en producción).

Por qué hace falta esto:
Subiste la base a Atlas ANTES de correr los scripts de migración
(generar_cuentas_madres.py, corregir_padre_tutor.py,
completar_datos_desde_matricula.py, migrar_asignaturas.py...).
Esos scripts corrieron contra tu Mongo local, así que Atlas se
quedó desactualizado (por eso localmente "atorrez" funciona pero
en Render no).

CÓMO USARLO
-----------
1. Completa LOCAL_URI, ATLAS_URI y NOMBRE_BASE_DATOS abajo.
2. Corre primero con DRY_RUN = True (no escribe nada, solo
   muestra cuántos documentos hay en cada colección en local vs.
   en Atlas, para que confirmes que tiene sentido antes de
   sobreescribir nada).
3. Si todo se ve bien, cambia DRY_RUN = False para aplicar de
   verdad. Esto reemplaza (dropea) cada colección en Atlas y
   la vuelve a llenar con el contenido exacto de tu local,
   preservando los mismos _id (para no romper referencias entre
   colecciones, ej. estudiante_id, docente_id, etc.).

ADVERTENCIA: la aplicación real (DRY_RUN = False) SOBREESCRIBE
por completo cada colección en Atlas con lo que tengas en local.
Si en Atlas ya hay datos nuevos que no existen en tu local (por
ejemplo, algo que se registró en producción y no en tu máquina),
esos datos se perderían. Si crees que eso pudo pasar, avísame
antes de aplicar de verdad.
"""

from pymongo import MongoClient

# ==========================================================
# CONFIGURACIÓN — completa esto antes de correr el script
# ==========================================================

DRY_RUN = True  # Cambia a False solo cuando ya revisaste el reporte

LOCAL_URI = "mongodb://localhost:27017"   # tu conexión local (config/database.py)
ATLAS_URI = "mongodb+srv://ciemadmin:CiemAtlas2026@cluster0.olbd8g8.mongodb.net/CIEM?retryWrites=true&w=majority&appName=Cluster0"

NOMBRE_BASE_DATOS = "CIEM"  # ej. "ciem_academico"

# Colecciones a sincronizar. Si tienes alguna colección extra que
# no aparece aquí, agrégala a esta lista.
COLECCIONES = [
    "usuarios",
    "estudiantes",
    "docentes",
    "asignaturas",
    "asignaciones_clase",
    "notas",
    "asistencias",
    "incidencias",
    "matriculas",
    "mensajes",
    "conversaciones",
    "avisos",
    # GridFS de los planes de clase subidos por docentes:
    "planes_clase.files",
    "planes_clase.chunks",
]


def main():

    cliente_local = MongoClient(LOCAL_URI)
    cliente_atlas = MongoClient(ATLAS_URI)

    db_local = cliente_local[NOMBRE_BASE_DATOS]
    db_atlas = cliente_atlas[NOMBRE_BASE_DATOS]

    print("=" * 60)
    print("MODO:", "DRY RUN (solo reporte, no escribe nada)" if DRY_RUN else "APLICACIÓN REAL")
    print("=" * 60)

    for nombre in COLECCIONES:

        col_local = db_local[nombre]
        col_atlas = db_atlas[nombre]

        total_local = col_local.count_documents({})
        total_atlas_antes = col_atlas.count_documents({})

        print(f"\nColección: {nombre}")
        print(f"  En local:  {total_local} documentos")
        print(f"  En Atlas:  {total_atlas_antes} documentos (antes de sincronizar)")

        if total_local == 0:
            print("  (vacía en local, se omite)")
            continue

        if DRY_RUN:
            continue

        documentos = list(col_local.find({}))

        col_atlas.drop()

        if documentos:
            col_atlas.insert_many(documentos)

        total_atlas_despues = col_atlas.count_documents({})
        print(f"  En Atlas:  {total_atlas_despues} documentos (después de sincronizar)")

    print("\n" + "=" * 60)
    if DRY_RUN:
        print("Este fue un DRY RUN. Nada se modificó en Atlas.")
        print("Si el reporte de arriba tiene sentido, cambia DRY_RUN = False y vuelve a correr.")
    else:
        print("Sincronización aplicada. Revisa en Render que 'atorrez' ya funcione.")
    print("=" * 60)


if __name__ == "__main__":
    main()
