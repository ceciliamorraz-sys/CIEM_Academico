# ==========================================================
# EXPORTAR CREDENCIALES: DOCENTES Y PADRES
#
# Script de SOLO LECTURA. No modifica nada en la base de
# datos — únicamente lee las cuentas ya existentes en
# db.usuarios (rol "docente" y rol "padre") y las exporta a
# dos archivos CSV con su usuario, contraseña y una referencia
# (nombre del docente, o estudiante + madre/tutor) para que
# sepas a quién corresponde cada cuenta.
#
# Ejecutar desde la raíz del proyecto:
#   python exportar_credenciales_docentes_padres.py
#
# Genera:
#   credenciales_docentes.csv
#   credenciales_padres.csv
# ==========================================================

import csv
from config.database import db


# ==========================================================
# DOCENTES
# ==========================================================

usuarios_docentes = list(
    db.usuarios.find({"rol": "docente"})
)

with open(
    "credenciales_docentes.csv",
    "w",
    newline="",
    encoding="utf-8-sig"
) as _archivo:

    _escritor = csv.writer(_archivo)

    _escritor.writerow([
        "docente_id",
        "nombre",
        "usuario",
        "password",
        "activo"
    ])

    for _u in usuarios_docentes:

        _docente = db.docentes.find_one({
            "codigo": _u.get("docente_id", "")
        })

        _nombre = _docente.get("nombre", "") if _docente else ""

        _escritor.writerow([
            _u.get("docente_id", ""),
            _nombre,
            _u.get("usuario", ""),
            _u.get("password", ""),
            "Sí" if _u.get("activo", True) else "No"
        ])

print(
    f"{len(usuarios_docentes)} cuentas de docentes exportadas "
    f"a credenciales_docentes.csv"
)


# ==========================================================
# PADRES / MADRES / TUTORES
# ==========================================================

usuarios_padres = list(
    db.usuarios.find({"rol": "padre"})
)

with open(
    "credenciales_padres.csv",
    "w",
    newline="",
    encoding="utf-8-sig"
) as _archivo:

    _escritor = csv.writer(_archivo)

    _escritor.writerow([
        "estudiante_codigo",
        "estudiante_nombre",
        "nombre_madre_o_tutor",
        "usuario",
        "password",
        "activo"
    ])

    for _u in usuarios_padres:

        _estudiante = db.estudiantes.find_one({
            "codigo": _u.get("estudiante_codigo", "")
        })

        _nombre_estudiante = ""
        _nombre_referencia = ""

        if _estudiante:

            _nombre_estudiante = _estudiante.get("nombre", "")

            _madre = _estudiante.get("madre", {}) or {}
            _tutor = _estudiante.get("tutor", {}) or {}

            if _madre.get("usuario") == _u.get("usuario"):
                _nombre_referencia = _madre.get("nombre", "")
            elif _tutor.get("usuario") == _u.get("usuario"):
                _nombre_referencia = _tutor.get("nombre", "")

        _escritor.writerow([
            _u.get("estudiante_codigo", ""),
            _nombre_estudiante,
            _nombre_referencia,
            _u.get("usuario", ""),
            _u.get("password", ""),
            "Sí" if _u.get("activo", True) else "No"
        ])

print(
    f"{len(usuarios_padres)} cuentas de padres/madres exportadas "
    f"a credenciales_padres.csv"
)
