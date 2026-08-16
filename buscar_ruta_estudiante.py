import os

print("\n======================================")
print(" BUSCANDO RUTA DEL ESTUDIANTE")
print("======================================\n")

for raiz, carpetas, archivos in os.walk("."):

    # No revisar estas carpetas
    carpetas[:] = [
        c for c in carpetas
        if c not in {".venv", "__pycache__", ".git"}
    ]

    for archivo in archivos:

        if archivo.endswith(".py"):

            ruta = os.path.join(
                raiz,
                archivo
            )

            try:

                with open(
                    ruta,
                    "r",
                    encoding="utf-8"
                ) as f:

                    contenido = f.read()

                if (
                    "/estudiante" in contenido
                    or "def estudiante" in contenido
                    or 'rol == "padre"' in contenido
                    or "rol == 'padre'" in contenido
                ):

                    print("--------------------------------------")
                    print("ARCHIVO:", ruta)

                    if "/estudiante" in contenido:
                        print("  → Contiene /estudiante")

                    if "def estudiante" in contenido:
                        print("  → Contiene def estudiante")

                    if 'rol == "padre"' in contenido:
                        print('  → Contiene rol == "padre"')

                    if "rol == 'padre'" in contenido:
                        print("  → Contiene rol == 'padre'")

            except Exception as e:

                print(
                    "ERROR:",
                    ruta,
                    e
                )

print("\n======================================")
print(" BÚSQUEDA TERMINADA")
print("======================================")