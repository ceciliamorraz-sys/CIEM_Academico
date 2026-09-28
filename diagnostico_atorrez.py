"""
Diagnóstico de solo lectura: revisa todos los documentos en
db.usuarios que coincidan con "atorrez" (sin importar mayúsculas),
para detectar duplicados, contraseña real guardada, rol y estado.

No modifica nada en la base de datos.
"""

from config.database import db

usuario_buscado = "atorrez"

print(f'Buscando todos los documentos con usuario ~= "{usuario_buscado}"...\n')

resultados = list(
    db.usuarios.find({
        "usuario": {"$regex": f"^{usuario_buscado}$", "$options": "i"}
    })
)

if not resultados:
    print("No se encontró NINGÚN documento con ese usuario.")
else:
    print(f"Se encontraron {len(resultados)} documento(s):\n")
    for i, doc in enumerate(resultados, start=1):
        print(f"--- Documento {i} ---")
        for campo, valor in doc.items():
            if campo == "password":
                print(f"  password: {repr(valor)}  (tipo: {type(valor).__name__}, len: {len(str(valor))})")
            else:
                print(f"  {campo}: {repr(valor)}")
        print()
