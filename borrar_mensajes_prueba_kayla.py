"""
borrar_mensajes_prueba_kayla.py

Borra en MongoDB Atlas (producción) los mensajes y conversaciones
de prueba detectados para la estudiante Kayla Marcela Brown Morráz
(CIEM-KMBM), identificados en diagnostico_mensajes_kayla.py:

- 4 conversaciones con contenido de prueba evidente ("PRUEBA",
  "PRUEBA ERROR", "HOLITA EVERT", mensajes numéricos incrementales)
  ligadas a la cuenta huérfana "alma".
- 1 conversación más ligada a "alma" ("Evert no lleva a la niña
  esta enferma").
- 1 conversación ligada a la cuenta oficial "atorrez" con el
  mensaje "Hola", confirmada también como prueba.
- Los 6 mensajes individuales asociados a esas 6 conversaciones.

CÓMO USARLO
-----------
1. Corre primero con DRY_RUN = True (no borra nada, solo muestra
   qué documentos encontró y confirma que coinciden con lo
   esperado antes de borrar).
2. Si el reporte se ve bien, cambia DRY_RUN = False y vuelve a
   correr para borrar de verdad.
"""

from pymongo import MongoClient
from bson import ObjectId

ATLAS_URI = "mongodb+srv://ciemadmin:CiemAtlas2026@cluster0.olbd8g8.mongodb.net/CIEM?retryWrites=true&w=majority&appName=Cluster0"
NOMBRE_BASE_DATOS = "CIEM"

DRY_RUN = True  # Cambia a False solo cuando ya revisaste el reporte

CONVERSACIONES_A_BORRAR = [
    "6a68c153109b645be6876066",  # "Evert no lleva a la niña esta enferma" (alma)
    "6a729e31b158cce20e1aa355",  # "HOLITA EVERT" (alma)
    "6a7ca90fe87cdbf843db771f",  # "PRUEBA ERROR" (alma)
    "6a7d24b4624179fab25c4e91",  # "PRUEBA" (alma)
    "6a80b8b54759a4d411e5250c",  # mensajes numéricos incrementales (alma)
    "6aaf199ab490b492acc380d9",  # "Hola" (atorrez, confirmada como prueba)
]

MENSAJES_A_BORRAR = [
    "6a80b8b54759a4d411e5250d",  # "123"
    "6a80b8fab2ab7fcd6db19872",  # "1234"
    "6a80b94fb2ab7fcd6db19873",  # "12345"
    "6a80ba5f648bceb1020135aa",  # "123456"
    "6a80bad0648bceb1020135ab",  # "1234567"
    "6aaf199ab490b492acc380da",  # "Hola"
]


def main():
    cliente = MongoClient(ATLAS_URI, tls=True, serverSelectionTimeoutMS=30000)
    db = cliente[NOMBRE_BASE_DATOS]

    ids_conversaciones = [ObjectId(id_str) for id_str in CONVERSACIONES_A_BORRAR]
    ids_mensajes = [ObjectId(id_str) for id_str in MENSAJES_A_BORRAR]

    print("=" * 60)
    print("MODO:", "DRY RUN (solo reporte, no borra nada)" if DRY_RUN else "APLICACIÓN REAL")
    print("=" * 60)

    # --- conversaciones ---
    col_conversaciones = db["conversaciones"]
    encontradas = list(col_conversaciones.find({"_id": {"$in": ids_conversaciones}}))

    print(f"\nColección: conversaciones")
    print(f"  IDs a borrar: {len(ids_conversaciones)}")
    print(f"  Encontradas en Atlas ahora mismo: {len(encontradas)}")

    for doc in encontradas:
        print(f"    - {doc['_id']} | último mensaje: {doc.get('ultimo_mensaje')}")

    if not DRY_RUN:
        resultado = col_conversaciones.delete_many({"_id": {"$in": ids_conversaciones}})
        print(f"  Borradas: {resultado.deleted_count}")

    # --- mensajes ---
    col_mensajes = db["mensajes"]
    encontrados = list(col_mensajes.find({"_id": {"$in": ids_mensajes}}))

    print(f"\nColección: mensajes")
    print(f"  IDs a borrar: {len(ids_mensajes)}")
    print(f"  Encontrados en Atlas ahora mismo: {len(encontrados)}")

    for doc in encontrados:
        print(f"    - {doc['_id']} | mensaje: {doc.get('mensaje')}")

    if not DRY_RUN:
        resultado = col_mensajes.delete_many({"_id": {"$in": ids_mensajes}})
        print(f"  Borrados: {resultado.deleted_count}")

    print("\n" + "=" * 60)
    if DRY_RUN:
        print("Este fue un DRY RUN. Nada se borró.")
        print("Si el reporte de arriba tiene sentido, cambia DRY_RUN = False y vuelve a correr.")
    else:
        print("Borrado aplicado en Atlas.")
    print("=" * 60)


if __name__ == "__main__":
    main()
