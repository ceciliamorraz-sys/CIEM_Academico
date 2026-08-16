from config.database import db

print("\n======================================")
print(" DATOS COMPLETOS DEL USUARIO ALMA")
print("======================================\n")

usuario = db.usuarios.find_one({
    "usuario": "alma"
})

if usuario:
    for campo, valor in usuario.items():
        print(f"{campo}: {valor}")
else:
    print("NO SE ENCONTRÓ EL USUARIO")

print("\n======================================")
print(" DATOS DE KAYLA")
print("======================================\n")

estudiante = db.estudiantes.find_one({
    "nombre": "Kayla Marcela Brown Morráz"
})

if estudiante:
    for campo, valor in estudiante.items():
        print(f"{campo}: {valor}")
else:
    print("NO SE ENCONTRÓ A KAYLA")

print("\nRevisión terminada.")