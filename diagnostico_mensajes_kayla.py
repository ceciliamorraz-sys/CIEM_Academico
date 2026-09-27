"""
diagnostico_mensajes_kayla.py

Script de SOLO LECTURA. No borra ni modifica nada.

Busca en las colecciones "mensajes" y "conversaciones" (en Atlas,
la base de producción) cualquier documento relacionado con la
estudiante Kayla Marcela Brown Morráz (código CIEM-KMBM), para
que puedas revisar cuáles son de prueba antes de borrarlos.

Busca por varios campos posibles ya que no sabemos con certeza
cuál usa cada colección para identificar al estudiante:
nombre, estudiante, estudiante_nombre, remitente, destinatario,
estudiante_codigo, etc. También hace una búsqueda de texto libre
en TODOS los campos string de cada documento, por si el nombre
aparece en un campo que no esperamos.
"""

from pymongo import MongoClient

ATLAS_URI = "mongodb+srv://ciemadmin:CiemAtlas2026@cluster0.olbd8g8.mongodb.net/CIEM?retryWrites=true&w=majority&appName=Cluster0"
NOMBRE_BASE_DATOS = "CIEM"

TERMINOS_BUSQUEDA = ["kayla", "brown", "ciem-kmbm"]

COLECCIONES_A_REVISAR = ["mensajes", "conversaciones"]


def documento_coincide(doc, terminos):
    for valor in doc.values():
        texto = str(valor).lower()
        for termino in terminos:
            if termino in texto:
                return True
    return False


def main():
    cliente = MongoClient(ATLAS_URI, tls=True, serverSelectionTimeoutMS=30000)
    db = cliente[NOMBRE_BASE_DATOS]

    for nombre_coleccion in COLECCIONES_A_REVISAR:

        col = db[nombre_coleccion]
        total = col.count_documents({})

        print("=" * 60)
        print(f"Colección: {nombre_coleccion} (total: {total} documentos)")
        print("=" * 60)

        encontrados = []

        for doc in col.find({}):
            if documento_coincide(doc, TERMINOS_BUSQUEDA):
                encontrados.append(doc)

        print(f"Coincidencias con Kayla Marcela Brown: {len(encontrados)}\n")

        for i, doc in enumerate(encontrados, start=1):
            print(f"  --- Documento {i} ---")
            for clave, valor in doc.items():
                print(f"    {clave}: {valor}")
            print()


if __name__ == "__main__":
    main()
