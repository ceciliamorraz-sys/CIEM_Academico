from config.database import db

print("\n======================================")
print(" REVISIÓN DE DATOS DE MADRES")
print("======================================\n")

estudiantes = db.estudiantes.find({})

for estudiante in estudiantes:

    nombre = estudiante.get("nombre", "SIN NOMBRE")
    madre = estudiante.get("madre")

    print("ESTUDIANTE:", nombre)
    print("MADRE:", madre)
    print("TIPO:", type(madre).__name__)
    print("--------------------------------------")

print("\nRevisión terminada.")