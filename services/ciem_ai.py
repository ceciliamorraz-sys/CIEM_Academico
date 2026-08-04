# ======================================
# CIEM ASISTE IA
# Motor de generación pedagógica
# ======================================


# ======================================
# RÚBRICA PROFESIONAL
# ======================================

def generar_rubrica(asignatura, tema, grado):

    return f"""

<div class="text-center mb-4">

<h2>
RÚBRICA DE EVALUACIÓN
</h2>

</div>


<table class="table table-bordered">

<tr>

<th>
Institución
</th>

<td colspan="3">
Colegio Integral Emanuel Matagalpa
</td>

</tr>


<tr>

<th>
Asignatura
</th>

<td>
{asignatura}
</td>


<th>
Grado
</th>

<td>
{grado}
</td>


</tr>


<tr>

<th>
Tema
</th>

<td colspan="3">
{tema}
</td>


</tr>


</table>



<h5>
Competencia
</h5>


<p>

Desarrolla conocimientos, habilidades y destrezas
para resolver situaciones relacionadas con el área.

</p>



<h5>
Criterios de evaluación
</h5>



<table class="table table-bordered table-striped">


<thead class="table-dark">


<tr>

<th>
Criterio
</th>

<th>
Excelente (5)
</th>

<th>
Muy Bueno (4)
</th>

<th>
Bueno (3)
</th>

<th>
En proceso (2)
</th>

<th>
Deficiente (1)
</th>


</tr>


</thead>



<tbody>


<tr>

<td>
Dominio conceptual
</td>

<td>
Comprende y explica correctamente los conceptos.
</td>

<td>
Comprende la mayoría de conceptos.
</td>

<td>
Presenta conocimientos básicos.
</td>

<td>
Requiere acompañamiento.
</td>

<td>
No evidencia comprensión.
</td>

</tr>




<tr>

<td>
Aplicación práctica
</td>

<td>
Aplica correctamente los conocimientos adquiridos.
</td>

<td>
Resuelve con pocos errores.
</td>

<td>
Resuelve parcialmente.
</td>

<td>
Presenta dificultades.
</td>

<td>
No logra aplicar.
</td>

</tr>




<tr>

<td>
Resolución de problemas
</td>

<td>
Propone soluciones correctas y argumentadas.
</td>

<td>
Resuelve adecuadamente.
</td>

<td>
Necesita orientación.
</td>

<td>
Requiere apoyo constante.
</td>

<td>
No logra resolver.
</td>

</tr>




<tr>

<td>
Presentación del trabajo
</td>

<td>
Trabajo completo, ordenado y profesional.
</td>

<td>
Buena presentación.
</td>

<td>
Cumple parcialmente.
</td>

<td>
Debe mejorar.
</td>

<td>
No cumple.
</td>

</tr>


</tbody>


</table>



<br>


<h5>

Puntaje obtenido:
______ / 20

</h5>



<h5>

Observaciones del docente:

</h5>


<div style="
height:80px;
border:1px solid #ccc;
border-radius:10px;
">

</div>

"""



# ======================================
# LISTA DE COTEJO
# ======================================

def generar_lista_cotejo(asignatura, tema, grado):


    return f"""


<h2 class="text-center">
LISTA DE COTEJO
</h2>



<table class="table table-bordered">


<tr>

<th>
Asignatura
</th>

<td>
{asignatura}
</td>


<th>
Grado
</th>

<td>
{grado}
</td>


</tr>


<tr>

<th>
Tema
</th>

<td colspan="3">
{tema}
</td>

</tr>


</table>




<table class="table table-bordered">


<thead class="table-dark">

<tr>

<th>
Criterio
</th>

<th>
Sí
</th>

<th>
No
</th>

<th>
Observaciones
</th>


</tr>

</thead>



<tbody>


<tr>

<td>
Comprende el contenido desarrollado.
</td>

<td>☐</td>

<td>☐</td>

<td></td>

</tr>



<tr>

<td>
Aplica los procedimientos correctamente.
</td>

<td>☐</td>

<td>☐</td>

<td></td>

</tr>




<tr>

<td>
Participa activamente en las actividades.
</td>

<td>☐</td>

<td>☐</td>

<td></td>

</tr>



<tr>

<td>
Presenta evidencias del trabajo realizado.
</td>

<td>☐</td>

<td>☐</td>

<td></td>

</tr>



</tbody>


</table>


"""



# ======================================
# GUÍA PRÁCTICA
# ======================================

