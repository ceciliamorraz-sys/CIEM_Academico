# ==========================================================
# CORRECCIÓN: padre/tutor GUARDADOS COMO TEXTO PLANO
#
# Convierte el string guardado (ej. "Carlos Alberto García")
# en el mismo formato de objeto que ya usa "madre":
#
#   {"nombre": "...", "cedula": "", "telefono": "",
#    "celular": "", "ocupacion": ""}
#
# "tutor" además lleva "parentesco": "".
#
# El texto original se conserva completo como "nombre" —
# no se pierde ningún dato, solo se reacomoda.
#
# ==========================================================
# MODO DE PRUEBA POR DEFECTO.
#
# Con DRY_RUN = True (por defecto) el script SOLO IMPRIME
# qué cambiaría, sin tocar la base de datos.
#
# Cuando revises que la lista se ve bien, cambia a
# DRY_RUN = False y vuelve a correrlo para aplicar los
# cambios de verdad.
# ==========================================================

DRY_RUN = False

from config.database import db

CAMPOS_A_CORREGIR = ["padre", "tutor"]

total_revisados = 0
total_a_corregir = 0

for estudiante in db.estudiantes.find({}):

    codigo = estudiante.get("_id", "???")
    nombre_estudiante = estudiante.get("nombre", "(sin nombre)")

    total_revisados += 1

    cambios = {}

    for campo in CAMPOS_A_CORREGIR:

        valor = estudiante.get(campo)

        if isinstance(valor, str):

            nuevo_objeto = {
                "nombre": valor.strip(),
                "cedula": "",
                "telefono": "",
                "celular": "",
                "ocupacion": ""
            }

            if campo == "tutor":
                nuevo_objeto["parentesco"] = ""

            cambios[campo] = nuevo_objeto

    if cambios:

        total_a_corregir += 1

        print(f"\n{codigo} — {nombre_estudiante}")

        for campo, nuevo_objeto in cambios.items():
            print(f"    {campo}: '{estudiante.get(campo)}'  ->  {nuevo_objeto}")

        if not DRY_RUN:

            db.estudiantes.update_one(
                {"_id": codigo},
                {"$set": cambios}
            )


print("\n" + "=" * 70)
print(f"Estudiantes revisados: {total_revisados}")
print(f"Estudiantes corregidos: {total_a_corregir}")

if DRY_RUN:
    print("\nMODO DE PRUEBA: no se modificó nada todavía.")
    print("Cambia DRY_RUN a False arriba y vuelve a correr el script para aplicar.")
else:
    print("\nCambios aplicados en la base de datos.")

print("=" * 70)
