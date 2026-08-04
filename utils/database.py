from pymongo import MongoClient
from urllib.parse import quote_plus

# =====================================
# CONEXIÓN A MONGODB ATLAS
# =====================================

usuario_atlas = "ceciliamorraz_db_user"
password_atlas = quote_plus("CiemAtlas2026")

MONGO_URI = (
    f"mongodb+srv://{usuario_atlas}:{password_atlas}"
    "@cluster0.olbd8g8.mongodb.net/CIEM"
    "?retryWrites=true&w=majority&appName=Cluster0"
)

client = MongoClient(MONGO_URI)

# Base de datos
db = client["CIEM"]