# -*- coding: utf-8 -*-
from config.database import db

print("=" * 60)
print("CUENTA CORRECTA: atorrez (madre de Kayla Marcela Brown Morraz)")
print("=" * 60)
correcta = db.usuarios.find_one({"usuario": "atorrez"})
if correcta:
    for campo, valor in correcta.items():
        print(f"{campo}: {valor}")
else:
    print("No se encontro la cuenta 'atorrez' en db.usuarios (raro, revisar).")

print()
print("=" * 60)
print("CUENTA HUERFANA A BORRAR: alma")
print("=" * 60)
huerfana = db.usuarios.find_one({"usuario": "alma"})
if huerfana:
    for campo, valor in huerfana.items():
        print(f"{campo}: {valor}")
else:
    print("No se encontro la cuenta 'alma' (puede que ya se haya borrado).")

print()
print("=" * 60)
print("Si arriba 'atorrez' tiene contrasena y esta bien, y 'alma' es")
print("efectivamente la huerfana sin estudiante vinculado, corre")
print("el siguiente script para borrarla: python borrar_alma.py")
print("=" * 60)