def generar_practica(asignatura, tema, grado):

    return f"""

<div class="text-center">

<h2>
GUÍA PRÁCTICA
</h2>

<h5>
CIEM Asiste IA
</h5>

</div>



<table class="table table-bordered">


<tr>
<th>Institución</th>
<td>Colegio Integral Emanuel Matagalpa</td>
</tr>


<tr>
<th>Asignatura</th>
<td>{asignatura}</td>
</tr>


<tr>
<th>Tema</th>
<td>{tema}</td>
</tr>


<tr>
<th>Grado</th>
<td>{grado}</td>
</tr>


<tr>
<th>Tiempo estimado</th>
<td>90 minutos</td>
</tr>


</table>




<h4>
1. Competencia
</h4>


<p>

Desarrolla conocimientos, habilidades y destrezas
mediante actividades prácticas relacionadas con el área.

</p>




<h4>
2. Indicadores de logro
</h4>


<ul>

<li>
Identifica los conceptos principales del tema.
</li>

<li>
Aplica procedimientos adecuados.
</li>

<li>
Resuelve situaciones prácticas.
</li>

</ul>




<h4>
3. Objetivos de aprendizaje
</h4>


<ul>

<li>
Comprender el contenido desarrollado.
</li>

<li>
Aplicar los conocimientos adquiridos.
</li>

<li>
Demostrar dominio mediante ejercicios.
</li>

</ul>




<h4>
4. Recursos

</h4>


<ul>

<li>
Material didáctico.
</li>

<li>
Guía de trabajo.
</li>

<li>
Herramientas digitales.
</li>

</ul>




<h4>
5. Desarrollo de la práctica

</h4>



<h5>
Actividad 1: Exploración inicial
</h5>


<p>

Analice los conocimientos previos relacionados con:
<b>{tema}</b>

</p>




<h5>
Actividad 2: Aplicación práctica
</h5>


<ol>

<li>
Resolver ejercicios relacionados con el contenido.
</li>

<li>
Explicar el procedimiento utilizado.
</li>

<li>
Presentar resultados obtenidos.
</li>

</ol>




<h5>
Actividad 3: Desafío

</h5>


<p>

Proponga una solución aplicando los conocimientos adquiridos.

</p>




<h4>
6. Evidencias de aprendizaje

</h4>


<ul>

<li>
Ejercicios desarrollados.
</li>

<li>
Producto elaborado.
</li>

<li>
Explicación del procedimiento.
</li>

</ul>




<h4>
7. Criterios de evaluación

</h4>



<table class="table table-bordered">


<tr>

<th>
Criterio
</th>

<th>
Cumple
</th>

<th>
En proceso
</th>

</tr>



<tr>

<td>
Comprende el contenido.
</td>

<td>☐</td>

<td>☐</td>

</tr>



<tr>

<td>
Aplica correctamente los procedimientos.
</td>

<td>☐</td>

<td>☐</td>

</tr>



<tr>

<td>
Presenta evidencias completas.
</td>

<td>☐</td>

<td>☐</td>

</tr>



</table>




<h4>
8. Autoevaluación

</h4>


<p>

¿Qué aprendí?

______________________________

</p>


<p>

¿Qué debo mejorar?

______________________________

</p>


"""


# ======================================
# EXAMEN
# ======================================

def generar_examen(asignatura, tema, grado):


    return f"""


<h2 class="text-center">
EXAMEN
</h2>



<table class="table table-bordered">


<tr>

<th>
Asignatura
</th>

<td>
{asignatura}
</td>


</tr>



<tr>

<th>
Tema
</th>

<td>
{tema}
</td>

</tr>



<tr>

<th>
Grado
</th>

<td>
{grado}
</td>

</tr>



</table>




<h5>
I. Selección múltiple
</h5>


<p>

1. Seleccione la respuesta correcta relacionada con el tema estudiado.

</p>



<h5>
II. Desarrollo
</h5>


<p>

Explique el procedimiento utilizado para resolver
el problema planteado.

</p>



<h5>
III. Caso práctico
</h5>


<p>

Aplique los conocimientos adquiridos en una situación real.

</p>


"""



# ======================================
# PLAN DE CLASE
# ======================================

def generar_plan(asignatura, tema, grado):


    return f"""


<h2 class="text-center">
PLAN DE CLASE
</h2>



<table class="table table-bordered">


<tr>

<th>
Asignatura
</th>

<td>
{asignatura}
</td>


</tr>



<tr>

<th>
Tema
</th>

<td>
{tema}
</td>


</tr>



<tr>

<th>
Grado
</th>

<td>
{grado}
</td>


</tr>


</table>




<h5>
Competencia
</h5>


<p>

Desarrolla habilidades mediante actividades
significativas de aprendizaje.

</p>



<h5>
Inicio

</h5>

<p>

Exploración de conocimientos previos y motivación.

</p>



<h5>
Desarrollo

</h5>

<p>

Explicación del contenido, ejemplos y práctica guiada.

</p>



<h5>
Cierre

</h5>

<p>

Retroalimentación y evaluación del aprendizaje.

</p>


"""