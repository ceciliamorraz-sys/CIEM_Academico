"""
sincronizar_atlas_a_local.py

Copia TODAS las colecciones de tu MongoDB Atlas (la base de
producción, que ya tiene aplicadas todas las correcciones y
migraciones: cuentas de madres, padre/tutor, asignaciones de
clase, etc.) hacia tu Mongo local, para que tengas una copia
actualizada con la que desarrollar.

Por qué hace falta esto:
app.py se conecta con tls=True, lo cual indica que en realidad
tu app y tus scripts de migración (generar_cuentas_madres.py,
corregir_padre_tutor.py, completar_datos_desde_matricula.py,
migrar_asignaturas.py...) corrieron contra Atlas, no contra tu
Mongo local. Por eso local quedó desactualizado/incompleto
(pocos documentos) y Atlas es en realidad la base buena.

Este script es la dirección INVERSA del script original
sincronizar_local_a_atlas.py — aquí Atlas es el origen (fuente
de verdad) y local es el destino que se sobreescribe.

CÓMO USARLO
-----------
1. Completa LOCAL_URI, ATLAS_URI y NOMBRE_BASE_DATOS abajo.
2. Corre primero con DRY_RUN = True (no escribe nada, solo
   muestra cuántos documentos hay en cada colección en Atlas vs.
   en local, para que confirmes que tiene sentido antes de
   sobreescribir nada).
3. Si todo se ve bien, cambia DRY_RUN = False para aplicar de
   verdad. Esto reemplaza (dropea) cada colección en LOCAL y
   la vuelve a llenar con el contenido exacto de Atlas,
   preservando los mismos _id (para no romper referencias entre
   colecciones, ej. estudiante_id, docente_id, etc.).

ADVERTENCIA: la aplicación real (DRY_RUN = False) SOBREESCRIBE
por completo cada colección en LOCAL con lo que tengas en Atlas.
Cualquier dato que solo exista en local (pruebas, cambios que
hiciste ahí y no en producción) se perdería. Si crees que eso
pudo pasar, revísalo antes de aplicar de verdad.
"""

from pymongo import MongoClient

# ==========================================================
# CONFIGURACIÓN — completa esto antes de correr el script
# ==========================================================

DRY_RUN = False  # Cambia a False solo cuando ya revisaste el reporte

LOCAL_URI = "mongodb://localhost:27017"   # tu conexión local (config/database.py)
ATLAS_URI = "mongodb+srv://ciemadmin:CiemAtlas2026@cluster0.olbd8g8.mongodb.net/CIEM?retryWrites=true&w=majority&appName=Cluster0"

NOMBRE_BASE_DATOS = "CIEM"

# Colecciones a sincronizar. Si tienes alguna colección extra que
# no aparece aquí, agrégala a esta lista. (Se agregaron algunas
# vistas en el listado real de Atlas que no estaban en el script
# original: clase, clases, materiales, tareas, entregas,
# cierre_academico, comunicados, comunicaciones, mensajeria,
# horario, asignaturas_catalogo, matricula, insidencia, mensaje —
# revisa si de verdad las usas o son nombres viejos/duplicados
# antes de sincronizarlas.)
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
    cliente_atlas = MongoClient(ATLAS_URI, tls=True, serverSelectionTimeoutMS=30000)

    db_local = cliente_local[NOMBRE_BASE_DATOS]
    db_atlas = cliente_atlas[NOMBRE_BASE_DATOS]

    print("=" * 60)
    print("MODO:", "DRY RUN (solo reporte, no escribe nada)" if DRY_RUN else "APLICACIÓN REAL")
    print("Dirección: Atlas (origen) -> Local (destino, se sobreescribe)")
    print("=" * 60)

    for nombre in COLECCIONES:

        col_atlas = db_atlas[nombre]
        col_local = db_local[nombre]

        total_atlas = col_atlas.count_documents({})
        total_local_antes = col_local.count_documents({})

        print(f"\nColección: {nombre}")
        print(f"  En Atlas:  {total_atlas} documentos")
        print(f"  En local:  {total_local_antes} documentos (antes de sincronizar)")

        if total_atlas == 0:
            print("  (vacía en Atlas, se omite)")
            continue

        if DRY_RUN:
            continue

        documentos = list(col_atlas.find({}))

        col_local.drop()

        if documentos:
            col_local.insert_many(documentos)

        total_local_despues = col_local.count_documents({})
        print(f"  En local:  {total_local_despues} documentos (después de sincronizar)")

    print("\n" + "=" * 60)
    if DRY_RUN:
        print("Este fue un DRY RUN. Nada se modificó en local.")
        print("Si el reporte de arriba tiene sentido, cambia DRY_RUN = False y vuelve a correr.")
    else:
        print("Sincronización aplicada. Tu Mongo local ahora es una copia de Atlas.")
    print("=" * 60)


if __name__ == "__main__":
    main()
