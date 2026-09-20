# -*- coding: utf-8 -*-
from config.database import db

usuario_objetivo = "alma"

print("=" * 60)
print(f"VERIFICANDO que ningun estudiante use madre_usuario: '{usuario_objetivo}'")
print("=" * 60)

vinculados = list(db.estudiantes.find({"madre_usuario": usuario_objetivo}))

if vinculados:
    print(f"¡ALTO! Hay {len(vinculados)} estudiante(s) vinculado(s) a '{usuario_objetivo}':")
    for est in vinculados:
        print(f"  - {est.get('nombre')} (codigo: {est.get('codigo')})")
    print("NO se va a borrar la cuenta para evitar romper ese vinculo.")
else:
    print(f"Ningun estudiante usa '{usuario_objetivo}' como madre_usuario. Es seguro borrar.")
    print()
    resultado = db.usuarios.delete_one({"usuario": usuario_objetivo})
    print(f"Cuentas borradas: {resultado.deleted_count}")
    if resultado.deleted_count:
        print(f"Listo: la cuenta '{usuario_objetivo}' fue eliminada de db.usuarios.")
    else:
        print(f"No se encontro ninguna cuenta con usuario '{usuario_objetivo}' (puede que ya se haya borrado antes).")

print("=" * 60)
