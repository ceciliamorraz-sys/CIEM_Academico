"""
diagnostico_docentes_asignaturas.py

Script de SOLO LECTURA. No modifica nada en ninguna base.

Compara las colecciones "docentes" y "asignaturas" entre tu Mongo
local y Atlas, para ver exactamente qué documentos existen en
local pero NO en Atlas (los que se perderían si corres
sincronizar_atlas_a_local.py con DRY_RUN = False, ya que ese
script dropea y reemplaza local con lo de Atlas).

Compara por _id primero. Si un documento de local no tiene su
_id en Atlas, lo muestra completo para que decidas si es basura
de pruebas o algo real que hay que rescatar.
"""

from pymongo import MongoClient

LOCAL_URI = "mongodb://localhost:27017"
ATLAS_URI = "mongodb+srv://ciemadmin:CiemAtlas2026@cluster0.olbd8g8.mongodb.net/CIEM?retryWrites=true&w=majority&appName=Cluster0"

NOMBRE_BASE_DATOS = "CIEM"

COLECCIONES_A_COMPARAR = ["docentes", "asignaturas"]


def comparar_coleccion(db_local, db_atlas, nombre):
    col_local = db_local[nombre]
    col_atlas = db_atlas[nombre]

    ids_atlas = set(doc["_id"] for doc in col_atlas.find({}, {"_id": 1}))

    docs_local = list(col_local.find({}))

    solo_en_local = [doc for doc in docs_local if doc["_id"] not in ids_atlas]

    print("=" * 60)
    print(f"Colección: {nombre}")
    print(f"  Total en local: {len(docs_local)}")
    print(f"  Total en Atlas: {len(ids_atlas)}")
    print(f"  En local pero NO en Atlas: {len(solo_en_local)}")
    print("=" * 60)

    if not solo_en_local:
        print("  (no hay documentos exclusivos de local, nada que rescatar)")
        return

    for i, doc in enumerate(solo_en_local, start=1):
        print(f"\n  --- Documento {i} (solo en local) ---")
        for clave, valor in doc.items():
            print(f"    {clave}: {valor}")


def main():
    cliente_local = MongoClient(LOCAL_URI)
    cliente_atlas = MongoClient(ATLAS_URI, tls=True, serverSelectionTimeoutMS=30000)

    db_local = cliente_local[NOMBRE_BASE_DATOS]
    db_atlas = cliente_atlas[NOMBRE_BASE_DATOS]

    for nombre in COLECCIONES_A_COMPARAR:
        comparar_coleccion(db_local, db_atlas, nombre)
        print()


if __name__ == "__main__":
    main()
