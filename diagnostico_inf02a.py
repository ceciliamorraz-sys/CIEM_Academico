# ==========================================================
# DIAGNÓSTICO: NOTAS HUÉRFANAS CON asignatura_id = "INF02A"
# ==========================================================
#
# Este script NO modifica nada. Solo muestra información para
# decidir qué hacer con las 21 notas que quedaron sin
# asignatura_nombre.
#
# USO:
#   python diagnostico_inf02a.py
# ==========================================================

import re

from config.database import db


print("==========================================")
print("📋 NOTAS CON asignatura_id = INF02A")
print("==========================================")

notas = list(
    db.notas.find({
        "asignatura_id": "INF02A"
    })
)

print("TOTAL:", len(notas))
print("")

for nota in notas:

    print(
        "ID:", nota.get("_id"),
        "| estudiante_id:", nota.get("estudiante_id"),
        "| grado:", nota.get("grado"),
        "| seccion:", nota.get("seccion"),
        "| periodo:", nota.get("periodo"),
        "| evaluacion:", nota.get("evaluacion"),
        "| docente_id:", nota.get("docente_id"),
        "| docente_nombre:", nota.get("docente_nombre")
    )

print("")
print("==========================================")
print("🔎 BUSCANDO 'INF' EN asignaciones_clase")
print("==========================================")

for a in db.asignaciones_clase.find({
    "$or": [
        {"asignatura_codigo": {"$regex": "INF", "$options": "i"}},
        {"asignatura_nombre": {"$regex": "inform", "$options": "i"}},
    ]
}):
    print(
        "ID:", a.get("_id"),
        "| codigo:", a.get("asignatura_codigo"),
        "| nombre:", a.get("asignatura_nombre"),
        "| grado:", a.get("grado"),
        "| seccion:", a.get("seccion"),
        "| docente_id:", a.get("docente_id"),
        "| activo:", a.get("activo")
    )

print("")
print("==========================================")
print("🔎 BUSCANDO 'INF' EN asignaturas")
print("==========================================")

for a in db.asignaturas.find({
    "$or": [
        {"codigo": {"$regex": "INF", "$options": "i"}},
        {"nombre": {"$regex": "inform", "$options": "i"}},
    ]
}):
    print(
        "ID:", a.get("_id"),
        "| codigo:", a.get("codigo"),
        "| nombre:", a.get("nombre")
    )

print("")
print("==========================================")
print("🔎 BUSCANDO 'INF' EN asignaturas_catalogo")
print("==========================================")

for a in db.asignaturas_catalogo.find({
    "$or": [
        {"codigo": {"$regex": "INF", "$options": "i"}},
        {"nombre": {"$regex": "inform", "$options": "i"}},
    ]
}):
    print(
        "ID:", a.get("_id"),
        "| codigo:", a.get("codigo"),
        "| nombre:", a.get("nombre")
    )

print("")
print("==========================================")
print("FIN DEL DIAGNÓSTICO")
print("==========================================")
