import os
import re

print("\n======================================")
print(" RUTAS FLASK DEL PROYECTO")
print("======================================\n")

for raiz, carpetas, archivos in os.walk("."):

    carpetas[:] = [
        c for c in carpetas
        if c not in {".venv", "__pycache__", ".git"}
    ]

    for archivo in archivos:

        if not archivo.endswith(".py"):
            continue

        ruta = os.path.join(raiz, archivo)

        try:

            with open(
                ruta,
                "r",
                encoding="utf-8"
            ) as f:

                lineas = f.readlines()

            for numero, linea in enumerate(
                lineas,
                start=1
            ):

                if (
                    "@app.route" in linea
                    or "@.*_bp.route" in linea
                    or ".route(" in linea
                ):

                    print(
                        f"{ruta} | línea {numero}: "
                        f"{linea.strip()}"
                    )

        except Exception:
            pass

print("\n======================================")
print(" FIN")
print("======================================")