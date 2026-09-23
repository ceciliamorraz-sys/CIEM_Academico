# ==========================================================
# DIAGNÓSTICO: ¿LOS DATOS COMPLETOS DE padre/madre/tutor
# (cédula, teléfono, celular, ocupación) ESTÁN GUARDADOS EN
# LA MATRÍCULA AUNQUE NO ESTÉN EN EL ESTUDIANTE?
#
# Para cada uno de los 18 códigos afectados, busca su
# matrícula más reciente y compara padre/madre/tutor ahí
# contra lo que quedó en estudiantes tras la corrección.
#
# Solo lee la base de datos, no modifica nada.
# ==========================================================

from config.database import db

CODIGOS_AFECTADOS = [
    "CIEM-ALGJ", "CIEM-BBRG", "CIEM-CSGC", "CIEM-DCGL",
    "CIEM-JDCB", "CIEM-JJAV", "CIEM-JJMM", "CIEM-JOOL",
    "CIEM-KMBM", "CIEM-KMFP", "CIEM-LATN", "CIEM-LJZU",
    "CIEM-LRVM", "CIEM-MNBT", "CIEM-NDPD", "CIEM-PAMS",
    "CIEM-SOGC", "CIEM-LDCP"
]

CAMPOS = ["padre", "madre", "tutor"]
SUBCAMPOS_A_REVISAR = ["cedula", "telefono", "celular", "ocupacion"]


def tiene_datos_extra(objeto):
    """True si al menos uno de cedula/telefono/celular/ocupacion
    tiene algo distinto de vacío."""

    if not isinstance(objeto, dict):
        return False

    for sub in SUBCAMPOS_A_REVISAR:
        if str(objeto.get(sub, "")).strip():
            return True

    return False


for codigo in CODIGOS_AFECTADOS:

    estudiante = db.estudiantes.find_one({"_id": codigo})

    matricula_mas_reciente = db.matriculas.find_one(
        {"estudiante_id": codigo},
        sort=[("fecha_creacion", -1)]
    )

    print(f"\n{'=' * 70}")
    print(f"{codigo} — {estudiante.get('nombre', '???') if estudiante else '(sin estudiante)'}")
    print(f"{'=' * 70}")

    if not matricula_mas_reciente:
        print("  No se encontró ninguna matrícula para este estudiante.")
        continue

    for campo in CAMPOS:

        objeto_estudiante = (estudiante or {}).get(campo, {})
        objeto_matricula = matricula_mas_reciente.get(campo, {})

        extra_en_estudiante = tiene_datos_extra(objeto_estudiante)
        extra_en_matricula = tiene_datos_extra(objeto_matricula)

        estado = (
            "✅ ya completo en estudiante" if extra_en_estudiante else
            "📋 datos completos SOLO en matrícula — se pueden copiar" if extra_en_matricula else
            "— sin datos extra en ninguno de los dos"
        )

        print(f"  {campo}: {estado}")

        if extra_en_matricula and not extra_en_estudiante:
            print(f"      matrícula: {objeto_matricula}")
