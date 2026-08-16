from config.database import db

print("\n======================================")
print(" PRUEBA DE RELACIÓN PADRE/MADRE")
print("======================================\n")

usuario = "alma"

estudiante = db.estudiantes.find_one({
    "madre_usuario": usuario
})

if estudiante:

    print("✅ ESTUDIANTE ENCONTRADO")
    print("ID:", estudiante.get("_id"))
    print("NOMBRE:", estudiante.get("nombre"))
    print("MADRE:", estudiante.get("madre"))
    print("MADRE_USUARIO:", estudiante.get("madre_usuario"))

else:

    print("❌ NO SE ENCONTRÓ ESTUDIANTE")

print("\nPrueba terminada.")