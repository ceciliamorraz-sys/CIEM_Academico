# Corrección módulo de matrículas CIEM (2026–2027)

## Qué contiene
| Archivo | Destino en tu proyecto |
|---|---|
| `app.py` | reemplaza `app.py` (es tu app.py subido + los cambios; ver lista abajo) |
| `templates/admin/matriculas.html` | `templates/admin/` |
| `templates/admin/ver_matricula.html` | `templates/admin/` |
| `templates/admin/editar_matricula.html` | `templates/admin/` |
| `templates/admin/reporte_matriculas.html` | `templates/admin/` |
| `templates/admin/reporte_matriculas_pdf.html` | `templates/admin/` |
| `diagnostico_matriculas.py` | raíz del proyecto (solo lectura) |

## Causa del problema
1. El listado, el dashboard y los reportes contaban/listaban `db.matriculas` sin filtrar por `anio_lectivo`, por eso una matrícula 2027 aparecía en el total de 2026.
2. "2026" estaba escrito fijo en las plantillas.
3. Al renovar, `agregar_matricula` y `editar_matricula` sobrescribían `estudiantes.grado/seccion` con el grado del año nuevo.
4. `ver/editar_matricula` tomaban siempre la matrícula más reciente, sin importar cuál se había pulsado.

## Cambios en app.py
- Bloque nuevo antes de "LISTAR MATRÍCULAS": `ANIO_LECTIVO_VIGENTE`, orden académico de grados, y funciones `obtener_matriculas_anio`, `contar_matriculas_anio`, `agrupar_matriculas_por_grado`, etc.
- `listar_matriculas`: filtra por año (`?anio=`), grado, sección y búsqueda (`?q=`); orden año → grado → sección → apellidos/nombres; agrupado por grado/sección.
- `admin_dashboard`, `reporte_matriculas`, `reporte_matriculas_pdf`, `reporte_academico`: totales por año lectivo (mismo conteo en todos).
- `agregar_matricula`: grado/sección de la ficha solo se actualizan si el año es `ANIO_LECTIVO_VIGENTE`.
- `ver_matricula` / `editar_matricula`: abren la matrícula del año pulsado (`?anio=`); el año lectivo ya no se edita; grado/sección de la ficha solo cambian si es el año vigente.
- No se tocó ningún otro módulo ni el esquema de la BD. No se eliminan estudiantes ni matrículas.

## Pasos para implementar
1. Haz respaldo: copia de `app.py` y las 5 plantillas, y exporta la BD (`mongodump`).
2. Copia los archivos a su destino.
3. Ejecuta `python diagnostico_matriculas.py` (solo lee) y revisa: duplicados, años como texto, fichas con grado distinto a la matrícula 2026.
4. Arranca la app local y haz las pruebas de abajo.
5. Si todo está bien: `git add . && git commit -m "Matrículas por año lectivo" && git push` (Render despliega solo).
6. Cuando comience el año 2027, cambia `ANIO_LECTIVO_VIGENTE = 2027` en app.py.

## Pruebas manuales
1. `/matriculas` muestra año 2026 por defecto; el total de la tarjeta = filas de la tabla.
2. Renueva un estudiante de 2026 a 2027 (otro grado): el total 2026 NO cambia; `/matriculas?anio=2027` muestra +1.
3. La ficha del estudiante conserva su grado 2026.
4. Dashboard (`/admin`) y `/admin/reporte/matriculas` muestran el mismo total 2026 que el listado; con `?anio=2027` el de 2027.
5. Orden: Preescolar → 1er a 6to grado → 1er a 5to año; dentro, sección A, B, C y apellidos.
6. Filtros: grado, sección, búsqueda con y sin tildes.
7. Ver/editar desde una fila 2026 y otra 2027 abre cada una (la URL lleva `?anio=`); guardar edición de 2027 no cambia el grado de la ficha.
8. PDF: nombre `reporte_matriculas_2026.pdf` y año en el encabezado.

## Opcional: índice único (estudiante, año)
Evita duplicados a nivel de BD. Solo si el diagnóstico no muestra duplicados:
`python diagnostico_matriculas.py --crear-indice`
Reversión: `db.matriculas.drop_index("uniq_estudiante_anio")`.

## Reversión
Restaura los archivos respaldados. Los cambios no modifican datos existentes en la BD.

## Qué se verificó y qué no (honestidad)
- Verificado: `app.py` compila sin errores; las plantillas se renderizan con datos de prueba; la lógica de orden de grados y agrupación se probó con casos de ejemplo.
- NO verificado: ejecución contra tu MongoDB real, las pantallas completas en navegador, ni el despliegue en GitHub/Render. Prueba primero en local.
- `reporte_academico.html` no fue enviada: recibe el mismo `total_matriculas` y `grados`, ahora por año; si tiene "2026" fijo, ajústalo con `{{ anio_lectivo }}`.
- El estado "cancelada" del editar sigue disponible; se añadió "inactiva" para no reactivar por error matrículas desactivadas.
