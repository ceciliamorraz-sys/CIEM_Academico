# -*- coding: utf-8 -*-
from config.database import db

print("=" * 60)
print("EJEMPLO DE UN DOCUMENTO DE 'notas'")
print("=" * 60)
ejemplo_nota = db.notas.find_one()
if ejemplo_nota:
    for campo, valor in ejemplo_nota.items():
        print(f"{campo}: {valor}")
else:
    print("La coleccion 'notas' esta vacia.")

print()
print("=" * 60)
print("EJEMPLO DE UN DOCUMENTO DE 'asistencias'")
print("=" * 60)
ejemplo_asistencia = db.asistencias.find_one()
if ejemplo_asistencia:
    for campo, valor in ejemplo_asistencia.items():
        print(f"{campo}: {valor}")
else:
    print("La coleccion 'asistencias' esta vacia.")

print()
print("=" * 60)
print("TOTAL de notas y asistencias en el sistema")
print("=" * 60)
print("Total notas:", db.notas.count_documents({}))
print("Total asistencias:", db.asistencias.count_documents({}))

print()
print("=" * 60)
print("EJEMPLO DE UN DOCUMENTO DE 'asignaciones_clase' (para ver campos de referencia)")
print("=" * 60)
ejemplo_asignacion = db.asignaciones_clase.find_one()
if ejemplo_asignacion:
    for campo, valor in ejemplo_asignacion.items():
        print(f"{campo}: {valor}")
