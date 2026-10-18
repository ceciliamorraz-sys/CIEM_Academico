# Solo lectura: no modifica nada en la base de datos.
# Explica por que matricula 2026 (182) y estudiantes (184) no coinciden.
from collections import Counter
from config.database import db

ANIO = "2026"

estudiantes = list(db.estudiantes.find({}))
matriculas = list(db.matriculas.find({}))

print("Estudiantes en total:", len(estudiantes))
print("Matriculas en total:", len(matriculas))

# 1) Que valores tiene el campo de anio en matriculas
anios = Counter(str(m.get("anio_lectivo", "(sin campo)")) for m in matriculas)
print("\nMatriculas por anio_lectivo:", dict(anios))

mat_anio = [m for m in matriculas if str(m.get("anio_lectivo", "")) == ANIO]
print("Matriculas %s: %d" % (ANIO, len(mat_anio)))


def codigo_de(m):
    for k in ("estudiante_codigo", "codigo_estudiante", "codigo"):
        if m.get(k):
            return str(m[k])
    return None


# 2) Matriculas del anio repetidas o sin codigo
codigos_mat = [codigo_de(m) for m in mat_anio]
print("Matriculas %s sin codigo de estudiante: %d" % (ANIO, codigos_mat.count(None)))
rep = {c: n for c, n in Counter(codigos_mat).items() if c and n > 1}
print("Codigos con mas de una matricula %s: %s" % (ANIO, rep or "ninguno"))

# 3) Estudiantes sin matricula del anio
set_mat = set(c for c in codigos_mat if c)
sin_mat = [e for e in estudiantes if str(e.get("codigo", "")) not in set_mat]
print("\nEstudiantes SIN matricula %s: %d" % (ANIO, len(sin_mat)))
for e in sin_mat:
    print("  ", e.get("codigo"), "|", e.get("nombres") or e.get("nombre"),
          e.get("apellidos", ""), "| grado:", e.get("grado"),
          "| creado:", e.get("fecha_creacion") or e.get("created_at") or "-")

# 4) Matriculas del anio que apuntan a un codigo que no existe en estudiantes
set_est = set(str(e.get("codigo", "")) for e in estudiantes)
huerfanas = [c for c in set_mat if c not in set_est]
print("\nMatriculas %s con codigo inexistente en estudiantes: %s" % (ANIO, huerfanas or "ninguna"))

# 5) Estudiantes duplicados por codigo
dup = {c: n for c, n in Counter(str(e.get("codigo", "")) for e in estudiantes).items() if n > 1}
print("Codigos de estudiante duplicados:", dup or "ninguno")
