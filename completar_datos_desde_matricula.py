# ==========================================================
# CORRECCIÓN: TRAER cedula/telefono/celular/ocupacion (y
# parentesco de tutor) DESDE LA MATRÍCULA MÁS RECIENTE DE
# CADA ESTUDIANTE, PARA LOS CASOS DONDE EL ESTUDIANTE SE
# QUEDÓ SOLO CON EL NOMBRE.
#
# Regla de combinación: para cada subcampo (cedula, telefono,
# celular, ocupacion, parentesco), si la matrícula tiene un
# valor no vacío, se usa ese. Si la matrícula no lo tiene, se
# conserva lo que ya haya en el estudiante. El nombre nunca
# se toca (ya está correcto en ambos lados).
#
# No se copian campos ajenos al estudiante (como "usuario"
# dentro de madre, que es propio del documento de matrícula).
#
# ==========================================================
# MODO DE PRUEBA POR DEFECTO — con DRY_RUN = True solo
# imprime qué cambiaría, sin tocar la base de datos.
# ==========================================================

DRY_RUN = False

from config.database import db

CODIGOS_AFECTADOS = [
    "CIEM-ALGJ", "CIEM-BBRG", "CIEM-CSGC", "CIEM-DCGL",
    "CIEM-JDCB", "CIEM-JJAV", "CIEM-JJMM", "CIEM-JOOL",
    "CIEM-KMBM", "CIEM-KMFP", "CIEM-LATN", "CIEM-LJZU",
    "CIEM-LRVM", "CIEM-MNBT", "CIEM-NDPD", "CIEM-PAMS",
    "CIEM-SOGC", "CIEM-LDCP"
]

SUBCAMPOS_POR_CAMPO = {
    "padre": ["cedula", "telefono", "celular", "ocupacion"],
    "madre": ["cedula", "telefono", "celular", "ocupacion"],
    "tutor": ["cedula", "telefono", "celular", "ocupacion", "parentesco"]
}


def combinar(objeto_estudiante, objeto_matricula, subcampos):

    objeto_estudiante = objeto_estudiante if isinstance(objeto_estudiante, dict) else {}
    objeto_matricula = objeto_matricula if isinstance(objeto_matricula, dict) else {}

    resultado = dict(objeto_estudiante)

    for sub in subcampos:

        valor_matricula = str(objeto_matricula.get(sub, "")).strip()

        if valor_matricula:
            resultado[sub] = valor_matricula

    return resultado


total_actualizados = 0

for codigo in CODIGOS_AFECTADOS:

    estudiante = db.estudiantes.find_one({"_id": codigo})

    if not estudiante:
        print(f"\n{codigo}: no se encontró en estudiantes, se omite.")
        continue

    matricula_mas_reciente = db.matriculas.find_one(
        {"estudiante_id": codigo},
        sort=[("fecha_creacion", -1)]
    )

    if not matricula_mas_reciente:
        print(f"\n{codigo}: no tiene matrícula, se omite.")
        continue

    cambios = {}

    for campo, subcampos in SUBCAMPOS_POR_CAMPO.items():

        nuevo_objeto = combinar(
            estudiante.get(campo),
            matricula_mas_reciente.get(campo),
            subcampos
        )

        if nuevo_objeto != (estudiante.get(campo) or {}):
            cambios[campo] = nuevo_objeto

    if cambios:

        total_actualizados += 1

        print(f"\n{codigo} — {estudiante.get('nombre', '???')}")

        for campo, nuevo_objeto in cambios.items():
            print(f"    {campo}: {estudiante.get(campo)}  ->  {nuevo_objeto}")

        if not DRY_RUN:

            db.estudiantes.update_one(
                {"_id": codigo},
                {"$set": cambios}
            )

    else:

        print(f"\n{codigo}: nada que combinar (la matrícula no tenía datos extra).")


print("\n" + "=" * 70)
print(f"Estudiantes revisados: {len(CODIGOS_AFECTADOS)}")
print(f"Estudiantes actualizados: {total_actualizados}")

if DRY_RUN:
    print("\nMODO DE PRUEBA: no se modificó nada todavía.")
    print("Cambia DRY_RUN a False arriba y vuelve a correr el script para aplicar.")
else:
    print("\nCambios aplicados en la base de datos.")

print("=" * 70)
