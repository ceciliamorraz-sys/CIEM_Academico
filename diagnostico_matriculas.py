"""
Diagnóstico de matrículas CIEM (SOLO LECTURA por defecto).

Uso (desde la carpeta del proyecto, con el entorno virtual activo):
    python diagnostico_matriculas.py
    python diagnostico_matriculas.py --crear-indice   # opcional, ver LEEME.md

NO importa app.py (app.py escribe en la BD al importarse).
"""
import sys
from collections import Counter
from config.database import db

def main():
    print("== Matrículas por año lectivo (y estado) ==")
    c = Counter((repr(m.get("anio_lectivo")), m.get("estado")) for m in db.matriculas.find({}, {"anio_lectivo": 1, "estado": 1}))
    for k, v in sorted(c.items(), key=lambda x: str(x)):
        print(f"  año={k[0]:8} estado={k[1]!s:10} -> {v}")
    print(f"  TOTAL en colección: {db.matriculas.count_documents({})}")

    print("\n== Matrículas con anio_lectivo ausente o como texto ==")
    raros = list(db.matriculas.find({"$or": [{"anio_lectivo": {"$exists": False}}, {"anio_lectivo": {"$type": "string"}}]}, {"estudiante_id": 1, "anio_lectivo": 1}))
    print(f"  {len(raros)} registros", raros[:10])

    print("\n== Duplicados (estudiante_id + año) ==")
    dup = list(db.matriculas.aggregate([
        {"$group": {"_id": {"e": "$estudiante_id", "a": "$anio_lectivo"}, "n": {"$sum": 1}}},
        {"$match": {"n": {"$gt": 1}}}]))
    print(f"  {len(dup)} duplicados", dup[:10])

    print("\n== Estudiantes cuyo grado en la ficha difiere de su matrícula 2026 ==")
    difs = 0
    for m in db.matriculas.find({"anio_lectivo": {"$in": [2026, "2026"]}}, {"estudiante_id": 1, "grado": 1}):
        e = db.estudiantes.find_one({"_id": m["estudiante_id"]}, {"grado": 1})
        if e and e.get("grado") != m.get("grado"):
            difs += 1
            if difs <= 15:
                print(f"  {m['estudiante_id']}: ficha='{e.get('grado')}' vs matrícula 2026='{m.get('grado')}'")
    print(f"  {difs} diferencias (posible efecto de renovaciones 2027 que pisaron la ficha)")

    print("\n== Matrículas sin estudiante asociado ==")
    ids = set(db.estudiantes.distinct("_id"))
    huerf = [m["_id"] for m in db.matriculas.find({}, {"estudiante_id": 1}) if m.get("estudiante_id") not in ids]
    print(f"  {len(huerf)} huérfanas")

    if "--crear-indice" in sys.argv:
        db.matriculas.create_index(
            [("estudiante_id", 1), ("anio_lectivo", 1)], unique=True,
            partialFilterExpression={"anio_lectivo": {"$type": "int"}},
            name="uniq_estudiante_anio")
        print("\nÍndice único creado.")

if __name__ == "__main__":
    main()
