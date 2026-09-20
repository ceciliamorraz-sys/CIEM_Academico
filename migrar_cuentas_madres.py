# ==============================================================
# MIGRACIÓN ÚNICA: cuentas de acceso para madres/tutoras
# ==============================================================
#
# Por qué hace falta:
#
# Antes del arreglo, la matrícula guardaba el usuario deseado de
# la madre solo dentro de "madre": {"usuario": ...}, nunca como
# campo plano "madre_usuario", y nunca creaba la cuenta real en
# db.usuarios. Eso significa que TODOS los estudiantes matriculados
# antes de hoy no tienen manera de que su madre/tutora inicie
# sesión, aunque el arreglo en app.py ya funcione para matrículas
# nuevas.
#
# Qué hace este script:
#
# 1. Recorre todos los documentos de db.estudiantes.
# 2. Si tienen madre.usuario pero les falta el campo plano
#    madre_usuario, lo agrega.
# 3. Si ese usuario todavía no tiene cuenta en db.usuarios, la
#    crea con rol "padre" y una contraseña de 6 dígitos generada
#    al azar.
# 4. Si el usuario YA tiene cuenta (por ejemplo, dos hermanos con
#    la misma madre), no toca nada — evita duplicar cuentas.
# 5. Al final imprime la lista de credenciales nuevas para que
#    se las entregues a cada familia.
#
# Cómo ejecutarlo (UNA sola vez, desde la carpeta del proyecto):
#
#     python migrar_cuentas_madres.py
#
# Es seguro volver a correrlo por accidente: los estudiantes que
# ya quedaron migrados simplemente se saltan (no se generan
# contraseñas nuevas ni cuentas duplicadas).
# ==============================================================

import random
from datetime import datetime

from config.database import db


def generar_password():

    return str(
        random.randint(100000, 999999)
    )


def migrar():

    estudiantes = list(
        db.estudiantes.find({})
    )

    total_estudiantes = len(estudiantes)

    campo_agregado = 0
    cuentas_creadas = 0
    sin_madre_usuario = 0
    ya_tenian_cuenta = 0

    credenciales_generadas = []

    for est in estudiantes:

        madre = est.get("madre")

        if not isinstance(madre, dict):

            # Registros antiguos donde "madre" es un texto
            # suelto (el nombre) en vez del formato con
            # sub-campos. No hay usuario que migrar aquí.

            madre = {}

        madre_usuario = (
            madre.get("usuario") or ""
        ).strip()

        # ----------------------------------------------------
        # SIN USUARIO DE MADRE REGISTRADO: nada que migrar
        # ----------------------------------------------------

        if not madre_usuario:

            sin_madre_usuario += 1

            continue

        # ----------------------------------------------------
        # 1. ASEGURAR EL CAMPO PLANO madre_usuario
        # ----------------------------------------------------

        if est.get("madre_usuario") != madre_usuario:

            db.estudiantes.update_one(
                {"_id": est["_id"]},
                {"$set": {"madre_usuario": madre_usuario}}
            )

            campo_agregado += 1

        # ----------------------------------------------------
        # 2. ASEGURAR LA CUENTA EN db.usuarios
        # ----------------------------------------------------

        cuenta = db.usuarios.find_one({
            "usuario": madre_usuario
        })

        if cuenta:

            ya_tenian_cuenta += 1

            continue

        password = generar_password()

        db.usuarios.insert_one({
            "usuario": madre_usuario,
            "password": password,
            "rol": "padre",
            "activo": True,
            "estudiante_codigo": est.get(
                "codigo",
                str(est.get("_id"))
            ),
            "fecha_creacion": datetime.now()
        })

        cuentas_creadas += 1

        credenciales_generadas.append({
            "estudiante": est.get("nombre", ""),
            "codigo": est.get(
                "codigo",
                str(est.get("_id"))
            ),
            "usuario": madre_usuario,
            "password": password
        })

    # ==========================================================
    # RESUMEN
    # ==========================================================

    print("=" * 60)
    print("MIGRACIÓN DE CUENTAS DE MADRES/TUTORAS")
    print("=" * 60)
    print(f"Estudiantes revisados:        {total_estudiantes}")
    print(f"Sin usuario de madre:         {sin_madre_usuario}")
    print(f"Campo madre_usuario corregido:{campo_agregado}")
    print(f"Ya tenían cuenta:             {ya_tenian_cuenta}")
    print(f"Cuentas nuevas creadas:       {cuentas_creadas}")
    print("=" * 60)

    if credenciales_generadas:

        print(
            "\nCREDENCIALES NUEVAS "
            "(entregar a cada familia):\n"
        )

        for c in credenciales_generadas:

            print(
                f"  {c['estudiante']} ({c['codigo']}) "
                f"-> usuario: {c['usuario']}  "
                f"contraseña: {c['password']}"
            )

    else:

        print(
            "\nNo se generaron cuentas nuevas "
            "(todas ya estaban al día)."
        )


if __name__ == "__main__":

    migrar()
