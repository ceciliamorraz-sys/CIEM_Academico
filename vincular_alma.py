# -*- coding: utf-8 -*-
"""
Paso 1: buscar al estudiante "Kayla Marcela Brown Morraz" para confirmar su codigo_estudiante.
Paso 2 (comentado, activalo despues de confirmar): vincular la cuenta 'alma' a ese codigo.
"""
from config.database import db

print("=" * 60)
print("BUSCANDO ESTUDIANTE: Kayla Marcela Brown Morraz")
print("=" * 60)

# Busqueda flexible por si el nombre esta repartido en varios campos
candidatos = list(db.estudiantes.find({
    "$or": [
        {"nombre_completo": {"$regex": "Kayla.*Brown.*Morraz", "$options": "i"}},
        {"nombre": {"$regex": "Kayla", "$options": "i"}, "apellido": {"$regex": "Brown", "$options": "i"}},
    ]
}))

if not candidatos:
    print("No se encontro ningun estudiante con ese nombre. Revisa el nombre exacto en la base.")
else:
    for est in candidatos:
        print("-" * 60)
        for campo, valor in est.items():
            print(f"{campo}: {valor}")

print("=" * 60)
print("Si el estudiante de arriba es el correcto, copia su 'codigo' (ej: CIEM-KMBM)")
print("y confirmame para activar el paso 2 (vincular la cuenta de alma).")
