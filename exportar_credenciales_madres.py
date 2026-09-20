# ==============================================================
# EXPORTAR CREDENCIALES DE MADRES/TUTORAS (SOLO LECTURA)
# ==============================================================
#
# No crea ni modifica nada. Solo lee db.usuarios (rol "padre")
# y las junta con el nombre del estudiante correspondiente en
# db.estudiantes, para que tengas en un solo lugar la lista
# completa de usuario + contraseña que ya se generaron.
#
# Ejecutar:
#     python exportar_credenciales_madres.py
#
# También guarda una copia en credenciales_madres.csv para que
# la puedas abrir en Excel.
# ==============================================================

import csv

from config.database import db


def exportar():

    cuentas = list(
        db.usuarios.find({
            "rol": "padre"
        })
    )

    filas = []

    for cuenta in cuentas:

        codigo_estudiante = cuenta.get(
            "estudiante_codigo",
            ""
        )

        estudiante = db.estudiantes.find_one({
            "_id": codigo_estudiante
        })

        nombre_estudiante = (
            estudiante.get("nombre", "")
            if estudiante
            else "(no encontrado)"
        )

        filas.append({
            "estudiante": nombre_estudiante,
            "codigo_estudiante": codigo_estudiante,
            "usuario": cuenta.get("usuario", ""),
            "password": cuenta.get("password", "")
        })

    filas.sort(
        key=lambda f: f["estudiante"].lower()
    )

    print("=" * 70)
    print(f"CUENTAS DE MADRES/TUTORAS ENCONTRADAS: {len(filas)}")
    print("=" * 70)

    for f in filas:

        print(
            f"  {f['estudiante']} ({f['codigo_estudiante']}) "
            f"-> usuario: {f['usuario']}  "
            f"contraseña: {f['password']}"
        )

    # ----------------------------------------------------------
    # GUARDAR CSV
    # ----------------------------------------------------------

    with open(
        "credenciales_madres.csv",
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as archivo:

        escritor = csv.DictWriter(
            archivo,
            fieldnames=[
                "estudiante",
                "codigo_estudiante",
                "usuario",
                "password"
            ]
        )

        escritor.writeheader()
        escritor.writerows(filas)

    print("\nGuardado también en credenciales_madres.csv")


if __name__ == "__main__":

    exportar()
