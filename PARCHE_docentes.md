# Evidencias de preescolar (AA / AP) — cambios en tu proyecto

## Archivos nuevos (copiar tal cual)
- `routes/notas_preescolar.py`
- `templates/docente/notas_preescolar.html`

## Cambios en `routes/docentes.py` (3, todos pequeños)

### 1. Import (junto a los otros imports, cerca de la línea 67)
```python
from routes.notas_preescolar import (
    vista_notas_preescolar,
    registrar_preescolar
)
```

### 2. Registrar la ruta de guardado (justo después de definir `role_required`, ~línea 98)
```python
registrar_preescolar(docente_bp, role_required)
```

### 3. En `notas()` — desviar preescolar (después del paso "15. RESULTADO", antes de "16. BUSCAR NOTAS EXISTENTES", ~línea 2461)
```python
    if nivel_normalizado == "preescolar":
        return vista_notas_preescolar(asignacion, estudiantes, docente)
```

Con eso, en primaria y secundaria todo sigue igual (EP1–EP10).

## Qué hace
- La vista depende del **nivel de la clase asignada** (`asignaciones_clase.nivel == "Preescolar"`).
- Una hoja por estudiante y corte; cada docente solo puede marcar los indicadores de su materia:
  - Titular (cualquier materia de preescolar que no sea de las de abajo): social, emocional y 3 filas de cognitiva
  - Educación Física → dimensión física
  - Educación Cristiana → dimensión espiritual
  - Inglés → 1 fila de cognitiva
  - Informática Educativa → 1 fila de cognitiva
- El servidor ignora cualquier indicador que no sea del docente aunque alguien manipule el formulario.
- «Promedio general» se recalcula en cada guardado: AA si más de la mitad de los indicadores marcados son AA (`UMBRAL_AA_PROMEDIO`).
- Datos en la colección nueva `evidencias_preescolar`; no toca `notas`.

## Pendiente / cosas a revisar
1. **Indicadores:** los textos de `INDICADORES` son una propuesta mía; cámbialos por los oficiales del colegio. No cambies los ids (`cog1`, `soc1`…) cuando ya haya notas guardadas.
2. **Detección de materia por nombre:** busca "física", "cristian/bíblic", "inglés", "informática" en `asignatura_nombre`. Si alguna se llama distinto, ajusta `duenio_de_la_asignatura`.
3. **`guardar_notas()` actual (línea ~2853)** busca estudiantes solo con `grado == "I Nivel"` exacto, sin el mapa de preescolar. Con esta vista ya no se usa para preescolar, pero si en algún lugar sigue llamándose para esa clase no encontrará alumnos.
4. **Aún no hecho:** que el padre vea la hoja en su panel y el PDF/boletín con el formato de la hoja. Se construye sobre `evidencias_preescolar`.
