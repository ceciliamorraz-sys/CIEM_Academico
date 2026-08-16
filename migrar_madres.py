from config.database import db

print("\n======================================")
print(" MIGRACIÓN SEGURA DE DATOS DE MADRES")
print("======================================\n")

estudiantes = db.estudiantes.find({})

total = 0
diccionarios = 0
textos = 0
vacios = 0
modificados = 0

for estudiante in estudiantes:

    total += 1

    nombre_estudiante = estudiante.get(
        "nombre",
        "SIN NOMBRE"
    )

    madre = estudiante.get("madre")

    # ==========================================
    # MADRE YA ES DICCIONARIO
    # NO TOCAR
    # ==========================================

    if isinstance(madre, dict):

        diccionarios += 1
        continue

    # ==========================================
    # MADRE ES TEXTO
    # CONVERTIR A DICCIONARIO
    # ==========================================

    if isinstance(madre, str) and madre.strip():

        textos += 1

        nueva_madre = {
            "nombre": madre.strip(),
            "cedula": "",
            "telefono": "",
            "celular": "",
            "ocupacion": "",
            "usuario": ""
        }

        resultado = db.estudiantes.update_one(
            {
                "_id": estudiante["_id"]
            },
            {
                "$set": {
                    "madre": nueva_madre
                }
            }
        )

        if resultado.modified_count == 1:

            modificados += 1

            print(
                "CORREGIDO:",
                nombre_estudiante,
                "→",
                madre
            )

    # ==========================================
    # MADRE VACÍA O NULL
    # NO TOCAR
    # ==========================================

    else:

        vacios += 1


print("\n======================================")
print(" RESULTADO DE LA MIGRACIÓN")
print("======================================")

print("Total estudiantes:", total)
print("Madres como dict:", diccionarios)
print("Madres como texto:", textos)
print("Madres vacías:", vacios)
print("Registros modificados:", modificados)

print("======================================")