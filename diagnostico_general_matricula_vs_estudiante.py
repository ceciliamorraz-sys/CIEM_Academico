# ==========================================================
# DIAGNÓSTICO GENERAL: PARA TODOS LOS ESTUDIANTES (no solo
# los 18 ya corregidos), compara padre/madre/tutor en
# "estudiantes" contra su matrícula más reciente, para ver
# si hay más casos donde la matrícula tiene datos
# (cedula/telefono/celular/ocupacion/parentesco) que nunca
# llegaron al documento del estudiante.
#
# Solo lee la base de datos, no modifica nada.
# ==========================================================

from config.database import db

CAMPOS = ["padre", "madre", "tutor"]
SUBCAMPOS = ["cedula", "telefono", "celular", "ocupacion", "parentesco"]


def como_dict(valor):
    return valor if isinstance(valor, dict) else {}


def le_falta_algo(objeto_estudiante, objeto_matricula, subcampos):
    """True si la matrícula tiene un valor no vacío en algún
    subcampo que en el estudiante está vacío."""

    for sub in subcampos:

        valor_matricula = str(objeto_matricula.get(sub, "")).strip()
        valor_estudiante = str(objeto_estudiante.get(sub, "")).strip()

        if valor_matricula and not valor_estudiante:
            return True

    return False


total_revisados = 0
total_con_diferencias = 0
codigos_con_diferencias = []

for estudiante in db.estudiantes.find({}):

    codigo = estudiante.get("_id", "???")
    nombre = estudiante.get("nombre", "(sin nombre)")

    total_revisados += 1

    matricula_mas_reciente = db.matriculas.find_one(
        {"estudiante_id": codigo},
        sort=[("fecha_creacion", -1)]
    )

    if not matricula_mas_reciente:
        continue

    diferencias = []

    for campo in CAMPOS:

        objeto_estudiante = como_dict(estudiante.get(campo))
        objeto_matricula = como_dict(matricula_mas_reciente.get(campo))

        if le_falta_algo(objeto_estudiante, objeto_matricula, SUBCAMPOS):
            diferencias.append(campo)

    if diferencias:

        total_con_diferencias += 1
        codigos_con_diferencias.append(codigo)

        print(f"\n{codigo} — {nombre}")
        print(f"    campos con datos solo en la matrícula: {', '.join(diferencias)}")


print("\n" + "=" * 70)
print(f"Estudiantes revisados: {total_revisados}")
print(f"Estudiantes con datos pendientes de traer de su matrícula: {total_con_diferencias}")

if codigos_con_diferencias:
    print("\nCódigos:")
    print(codigos_con_diferencias)
else:
    print("\nNingún estudiante tiene diferencias — todos están al día.")

print("=" * 70)
