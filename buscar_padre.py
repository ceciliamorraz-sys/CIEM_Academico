import os

print("\n======================================")
print(" BUSCANDO CÓDIGO DEL PADRE")
print("======================================\n")

palabras = [
    "madre_usuario",
    "db.estudiantes.find_one",
    "db.estudiantes.find",
    "session.get",
    "rol",
    "padre"
]

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

            coincidencias = []

            for numero, linea in enumerate(lineas, start=1):

                for palabra in palabras:

                    if palabra in linea:
                        coincidencias.append(
                            (numero, linea.strip())
                        )
                        break

            if coincidencias:

                print("--------------------------------------")
                print("ARCHIVO:", ruta)

                for numero, linea in coincidencias:
                    print(
                        f"{numero}: {linea}"
                    )

        except Exception as e:

            print(
                "ERROR:",
                ruta,
                e
            )

print("\n======================================")
print(" BÚSQUEDA TERMINADA")
print("======================================")