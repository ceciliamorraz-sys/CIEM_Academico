# ==============================================================
# DIAGNÓSTICO (SOLO LECTURA) — no modifica nada
# ==============================================================
#
# Muestra la forma real de un par de documentos de db.estudiantes
# para confirmar en qué campo (si en alguno) quedó guardado el
# usuario de la madre/tutora en los estudiantes ya matriculados.
#
# Ejecutar:
#     python diagnostico_estudiantes.py
# ==============================================================

import json

from config.database import db


def limpiar_para_imprimir(doc):

    # Convierte tipos de Mongo (ObjectId, datetime) a texto
    # para que se pueda imprimir sin errores.

    return json.loads(
        json.dumps(doc, default=str)
    )


def diagnosticar():

    total = db.estudiantes.count_documents({})

    print(f"TOTAL estudiantes: {total}\n")

    # ----------------------------------------------------------
    # 3 estudiantes de muestra, tal cual están guardados
    # ----------------------------------------------------------

    muestra = list(
        db.estudiantes.find({}).limit(3)
    )

    for i, est in enumerate(muestra, start=1):

        print("=" * 60)
        print(f"ESTUDIANTE #{i}")
        print("=" * 60)
        print(json.dumps(
            limpiar_para_imprimir(est),
            indent=2,
            ensure_ascii=False
        ))
        print()

    # ----------------------------------------------------------
    # Conteo de qué campos relacionados a "madre" o "usuario"
    # existen entre TODOS los estudiantes
    # ----------------------------------------------------------

    con_madre_dict = db.estudiantes.count_documents({
        "madre": {"$type": "object"}
    })

    con_madre_usuario_anidado = db.estudiantes.count_documents({
        "madre.usuario": {"$exists": True, "$ne": ""}
    })

    con_madre_usuario_plano = db.estudiantes.count_documents({
        "madre_usuario": {"$exists": True, "$ne": ""}
    })

    con_usuario_plano_raiz = db.estudiantes.count_documents({
        "usuario": {"$exists": True, "$ne": ""}
    })

    print("=" * 60)
    print("CONTEOS")
    print("=" * 60)
    print(f"madre es un objeto (dict):          {con_madre_dict}")
    print(f"madre.usuario con valor:            {con_madre_usuario_anidado}")
    print(f"madre_usuario (plano) con valor:    {con_madre_usuario_plano}")
    print(f"usuario (plano, raíz) con valor:     {con_usuario_plano_raiz}")


if __name__ == "__main__":

    diagnosticar()
