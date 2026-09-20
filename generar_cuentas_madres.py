# ==============================================================
# GENERAR CUENTAS PARA MADRES/TUTORAS SIN USUARIO
# ==============================================================
#
# A diferencia de migrar_cuentas_madres.py (que solo vincula un
# madre.usuario que YA estaba escrito), este script es para el
# caso real que encontramos: la mayoría de los 182 estudiantes
# tienen "madre" con todos sus datos, pero "usuario" vacío —
# nunca se escribió porque nadie lo llenó al matricular.
#
# Qué hace, por cada estudiante con madre.usuario vacío:
#
# 1. Genera un usuario a partir del nombre de la madre:
#    inicial del primer nombre + primer apellido, en minúscula
#    y sin acentos. Ej: "Karla Centeno" -> "kcenteno"
#    Si el nombre de la madre está vacío, usa el del tutor.
#    Si no hay ningún nombre disponible, salta ese estudiante
#    y lo reporta al final para revisarlo a mano.
#
# 2. Si ese usuario ya existe (choque entre dos madres con
#    inicial+apellido iguales, o hermanos), le agrega un número
#    al final (kcenteno, kcenteno2, kcenteno3...) hasta
#    encontrar uno libre — igual que se hace con el código del
#    estudiante.
#
# 3. Guarda ese usuario en madre.usuario Y en el campo plano
#    madre_usuario del estudiante.
#
# 4. Crea la cuenta en db.usuarios con una contraseña de 6
#    dígitos generada al azar, rol "padre".
#
# 5. Al final imprime la lista completa de usuario/contraseña
#    para entregar a cada familia, y aparte la lista de
#    estudiantes que se saltó por no tener ningún nombre de
#    madre/tutor disponible.
#
# No toca los estudiantes que ya tienen madre.usuario con valor
# (esos ya quedaron resueltos con migrar_cuentas_madres.py).
#
# Ejecutar UNA sola vez:
#     python generar_cuentas_madres.py
# ==============================================================

import random
import re
import unicodedata
from datetime import datetime

from config.database import db


def quitar_acentos(texto):

    texto_normalizado = unicodedata.normalize("NFKD", texto)

    return "".join(
        c for c in texto_normalizado
        if not unicodedata.combining(c)
    )


def generar_password():

    return str(
        random.randint(100000, 999999)
    )


def generar_username_base(nombre_completo):

    partes = [
        p for p in nombre_completo.strip().split()
        if p
    ]

    if not partes:
        return None

    inicial = partes[0][0]
    apellido = partes[-1]

    base = quitar_acentos(
        inicial + apellido
    ).lower()

    base = re.sub(r"[^a-z0-9]", "", base)

    return base or None


def username_disponible(candidato, usados_en_esta_corrida):

    if candidato in usados_en_esta_corrida:
        return False

    if db.usuarios.find_one({"usuario": candidato}):
        return False

    return True


def obtener_nombre_responsable(est):

    madre = est.get("madre")

    if isinstance(madre, dict):

        nombre_madre = (madre.get("nombre") or "").strip()

        if nombre_madre:
            return nombre_madre

    tutor = est.get("tutor")

    if isinstance(tutor, dict):

        nombre_tutor = (tutor.get("nombre") or "").strip()

        if nombre_tutor:
            return nombre_tutor

    elif isinstance(tutor, str) and tutor.strip():

        return tutor.strip()

    return ""


def generar():

    estudiantes = list(
        db.estudiantes.find({})
    )

    usados_en_esta_corrida = set()

    cuentas_creadas = []
    sin_nombre_disponible = []
    ya_tenian_usuario = 0

    for est in estudiantes:

        madre = est.get("madre")

        madre_usuario_actual = ""

        if isinstance(madre, dict):
            madre_usuario_actual = (
                madre.get("usuario") or ""
            ).strip()

        if madre_usuario_actual:
            ya_tenian_usuario += 1
            continue

        nombre_responsable = obtener_nombre_responsable(est)

        if not nombre_responsable:

            sin_nombre_disponible.append({
                "estudiante": est.get("nombre", ""),
                "codigo": est.get(
                    "codigo", str(est.get("_id"))
                )
            })

            continue

        base = generar_username_base(nombre_responsable)

        if not base:

            sin_nombre_disponible.append({
                "estudiante": est.get("nombre", ""),
                "codigo": est.get(
                    "codigo", str(est.get("_id"))
                )
            })

            continue

        candidato = base
        contador = 2

        while not username_disponible(
            candidato, usados_en_esta_corrida
        ):
            candidato = f"{base}{contador}"
            contador += 1

        usados_en_esta_corrida.add(candidato)

        password = generar_password()

        # ------------------------------------------------------
        # ACTUALIZAR ESTUDIANTE
        #
        # Si "madre" ya es un objeto, le agregamos el usuario.
        # Si "madre" es un texto suelto (formato viejo) o no
        # existe, lo convertimos a objeto conservando ese texto
        # como nombre. No se puede escribir "madre.usuario"
        # directamente sobre un campo que es un string — Mongo
        # lo rechaza.
        # ------------------------------------------------------

        if isinstance(madre, dict):

            madre_actualizada = dict(madre)
            madre_actualizada["usuario"] = candidato

        else:

            nombre_existente = (
                madre if isinstance(madre, str) else ""
            )

            madre_actualizada = {
                "nombre": nombre_existente,
                "cedula": "",
                "telefono": "",
                "celular": "",
                "ocupacion": "",
                "usuario": candidato
            }

        db.estudiantes.update_one(
            {"_id": est["_id"]},
            {
                "$set": {
                    "madre": madre_actualizada,
                    "madre_usuario": candidato
                }
            }
        )

        # ------------------------------------------------------
        # CREAR CUENTA
        # ------------------------------------------------------

        db.usuarios.insert_one({
            "usuario": candidato,
            "password": password,
            "rol": "padre",
            "activo": True,
            "estudiante_codigo": est.get(
                "codigo", str(est.get("_id"))
            ),
            "fecha_creacion": datetime.now()
        })

        cuentas_creadas.append({
            "estudiante": est.get("nombre", ""),
            "codigo": est.get(
                "codigo", str(est.get("_id"))
            ),
            "responsable": nombre_responsable,
            "usuario": candidato,
            "password": password
        })

    # ==========================================================
    # RESUMEN
    # ==========================================================

    print("=" * 60)
    print("GENERACIÓN DE CUENTAS DE MADRES/TUTORAS")
    print("=" * 60)
    print(f"Estudiantes revisados:        {len(estudiantes)}")
    print(f"Ya tenían usuario:            {ya_tenian_usuario}")
    print(f"Cuentas nuevas creadas:       {len(cuentas_creadas)}")
    print(f"Sin nombre disponible:        {len(sin_nombre_disponible)}")
    print("=" * 60)

    if cuentas_creadas:

        print(
            "\nCREDENCIALES NUEVAS "
            "(entregar a cada familia):\n"
        )

        for c in cuentas_creadas:

            print(
                f"  {c['estudiante']} ({c['codigo']}) "
                f"- {c['responsable']} "
                f"-> usuario: {c['usuario']}  "
                f"contraseña: {c['password']}"
            )

    if sin_nombre_disponible:

        print(
            "\nSIN NOMBRE DE MADRE/TUTOR "
            "(revisar a mano):\n"
        )

        for s in sin_nombre_disponible:

            print(
                f"  {s['estudiante']} ({s['codigo']})"
            )


if __name__ == "__main__":

    generar()
