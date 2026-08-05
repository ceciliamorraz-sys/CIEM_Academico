from pymongo import MongoClient

MONGO_URI = "mongodb+srv://ciemadmin:TU_CONTRASEÑA_REAL@cluster0.olbd8g8.mongodb.net/CIEM?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(MONGO_URI)

try:
    client.admin.command("ping")
    print("✅ Conexión exitosa")
except Exception as e:
    print("❌ Error:", e)