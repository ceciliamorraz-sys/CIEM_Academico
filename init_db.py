from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["CIEM"]

# LIMPIAR PARA EVITAR DUPLICADOS
db.usuarios.delete_many({})

# CREAR USUARIOS CORRECTOS
db.usuarios.insert_many([
    {
        "usuario": "admin",
        "password": "1234",
        "rol": "admin"
    },
    {
        "usuario": "docente1",
        "password": "1234",
        "rol": "docente"
    },
    {
        "usuario": "estudiante1",
        "password": "1234",
        "rol": "estudiante"
    }
])

print("USUARIOS CREADOS CORRECTAMENTE")