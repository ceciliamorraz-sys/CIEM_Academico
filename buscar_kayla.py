# -*- coding: utf-8 -*-
from config.database import db

print("=" * 60)
print("EJEMPLO DE UN DOCUMENTO DE 'estudiantes' (para ver los campos)")
print("=" * 60)
ejemplo = db.estudiantes.find_one()
if ejemplo:
    for campo, valor in ejemplo.items():
        print(f"{campo}: {valor}")
else:
    print("La coleccion 'estudiantes' esta vacia.")

print()
print("=" * 60)
print("BUSQUEDA AMPLIA por 'Kayla' O 'Brown' O 'Morraz' en CUALQUIER campo de texto")
print("=" * 60)

partes = ["Kayla", "Brown", "Morraz", "Marcela"]
vistos = set()

for parte in partes:
    # Busca la palabra en cualquier campo del documento, sin importar el nombre del campo
    resultados = list(db.estudiantes.find({
        "$or": [
            {campo: {"$regex": parte, "$options": "i"}}
            for campo in (ejemplo.keys() if ejemplo else [])
            if isinstance(ejemplo.get(campo), str)
        ]
    }))
    for est in resultados:
        _id = str(est.get("_id"))
        if _id not in vistos:
            vistos.add(_id)
            print("-" * 60)
            print(f"(coincidio con: '{parte}')")
            for campo, valor in est.items():
                print(f"{campo}: {valor}")

if not vistos:
    print("Ningun estudiante coincidio ni siquiera parcialmente.")
    print("Revisa el 'EJEMPLO' de arriba para confirmar los nombres de campo reales,")
    print("y si el nombre de Kayla esta escrito distinto en la base.")

print("=" * 60)
