from flask import (
    Blueprint,
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_file
    
   
)
from io import BytesIO
from weasyprint import HTML
from datetime import datetime
from flask_pymongo import PyMongo
from routes.mined import datos_mined, estadistica_grado
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from io import BytesIO
from flask import send_file
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)


import os
from bson import ObjectId

from reportlab.lib.styles import getSampleStyleSheet

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image
)

from reportlab.lib import colors

from reportlab.lib.pagesizes import letter

from reportlab.lib.enums import TA_CENTER

from io import BytesIO

from config.database import db

from routes.mined import (
    datos_mined,
    estadistica_grado,
    informe_retencion
)

from functools import wraps

from datetime import datetime



docente_bp = Blueprint(
    "docente",
    __name__,
    url_prefix="/docente"
)
# ==========================
# CONTROL DE ACCESO
# ==========================

def role_required(rol):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            if "rol" not in session:
                return redirect(url_for("login"))

            if session["rol"] != rol:
                return redirect(url_for("login"))

            return func(*args, **kwargs)

        return wrapper
    return decorator


# ============================================================
# DASHBOARD DOCENTE
# ============================================================

@docente_bp.route("/")
@role_required("docente")
def dashboard_docente():

    usuario = session.get("usuario")
    fecha_hoy = datetime.now().strftime("%d/%m/%Y")

   # ========================================================
    # 1. BUSCAR DOCENTE
    # ========================================================

    docente = db.docentes.find_one({
        "usuario": usuario
    })

    if not docente:

        flash(
            "Docente no encontrado",
            "danger"
        )

        return redirect(
            url_for("login")
        )

    docente_id = str(
        docente.get("_id")
    )
    # ========================================================
    # 2. ASIGNACIONES DE CLASE DEL DOCENTE
    # ========================================================
    #
    # La fuente oficial para el dashboard docente es ahora
    # la colección asignaciones_clase.
    #
    # Ejemplo:
    # DOC012 → Evert → 9 clases
    # DOC013 → Inglés → 9 clases
    #
    # Ya no dependemos de la colección antigua asignaturas.
    # ========================================================

    clases = list(
        db.asignaciones_clase.find({
            "docente_id": docente_id,
            "activo": True
        })
    )

    total_asignaturas = len(clases)

    print("")
    print("========================================================")
    print("📚 ASIGNACIONES DEL DOCENTE")
    print("========================================================")
    print("DOCENTE:", docente.get("nombre"))
    print("DOCENTE ID:", docente_id)
    print("TOTAL ASIGNACIONES:", total_asignaturas)

    for clase in clases:

        print(
            clase.get("_id"),
            "|",
            clase.get("asignatura_codigo"),
            "|",
            clase.get("asignatura_nombre"),
            "| NIVEL:",
            clase.get("nivel"),
            "| GRADO:",
            clase.get("grado"),
            "| SECCIÓN:",
            clase.get("seccion"),
            "| DOCENTE:",
            clase.get("docente_id")
        )

    print("========================================================")

    # ========================================================
    # 3. ESTUDIANTES
    # ========================================================
    #
    # IMPORTANTE:
    # Se utiliza la misma consulta que ya funciona
    # correctamente en la pantalla de estudiantes.
    #
    # No se filtra por:
    # - grado
    # - sección
    # - estado
    # - asignatura
    #
    # Esto garantiza que el dashboard muestre los
    # mismos 103 estudiantes.
    # ========================================================

    estudiantes = list(
        db.estudiantes.find({})
    )

    # ========================================================
    # ORDENAR ESTUDIANTES
    # ========================================================

    estudiantes.sort(
        key=lambda estudiante: str(
            estudiante.get(
                "nombre",
                ""
            )
        ).lower()
    )

    # ========================================================
    # TOTAL DE ESTUDIANTES
    # ========================================================

    total_estudiantes = len(
        estudiantes
    )

    # ========================================================
    # AGREGAR ID COMO TEXTO
    # ========================================================

    for estudiante in estudiantes:

        estudiante["id_str"] = str(
            estudiante.get("_id")
        )

    # ========================================================
    # 4. ASISTENCIAS
    # ========================================================

    total_asistencias = db.asistencias.count_documents({
        "docente": usuario
    })

    pendientes = list(
        db.asistencias.find({
            "docente": usuario
        }).sort(
            "_id",
            -1
        )
    )

    # ========================================================
    # 5. NOTAS DEL DOCENTE
    # ========================================================

    ids_estudiantes = [

        str(
            estudiante.get("_id")
        )

        for estudiante in estudiantes

        if estudiante.get("_id") is not None
    ]

    notas_docente = []

    if ids_estudiantes:

        notas_docente = list(
            db.notas.find({
                "estudiante_id": {
                    "$in": ids_estudiantes
                }
            }).sort(
                "_id",
                1
            )
        )

        # ========================================================
        # 🔎 ESTRUCTURA REAL DE LAS NOTAS
        # ========================================================

        print("")
        print("========================================================")
        print("🔎 ESTRUCTURA REAL DE LAS NOTAS")
        print("========================================================")

        for nota in notas_docente[:10]:

            print("----------------------------------------")
            print(nota)
            print("----------------------------------------")

        print("========================================================")

    # ========================================================
    # 6. PROMEDIO GENERAL
    # ========================================================

    valores_promedio = []

    for nota in notas_docente:

        # Utilizamos la nota real sobre 100
        valor = nota.get("nota")

        try:

            if valor is not None:

                valores_promedio.append(
                    float(valor)
                )

        except (
            ValueError,
            TypeError
        ):

            pass


    if valores_promedio:

        promedio_general = round(
            sum(valores_promedio)
            /
            len(valores_promedio)
        )

    else:

        promedio_general = 0

    # ========================================================
    # 7. APROBADOS Y REPROBADOS
    # ========================================================

    aprobados = sum(
        1
        for valor in valores_promedio
        if valor >= 60
    )

    reprobados = sum(
        1
        for valor in valores_promedio
        if valor < 60
    )

    # ========================================================
    # 8. PROGRESO DE NOTAS
    # ========================================================

    total_esperado_notas = (
        total_estudiantes * 4
    )

    if total_esperado_notas > 0:

        progreso_notas = round(
            (
                len(notas_docente)
                /
                total_esperado_notas
            )
            * 100
        )

        progreso_notas = min(
            progreso_notas,
            100
        )

    else:

        progreso_notas = 0

    # ========================================================
    # 9. PROGRESO DE ASISTENCIA
    # ========================================================

    if total_estudiantes > 0:

        progreso_asistencia = round(
            (
                total_asistencias
                /
                total_estudiantes
            )
            * 100
        )

        progreso_asistencia = min(
            progreso_asistencia,
            100
        )

    else:

        progreso_asistencia = 0

    # ========================================================
    # 10. MENSAJES
    # ========================================================

    conversaciones = list(
        db.conversaciones.find({
            "docente_id": docente_id
        }).sort(
            "ultima_actualizacion",
            -1
        )
    )

    mensajes_pendientes = (
        db.conversaciones.count_documents({
            "docente_id": docente_id,
            "no_leidos_docente": {
                "$gt": 0
            }
        })
    )

    # ========================================================
    # 11. ESTADÍSTICAS
    # ========================================================

    estadistica = {

        "total_asignaturas":
            total_asignaturas,

        "total_estudiantes":
            total_estudiantes,

        "promedio_general":
            promedio_general,

        "progreso_notas":
            progreso_notas,

        "progreso_asistencia":
            progreso_asistencia,

        "aprobados":
            aprobados,

        "reprobados":
            reprobados,

        "presentes":
            total_asistencias,

        "incidencias":
            0,

        "comunicaciones":
            len(conversaciones)
    }

    # ========================================================
    # 12. CLASES PARA MOSTRAR EN EL DASHBOARD
    # ========================================================

    clases_hoy = clases

    # ========================================================
    # 13. DASHBOARD
    # ========================================================

    return render_template(

        "docente/dashboard_docente.html",

        docente=docente,

        usuario=usuario,

        docente_id=docente_id,

        fecha_hoy=fecha_hoy,

        conversaciones=conversaciones,

        mensajes_pendientes=mensajes_pendientes,

        clases=clases,

        clases_hoy=clases_hoy,

        total_asignaturas=total_asignaturas,

        estudiantes=estudiantes,

        total_estudiantes=total_estudiantes,

        total_asistencias=total_asistencias,

        pendientes=pendientes,

        notas_docente=notas_docente,

        estadistica=estadistica
    )   
    

# ==========================================================
# MIS CLASES
# ==========================================================

@docente_bp.route("/mis_clases")
@role_required("docente")
def mis_clases():

    usuario = session.get("usuario")

    # ======================================================
    # BUSCAR DOCENTE
    # ======================================================

    docente = db.docentes.find_one({
        "usuario": usuario
    })

    if not docente:

        flash(
            "Docente no encontrado.",
            "danger"
        )

        return redirect(
            url_for("login")
        )

    # ======================================================
    # ID DEL DOCENTE
    # ======================================================

    docente_id = str(
        docente.get("_id")
    )

    # ======================================================
    # OBTENER ASIGNACIONES DE CLASE
    # ======================================================
    #
    # La fuente oficial ahora es:
    #
    # asignaciones_clase
    #
    # No necesitamos consultar:
    # - asignaciones
    # - asignaturas
    # - cursos
    #
    # porque la nueva colección ya contiene
    # toda la información necesaria.
    # ======================================================

    clases = list(
        db.asignaciones_clase.find({
            "docente_id": docente_id,
            "activo": True
        }).sort(
            [
                ("nivel", 1),
                ("grado", 1),
                ("seccion", 1),
                ("asignatura_nombre", 1)
            ]
        )
    )

    # ======================================================
    # INFORMACIÓN PARA DEPURACIÓN
    # ======================================================

    print("")
    print("========================================================")
    print("📚 MIS CLASES")
    print("========================================================")
    print("DOCENTE:", docente.get("nombre"))
    print("DOCENTE ID:", docente_id)
    print("TOTAL CLASES:", len(clases))

    for clase in clases:

        print(
            clase.get("_id"),
            "|",
            clase.get("asignatura_codigo"),
            "|",
            clase.get("asignatura_nombre"),
            "| NIVEL:",
            clase.get("nivel"),
            "| GRADO:",
            clase.get("grado"),
            "| SECCIÓN:",
            clase.get("seccion"),
            "| DOCENTE:",
            clase.get("docente_id")
        )

    print("========================================================")

    # ======================================================
    # MOSTRAR MIS CLASES
    # ======================================================

    return render_template(
        "docente/mis_clases.html",
        clases=clases,
        docente=docente,
        docente_id=docente_id
    )

    # ==========================================================
    # BUSCAR ASIGNACIÓN DE CLASE
    # ==========================================================

    docente_id = str(
        docente.get("_id")
    )

    asignatura = db.asignaciones_clase.find_one({
        "_id": asignatura_id,
        "docente_id": docente_id,
        "activo": True
    })
# =====================================
# CERRAR SESIÓN DOCENTE
# =====================================

@docente_bp.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# =====================================
# ABRIR ASISTENCIA
# =====================================

@docente_bp.route("/asistencia/<asignatura_id>")
@role_required("docente")
def asistencia(asignatura_id):

    print("========================================")
    print("🔥 ASISTENCIA")
    print("ASIGNACIÓN ID:", asignatura_id)
    print("========================================")

    # =====================================
    # BUSCAR DOCENTE
    # =====================================

    usuario = session.get("usuario")

    docente = db.docentes.find_one({
        "usuario": usuario
    })

    if not docente:

        flash(
            "Docente no encontrado",
            "danger"
        )

        return redirect(
            url_for("login")
        )

    # =====================================
    # ID OFICIAL DEL DOCENTE
    # =====================================

    codigo_docente = str(
        docente.get("codigo", "")
    ).strip()

    docente_id = f"DOC{codigo_docente}"

    print("👨‍🏫 DOCENTE:", docente.get("nombre"))
    print("🆔 DOCENTE ID:", docente_id)

    # =====================================
    # BUSCAR ASIGNACIÓN DE CLASE
    # =====================================
    #
    # La fuente oficial es:
    #
    # asignaciones_clase
    #
    # Ya NO utilizamos:
    #
    # db.asignaturas
    #
    # La asignación debe pertenecer al
    # docente que inició sesión.
    # =====================================

    asignacion = db.asignaciones_clase.find_one({

        "_id": asignatura_id,

        "docente_id": docente_id,

        "activo": True

    })

    print("📚 ASIGNACIÓN:", asignacion)

    if not asignacion:

        flash(
            "Asignación de clase no encontrada.",
            "danger"
        )

        return redirect(
            url_for("docente.aulas")
        )

    # =====================================
    # DATOS DE LA ASIGNACIÓN
    # =====================================

    grado = asignacion.get("grado")

    seccion = asignacion.get("seccion")

    nivel = asignacion.get("nivel")

    asignatura_codigo = asignacion.get(
        "asignatura_codigo"
    )

    asignatura_nombre = asignacion.get(
        "asignatura_nombre"
    )

    print("📚 CÓDIGO:", asignatura_codigo)
    print("📚 ASIGNATURA:", asignatura_nombre)
    print("🎓 NIVEL:", nivel)
    print("🎓 GRADO:", grado)
    print("🏫 SECCIÓN:", seccion)

    # =====================================
    # CONVERTIR GRADO
    # =====================================

    mapa_grados = {

        "1": "1er Grado",
        "2": "2do Grado",
        "3": "3er Grado",
        "4": "4to Grado",
        "5": "5to Grado",
        "6": "6to Grado"

    }

    grado_estudiante = mapa_grados.get(
        str(grado),
        grado
    )

    print(
        "🔄 GRADO PARA ESTUDIANTES:",
        grado_estudiante
    )

    # =====================================
    # BUSCAR ESTUDIANTES
    # =====================================

    estudiantes = list(
        db.estudiantes.find({

            "grado": grado_estudiante,

            "seccion": seccion,

            "estado": "activo"

        })
    )

    print("========================================")
    print("👥 ESTUDIANTES ENCONTRADOS")
    print("TOTAL:", len(estudiantes))
    print("========================================")

    for estudiante in estudiantes:

        print(
            "➡️",
            estudiante.get("_id"),
            "|",
            estudiante.get("nombre"),
            "|",
            estudiante.get("grado"),
            "|",
            estudiante.get("seccion")
        )

    # =====================================
    # FECHA ACTUAL
    # =====================================

    fecha = datetime.now().strftime(
        "%Y-%m-%d"
    )

    print("📅 FECHA:", fecha)

    # =====================================
    # BUSCAR ASISTENCIAS GUARDADAS
    #
    # PARA ESTA ASIGNACIÓN Y FECHA
    # =====================================

    asistencias_guardadas = list(
        db.asistencias.find({

            "asignatura_id": asignatura_id,

            "fecha": fecha

        })
    )

    print("========================================")
    print(
        "📋 ASISTENCIAS GUARDADAS:",
        len(asistencias_guardadas)
    )
    print("========================================")

    # =====================================
    # CONSTRUIR DICCIONARIO SEGURO
    # =====================================

    asistencia = {}

    for registro in asistencias_guardadas:

        estudiante_id = registro.get(
            "estudiante_id"
        )

        if estudiante_id is None:

            continue

        estudiante_id = str(
            estudiante_id
        )

        estado_guardado = registro.get(
            "estado",
            "Presente"
        )

        motivo_guardado = registro.get(
            "motivo",
            ""
        )

        asistencia[estudiante_id] = {

            "estado": str(
                estado_guardado
            ),

            "motivo": str(
                motivo_guardado
            )

        }

        print(
            "➡️",
            estudiante_id,
            "|",
            estado_guardado,
            "|",
            motivo_guardado
        )

    # =====================================
    # PREPARAR DATOS PARA EL HTML
    # =====================================
    #
    # Creamos un objeto compatible con
    # el template actual.
    #
    # Así podemos mantener:
    #
    # asignatura["grado"]
    # asignatura["seccion"]
    # asignatura["nombre"]
    #
    # aunque la información venga ahora
    # de asignaciones_clase.
    # =====================================

    asignatura = {

        "_id": asignacion.get("_id"),

        "codigo": asignatura_codigo,

        "nombre": asignatura_nombre,

        "nivel": nivel,

        "grado": grado,

        "seccion": seccion,

        "docente_id": docente_id

    }

    # =====================================
    # MOSTRAR ASISTENCIA
    # =====================================

    print("========================================")
    print("📦 ASISTENCIA ENVIADA AL HTML")
    print(asistencia)
    print("========================================")

    return render_template(

        "docente/asistencia.html",

        asignatura=asignatura,

        estudiantes=estudiantes,

        fecha=fecha,

        asistencia=asistencia,

        docente=docente

    )

    # =====================================
    # BUSCAR DOCENTE
    # =====================================

    docente = db.docentes.find_one({
        "usuario": usuario
    })

    if not docente:

        flash(
            "Docente no encontrado.",
            "danger"
        )

        return redirect(
            url_for("login")
        )

    docente_id = docente.get("_id")

    # =====================================
    # CLASES DEL DOCENTE
    # =====================================

    clases = list(
        db.asignaturas.find({
            "docente_id": docente_id,
            "activo": True
        })
    )

    # =====================================
    # GRADOS DISPONIBLES
    # =====================================

    grados = sorted(
        list({
            str(clase.get("grado"))
            for clase in clases
            if clase.get("grado") is not None
        })
    )

    # =====================================
    # DATOS RECIBIDOS
    # =====================================

    grado = request.args.get(
        "grado",
        ""
    ).strip()

    seccion = request.args.get(
        "seccion",
        ""
    ).strip()

    estudiante_id = request.args.get(
        "estudiante_id",
        ""
    ).strip()

    estudiantes = []

    estudiante = None

    incidencias = []

    asistencias = []

    # =====================================
    # BUSCAR ESTUDIANTES DEL GRADO
    # =====================================

    if grado:

        secciones_docente = list({
            clase.get("seccion")
            for clase in clases
            if str(clase.get("grado")) == grado
            and clase.get("seccion")
        })

        filtro_estudiantes = {
            "estado": "activo"
        }

        # ---------------------------------
        # FORMATO DEL GRADO
        # ---------------------------------

        mapa_grados = {
            "1": ["1", "1ro", "1ro Grado", "1er Grado"],
            "2": ["2", "2do", "2do Grado"],
            "3": ["3", "3ro", "3ro Grado", "3er Grado"],
            "4": ["4", "4to", "4to Grado"],
            "5": ["5", "5to", "5to Grado"],
            "6": ["6", "6to", "6to Grado"],
            "I Nivel": ["I Nivel"],
            "II Nivel": ["II Nivel"],
            "III Nivel": ["III Nivel"],
            "Primer Año": ["Primer Año"],
            "Segundo Año": ["Segundo Año"],
            "Tercer Año": ["Tercer Año"],
            "Cuarto Año": ["Cuarto Año"],
            "Quinto Año": ["Quinto Año"]
        }

        grados_busqueda = mapa_grados.get(
            grado,
            [grado]
        )

        filtro_estudiantes["grado"] = {
            "$in": grados_busqueda
        }

        # ---------------------------------
        # SECCIÓN
        # ---------------------------------

        if seccion:

            filtro_estudiantes["seccion"] = seccion

        else:

            if secciones_docente:

                filtro_estudiantes["seccion"] = {
                    "$in": secciones_docente
                }

        estudiantes = list(
            db.estudiantes.find(
                filtro_estudiantes
            ).sort(
                "nombre",
                1
            )
        )

# =====================================
# CONSULTA DE ESTUDIANTES
# ASISTENCIA + INCIDENCIAS
# =====================================

@docente_bp.route(
    "/consulta-estudiantes"
)
@role_required("docente")
def consulta_estudiantes():

    print("========================================")
    print("🔎 CONSULTA DE ESTUDIANTES")
    print("========================================")

    usuario = session.get("usuario")

    # =====================================
    # BUSCAR DOCENTE
    # =====================================

    docente = db.docentes.find_one({
        "usuario": usuario
    })

    if not docente:

        flash(
            "Docente no encontrado.",
            "danger"
        )

        return redirect(
            url_for("login")
        )

    docente_id = docente.get("_id")

    print(
        "👨‍🏫 DOCENTE:",
        docente.get("nombre")
    )

    # =====================================
    # CLASES DEL DOCENTE
    # =====================================

    clases = list(
        db.asignaturas.find({
            "docente_id": docente_id,
            "activo": True
        })
    )

    total_asignaturas = len(clases)

    print(
        "📚 TOTAL CLASES:",
        total_asignaturas
    )

    # =====================================
    # OBTENER ESTUDIANTES DE SUS CLASES
    # =====================================

    estudiantes_docente = []

    ids_estudiantes = set()

    mapa_grados = {

        1: "1ro Grado",
        2: "2do Grado",
        3: "3ro Grado",
        4: "4to Grado",
        5: "5to Grado",
        6: "6to Grado",

        "1": "1ro Grado",
        "2": "2do Grado",
        "3": "3ro Grado",
        "4": "4to Grado",
        "5": "5to Grado",
        "6": "6to Grado",

        "I Nivel": "I Nivel",
        "II Nivel": "II Nivel",
        "III Nivel": "III Nivel",

        "Primer Año": "Primer Año",
        "Segundo Año": "Segundo Año",
        "Tercer Año": "Tercer Año",
        "Cuarto Año": "Cuarto Año",
        "Quinto Año": "Quinto Año"
    }

    for clase in clases:

        grado_clase = clase.get(
            "grado"
        )

        seccion_clase = clase.get(
            "seccion"
        )

        grado_estudiante = mapa_grados.get(
            grado_clase,
            grado_clase
        )

        print("----------------------------------------")

        print(
            "📚 CLASE:",
            clase.get("nombre")
        )

        print(
            "🎓 GRADO:",
            grado_estudiante
        )

        print(
            "🏫 SECCIÓN:",
            seccion_clase
        )

        estudiantes_clase = db.estudiantes.find({
            "grado": grado_estudiante,
            "seccion": seccion_clase,
            "estado": "activo"
        })

        for estudiante_db in estudiantes_clase:

            estudiante_id_db = str(
                estudiante_db.get("_id")
            )

            if estudiante_id_db not in ids_estudiantes:

                estudiantes_docente.append(
                    estudiante_db
                )

                ids_estudiantes.add(
                    estudiante_id_db
                )

    total_estudiantes = len(
        estudiantes_docente
    )

    print(
        "👥 TOTAL ESTUDIANTES:",
        total_estudiantes
    )

    # =====================================
    # GRADOS DISPONIBLES
    # =====================================

    grados = sorted(
        list({
            str(clase.get("grado"))
            for clase in clases
            if clase.get("grado") is not None
        })
    )

    # =====================================
    # FILTROS
    # =====================================

    grado = request.args.get(
        "grado",
        ""
    ).strip()

    seccion = request.args.get(
        "seccion",
        ""
    ).strip()

    estudiante_id = request.args.get(
        "estudiante_id",
        ""
    ).strip()

    # =====================================
    # ESTUDIANTES PARA EL FILTRO
    # =====================================

    estudiantes = []

    if grado:

        grado_busqueda = mapa_grados.get(
            grado,
            grado
        )

        filtro_estudiantes = {
            "grado": grado_busqueda,
            "estado": "activo"
        }

        if seccion:

            filtro_estudiantes[
                "seccion"
            ] = seccion

        estudiantes = list(
            db.estudiantes.find(
                filtro_estudiantes
            ).sort(
                "nombre",
                1
            )
        )

    else:

        estudiantes = estudiantes_docente

    # =====================================
    # ESTUDIANTE SELECCIONADO
    # =====================================

    estudiante = None

    incidencias = []

    asistencias = []

    if estudiante_id:

        estudiante = db.estudiantes.find_one({
            "_id": estudiante_id,
            "estado": "activo"
        })

        # =================================
        # VERIFICAR QUE PERTENEZCA AL DOCENTE
        # =================================

        estudiante_permitido = False

        if estudiante:

            for estudiante_docente in estudiantes_docente:

                if str(
                    estudiante_docente.get("_id")
                ) == str(estudiante_id):

                    estudiante_permitido = True

                    break

        if not estudiante_permitido:

            estudiante = None

            flash(
                "El estudiante seleccionado no pertenece a una de tus clases.",
                "warning"
            )

        # =================================
        # CONSULTAR INCIDENCIAS
        # =================================

        if estudiante:

            incidencias = list(
                db.incidencias.find({
                    "estudiante_id": str(
                        estudiante_id
                    )
                }).sort(
                    "fecha",
                    -1
                )
            )

            # =================================
            # CONSULTAR ASISTENCIA
            # =================================

            asistencias = list(
                db.asistencias.find({
                    "estudiante_id": estudiante_id
                }).sort(
                    "fecha",
                    -1
                )
            )

    # =====================================
    # RESUMEN DE ASISTENCIA
    # =====================================

    total_asistencias = len(
        asistencias
    )

    presentes = sum(
        1
        for asistencia in asistencias
        if asistencia.get("estado")
        == "Presente"
    )

    ausentes = sum(
        1
        for asistencia in asistencias
        if asistencia.get("estado")
        == "Ausente"
    )

    justificadas = sum(
        1
        for asistencia in asistencias
        if asistencia.get("estado")
        == "Justificada"
    )

    porcentaje_asistencia = 0

    if total_asistencias > 0:

        porcentaje_asistencia = round(
            (
                presentes /
                total_asistencias
            ) * 100,
            1
        )

    # =====================================
    # CONTADORES DEL DASHBOARD
    # =====================================

    total_incidencias = db.incidencias.count_documents({
        "docente": usuario
    })

    total_comunicaciones = db.conversaciones.count_documents({
        "docente_id": docente_id
    })

    mensajes_pendientes = db.conversaciones.count_documents({
        "docente_id": docente_id,
        "no_leidos_docente": {
            "$gt": 0
        }
    })

    # =====================================
    # CONVERSACIONES
    # =====================================

    conversaciones = list(
        db.conversaciones.find({
            "docente_id": docente_id
        }).sort(
            "ultima_actualizacion",
            -1
        )
    )

    # =====================================
    # DATOS DEL DASHBOARD
    # =====================================

    estadistica = {

        "total_asignaturas":
            total_asignaturas,

        "total_estudiantes":
            total_estudiantes,

        "incidencias":
            total_incidencias,

        "comunicaciones":
            total_comunicaciones,

        "promedio_general":
            "0.0",

        "progreso_notas":
            0,

        "progreso_asistencia":
            0,

        "aprobados":
            0,

        "reprobados":
            0,

        "presentes":
            0
    }

    # =====================================
    # AVISOS
    # =====================================

    avisos = [

        "Recuerda registrar la asistencia diariamente.",

        "Mantén actualizadas las calificaciones.",

        "Consulta las incidencias de tus estudiantes."

    ]

    # =====================================
    # PENDIENTES
    # =====================================

    pendientes = []

    # =====================================
    # CLASES DE HOY
    # =====================================

    clases_hoy = clases

    # =====================================
    # RENDERIZAR CONSULTA
    # =====================================

    return render_template(
        "docente/consulta_estudiantes.html",

        docente=docente,

        clases=clases,

        grados=grados,

        grado=grado,

        seccion=seccion,

        estudiantes=estudiantes,

        estudiante=estudiante,

        incidencias=incidencias,

        asistencias=asistencias,

        total_asistencias=total_asistencias,

        presentes=presentes,

        ausentes=ausentes,

        justificadas=justificadas,

        porcentaje_asistencia=porcentaje_asistencia
    )

    
# =====================================
# NOTAS
# =====================================

@docente_bp.route("/notas/<asignatura_id>")
@role_required("docente")
def notas(asignatura_id):

    print("========================================")
    print("📝 NOTAS")
    print("ASIGNATURA ID:", asignatura_id)
    print("========================================")

    # =====================================
    # BUSCAR ASIGNATURA
    # =====================================

    asignatura = db.asignaturas.find_one({
        "_id": asignatura_id
    })

    print("📚 ASIGNATURA:", asignatura)

    if not asignatura:

        flash(
            "Asignatura no encontrada",
            "danger"
        )

        return redirect(
            url_for("docente.aulas")
        )

    grado = asignatura.get("grado")
    seccion = asignatura.get("seccion")

    print("🎓 GRADO:", grado)
    print("🏫 SECCIÓN:", seccion)


    # =====================================
    # CONVERTIR GRADO
    # =====================================

    mapa_grados = {

        "1": "1er Grado",
        "2": "2do Grado",
        "3": "3er Grado",
        "4": "4to Grado",
        "5": "5to Grado",
        "6": "6to Grado"

    }

    grado_estudiante = mapa_grados.get(
        str(grado),
        grado
    )

    print(
        "🔄 GRADO PARA ESTUDIANTES:",
        grado_estudiante
    )


    # =====================================
    # BUSCAR ESTUDIANTES
    # =====================================

    estudiantes = list(
        db.estudiantes.find({

            "grado": grado_estudiante,

            "seccion": seccion,

            "estado": "activo"

        })
    )


    print("👥 TOTAL ESTUDIANTES:", len(estudiantes))


    # =====================================
    # BUSCAR NOTAS EXISTENTES
    # =====================================

    notas_cortes = db.notas.find_one({

        "asignatura_id": asignatura_id

    })


    corte1 = 0
    corte2 = 0
    corte3 = 0
    corte4 = 0


    if notas_cortes:

        corte1 = notas_cortes.get(
            "corte1",
            0
        )

        corte2 = notas_cortes.get(
            "corte2",
            0
        )

        corte3 = notas_cortes.get(
            "corte3",
            0
        )

        corte4 = notas_cortes.get(
            "corte4",
            0
        )


    # =====================================
    # NOTA FINAL
    # =====================================

    nota_final = round(

        (
            corte1 +
            corte2 +
            corte3 +
            corte4
        ) / 4,

        2

    )


    # =====================================
    # MOSTRAR PANTALLA
    # =====================================

    return render_template(

        "docente/notas.html",

        asignatura=asignatura,

        estudiantes=estudiantes,

        corte1=corte1,

        corte2=corte2,

        corte3=corte3,

        corte4=corte4,

        nota_final=nota_final

    )

# =====================================
# GUARDAR NOTAS
# =====================================

@docente_bp.route("/notas/guardar", methods=["POST"])
@role_required("docente")
def guardar_notas():

    print("========================================")
    print("💾 ENTRE A guardar_notas")
    print("========================================")

    # =====================================
    # DATOS DEL FORMULARIO
    # =====================================

    asignatura_id = request.form.get("asignatura_id")
    periodo = request.form.get("periodo")
    evaluacion = request.form.get("evaluacion")

    print("📚 ASIGNATURA ID:", asignatura_id)
    print("📅 PERIODO:", periodo)
    print("📊 EVALUACIÓN:", evaluacion)

    # =====================================
    # MOSTRAR FORMULARIO RECIBIDO
    # =====================================

    print("========================================")
    print("📦 DATOS RECIBIDOS DEL FORMULARIO")
    print("========================================")

    for clave, valor in request.form.items():

        print(
            "CAMPO:",
            clave,
            "| VALOR:",
            valor
        )

    print("========================================")

    # =====================================
    # BUSCAR ASIGNATURA
    # =====================================

    asignatura = db.asignaturas.find_one({
        "_id": asignatura_id
    })

    print(
        "📚 ASIGNATURA ENCONTRADA:",
        asignatura
    )

    if not asignatura:

        flash(
            "Asignatura no encontrada.",
            "danger"
        )

        return redirect(
            url_for("docente.aulas")
        )

    # =====================================
    # OBTENER GRADO Y SECCIÓN
    # =====================================

    mapa_grados = {

        "1": "1er Grado",
        "2": "2do Grado",
        "3": "3er Grado",
        "4": "4to Grado",
        "5": "5to Grado",
        "6": "6to Grado"

    }

    grado = asignatura.get("grado")

    seccion = asignatura.get("seccion")

    grado_estudiante = mapa_grados.get(
        str(grado),
        grado
    )

    print("🎓 GRADO ASIGNATURA:", grado)
    print("🎓 GRADO ESTUDIANTE:", grado_estudiante)
    print("🏫 SECCIÓN:", seccion)

    # =====================================
    # BUSCAR ESTUDIANTES
    # =====================================

    estudiantes = list(
        db.estudiantes.find({

            "grado": grado_estudiante,

            "seccion": seccion,

            "estado": "activo"

        })
    )

    print(
        "👥 ESTUDIANTES A PROCESAR:",
        len(estudiantes)
    )

    # =====================================
    # DETERMINAR CORTE
    # =====================================

    campo_corte = None

    if (
        periodo == "I Semestre"
        and
        evaluacion == "Primer Parcial"
    ):

        campo_corte = "corte1"

    elif (
        periodo == "I Semestre"
        and
        evaluacion == "Segundo Parcial"
    ):

        campo_corte = "corte2"

    elif (
        periodo == "II Semestre"
        and
        evaluacion == "Tercer Parcial"
    ):

        campo_corte = "corte3"

    elif (
        periodo == "II Semestre"
        and
        evaluacion == "Cuarto Parcial"
    ):

        campo_corte = "corte4"

    # =====================================
    # VALIDAR CORTE
    # =====================================

    if not campo_corte:

        print("❌ NO SE PUDO DETERMINAR EL CORTE")

        flash(
            "Debe seleccionar un período y una evaluación válidos.",
            "warning"
        )

        return redirect(
            url_for(
                "docente.notas",
                asignatura_id=asignatura_id
            )
        )

    print(
        "📌 CAMPO DE CORTE:",
        campo_corte
    )

    # =====================================
    # GUARDAR NOTAS
    # =====================================

    guardados = 0

    for estudiante in estudiantes:

        estudiante_id = str(
            estudiante.get("_id")
        )

        print("----------------------------------------")
        print(
            "👤 ESTUDIANTE:",
            estudiante.get("nombre")
        )
        print(
            "🆔 ID:",
            estudiante_id
        )

        # =================================
        # LEER EP1 - EP10
        # =================================

        acumulados = {}

        for numero in range(1, 11):

            campo = (
                f"ep{numero}_{estudiante_id}"
            )

            valor = request.form.get(
                campo,
                "0"
            )

            try:

                nota = float(valor)

            except (
                ValueError,
                TypeError
            ):

                nota = 0

            # =============================
            # VALIDAR 0 - 10
            # =============================

            if nota < 0:

                nota = 0

            if nota > 10:

                nota = 10

            acumulados[
                f"ep{numero}"
            ] = nota

            print(
                f"EP{numero}:",
                nota
            )

        # =================================
        # CALCULAR ACUMULADO
        # =================================

        acumulado = round(
            sum(
                acumulados.values()
            ),
            2
        )

        # =================================
        # CALCULAR PROMEDIO
        # =================================

        promedio = round(
            acumulado / 10,
            2
        )

        print(
            "📊 ACUMULADO:",
            acumulado
        )

        print(
            "📊 PROMEDIO:",
            promedio
        )

        print(
            "📌 CORTE:",
            campo_corte
        )

        # =================================
        # DATOS A GUARDAR
        # =================================

        datos_guardar = {

            "asignatura_id":
                asignatura_id,

            "estudiante_id":
                estudiante_id,

            "grado":
                grado_estudiante,

            "seccion":
                seccion,

            "periodo":
                periodo,

            "evaluacion":
                evaluacion,

            "docente":
                session.get("usuario"),

            "acumulado":
                acumulado,

            "promedio":
                promedio,

            "nota":
                acumulado,

            "estado":
                (
                    "Aprobado"
                    if acumulado >= 60
                    else "Reforzamiento"
                ),

            "fecha":
                datetime.now()
        }

        # =================================
        # AGREGAR EP1 - EP10
        # =================================

        datos_guardar.update(
            acumulados
        )

        # =================================
        # GUARDAR CORTE
        # =================================

        datos_guardar[
            campo_corte
        ] = acumulado

        # =================================
        # GUARDAR EN MONGODB
        # =================================

        resultado = db.notas.update_one(

            {
                "asignatura_id":
                    asignatura_id,

                "estudiante_id":
                    estudiante_id,

                "periodo":
                    periodo,

                "evaluacion":
                    evaluacion
            },

            {
                "$set":
                    datos_guardar
            },

            upsert=True
        )

        print(
            "📝 DOCUMENTOS MODIFICADOS:",
            resultado.modified_count
        )

        print(
            "🆕 DOCUMENTO CREADO:",
            resultado.upserted_id
        )

        print("----------------------------------------")

        guardados += 1

    # =====================================
    # RESULTADO FINAL
    # =====================================

    print("========================================")
    print(
        "✅ NOTAS PROCESADAS:",
        guardados
    )
    print(
        "📌 PERIODO:",
        periodo
    )
    print(
        "📊 EVALUACIÓN:",
        evaluacion
    )
    print(
        "📌 CORTE:",
        campo_corte
    )
    print("========================================")

    flash(
        f"Notas guardadas correctamente. "
        f"Registros: {guardados}",
        "success"
    )

    return redirect(
        url_for(
            "docente.notas",
            asignatura_id=asignatura_id
        )
    )
# ==========================================================
# REPORTE DE NOTAS POR PARCIAL
# ==========================================================

@docente_bp.route("/notas/reporte/<asignatura_id>")
@role_required("docente")
def ver_reporte_notas(asignatura_id):

    print("========================================")
    print("📊 REPORTE DE NOTAS")
    print("========================================")
    print("ASIGNATURA:", asignatura_id)

    # ------------------------------------------------------
    # BUSCAR ASIGNATURA
    # ------------------------------------------------------

    asignatura = db.asignaturas.find_one({
        "_id": asignatura_id
    })

    if not asignatura:

        flash(
            "Asignatura no encontrada.",
            "danger"
        )

        return redirect(
            url_for("docente.aulas")
        )

    # ------------------------------------------------------
    # GRADO Y SECCIÓN
    # ------------------------------------------------------

    mapa_grados = {
        "1": "1er Grado",
        "2": "2do Grado",
        "3": "3er Grado",
        "4": "4to Grado",
        "5": "5to Grado",
        "6": "6to Grado"
    }

    grado = asignatura.get("grado")
    seccion = asignatura.get("seccion")

    grado_estudiante = mapa_grados.get(
        str(grado),
        grado
    )

    # ------------------------------------------------------
    # ESTUDIANTES
    # ------------------------------------------------------

    estudiantes = list(
        db.estudiantes.find({
            "grado": grado_estudiante,
            "seccion": seccion,
            "estado": "activo"
        }).sort(
            "nombre",
            1
        )
    )

    print(
        "👥 ESTUDIANTES:",
        len(estudiantes)
    )

    # ------------------------------------------------------
    # NOTAS
    # ------------------------------------------------------

    notas = list(
        db.notas.find({
            "asignatura_id": asignatura_id
        })
    )

    print(
        "📝 REGISTROS DE NOTAS:",
        len(notas)
    )

    # ------------------------------------------------------
    # ORGANIZAR NOTAS
    # ------------------------------------------------------

    notas_por_estudiante = {}

    for nota in notas:

        estudiante_id = str(
            nota.get("estudiante_id")
        )

        notas_por_estudiante[
            estudiante_id
        ] = nota

    # ------------------------------------------------------
    # CREAR REPORTE
    # ------------------------------------------------------

    reporte = []

    for estudiante in estudiantes:

        estudiante_id = str(
            estudiante.get("_id")
        )

        nota = notas_por_estudiante.get(
            estudiante_id
        )

        if nota:

            reporte.append({

                "nombre": estudiante.get(
                    "nombre",
                    ""
                ),

                "periodo": nota.get(
                    "periodo",
                    "-"
                ),

                "evaluacion": nota.get(
                    "evaluacion",
                    "-"
                ),

                "acumulado": nota.get(
                    "acumulado",
                    0
                ),

                "promedio": nota.get(
                    "promedio",
                    0
                ),

                "estado": nota.get(
                    "estado",
                    "Pendiente"
                ),

                "corte1": nota.get(
                    "corte1",
                    "-"
                ),

                "corte2": nota.get(
                    "corte2",
                    "-"
                ),

                "corte3": nota.get(
                    "corte3",
                    "-"
                ),

                "corte4": nota.get(
                    "corte4",
                    "-"
                )

            })

        else:

            reporte.append({

                "nombre": estudiante.get(
                    "nombre",
                    ""
                ),

                "periodo": "-",

                "evaluacion": "-",

                "acumulado": 0,

                "promedio": 0,

                "estado": "Pendiente",

                "corte1": "-",

                "corte2": "-",

                "corte3": "-",

                "corte4": "-"

            })

    # ------------------------------------------------------
    # MOSTRAR REPORTE
    # ------------------------------------------------------

    return render_template(
        "docente/reporte_notas.html",
        asignatura=asignatura,
        estudiantes=estudiantes,
        reporte=reporte
    )
# ==========================================================
# DESCARGAR REPORTE DE NOTAS EN PDF
# ==========================================================

@docente_bp.route(
    "/notas/reporte/<asignatura_id>/descargar",
    methods=["GET"]
)
@role_required("docente")
def descargar_reporte_notas(asignatura_id):

    print("========================================")
    print("📥 DESCARGANDO REPORTE DE NOTAS EN PDF")
    print("========================================")
    print("ASIGNATURA:", asignatura_id)

    # ======================================================
    # BUSCAR ASIGNATURA
    # ======================================================

    asignatura = db.asignaturas.find_one({
        "_id": asignatura_id
    })

    if not asignatura:

        flash(
            "Asignatura no encontrada.",
            "danger"
        )

        return redirect(
            url_for("docente.aulas")
        )

    # ======================================================
    # MAPA DE GRADOS
    # ======================================================

    mapa_grados = {
        "1": "1er Grado",
        "2": "2do Grado",
        "3": "3er Grado",
        "4": "4to Grado",
        "5": "5to Grado",
        "6": "6to Grado"
    }

    grado = asignatura.get("grado")
    seccion = asignatura.get("seccion")

    grado_estudiante = mapa_grados.get(
        str(grado),
        grado
    )

    # ======================================================
    # BUSCAR ESTUDIANTES
    # ======================================================

    estudiantes = list(
        db.estudiantes.find({
            "grado": grado_estudiante,
            "seccion": seccion,
            "estado": "activo"
        }).sort(
            "nombre",
            1
        )
    )

    print(
        "👥 ESTUDIANTES:",
        len(estudiantes)
    )

    # ======================================================
    # BUSCAR TODAS LAS NOTAS
    # ======================================================

    notas = list(
        db.notas.find({
            "asignatura_id": asignatura_id
        })
    )

    print(
        "📝 REGISTROS DE NOTAS:",
        len(notas)
    )

    # ======================================================
    # ORGANIZAR NOTAS POR ESTUDIANTE
    # ======================================================

    notas_por_estudiante = {}

    for nota in notas:

        estudiante_id = str(
            nota.get("estudiante_id")
        )

        if estudiante_id not in notas_por_estudiante:

            notas_por_estudiante[
                estudiante_id
            ] = []

        notas_por_estudiante[
            estudiante_id
        ].append(nota)

    # ======================================================
    # CREAR PDF
    # ======================================================

    buffer = BytesIO()

    documento = SimpleDocTemplate(

        buffer,

        pagesize=landscape(letter),

        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=25

    )

    elementos = []

    estilos = getSampleStyleSheet()

    # ======================================================
    # ESTILOS
    # ======================================================

    titulo = ParagraphStyle(

        "TituloCIEM",

        parent=estilos["Title"],

        alignment=TA_CENTER,

        fontSize=18,

        leading=22,

        spaceAfter=5

    )

    subtitulo = ParagraphStyle(

        "SubtituloCIEM",

        parent=estilos["Normal"],

        alignment=TA_CENTER,

        fontSize=10,

        leading=14,

        spaceAfter=5

    )

    # ======================================================
    # ENCABEZADO
    # ======================================================

    elementos.append(
        Paragraph(
            "COLEGIO INTEGRAL EMANUEL",
            titulo
        )
    )

    elementos.append(
        Paragraph(
            "CIEM ACADÉMICO",
            titulo
        )
    )

    elementos.append(
        Paragraph(
            "REPORTE DE CALIFICACIONES",
            subtitulo
        )
    )

    elementos.append(
        Spacer(1, 8)
    )

    # ======================================================
    # INFORMACIÓN DE LA ASIGNATURA
    # ======================================================

    nombre_asignatura = asignatura.get(
        "nombre",
        "Sin asignatura"
    )

    docente_nombre = session.get(
        "usuario",
        "Docente"
    )

    informacion = [

        [
            Paragraph(
                f"<b>Asignatura:</b> "
                f"{nombre_asignatura}",
                estilos["Normal"]
            ),

            Paragraph(
                f"<b>Docente:</b> "
                f"{docente_nombre}",
                estilos["Normal"]
            )
        ],

        [
            Paragraph(
                f"<b>Grado:</b> "
                f"{grado_estudiante}",
                estilos["Normal"]
            ),

            Paragraph(
                f"<b>Sección:</b> "
                f"{seccion}",
                estilos["Normal"]
            )
        ]

    ]

    tabla_info = Table(
        informacion,
        colWidths=[350, 350]
    )

    tabla_info.setStyle(
        TableStyle([

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5
            )

        ])
    )

    elementos.append(
        tabla_info
    )

    elementos.append(
        Spacer(1, 10)
    )

    # ======================================================
    # TABLA PRINCIPAL
    # ======================================================

    datos = [

        [
            "#",
            "Estudiante",
            "I Corte",
            "II Corte",
            "III Corte",
            "IV Corte",
            "Nota Final",
            "Estado"
        ]

    ]

    suma_final = 0
    aprobados = 0
    reforzamiento = 0

    contador = 1

    # ======================================================
    # PROCESAR ESTUDIANTES
    # ======================================================

    for estudiante in estudiantes:

        estudiante_id = str(
            estudiante.get("_id")
        )

        lista_notas = notas_por_estudiante.get(
            estudiante_id,
            []
        )

        corte1 = None
        corte2 = None
        corte3 = None
        corte4 = None

        # ==================================================
        # RECUPERAR CORTES
        # ==================================================

        for nota in lista_notas:

            if nota.get("corte1") is not None:

                corte1 = nota.get(
                    "corte1"
                )

            if nota.get("corte2") is not None:

                corte2 = nota.get(
                    "corte2"
                )

            if nota.get("corte3") is not None:

                corte3 = nota.get(
                    "corte3"
                )

            if nota.get("corte4") is not None:

                corte4 = nota.get(
                    "corte4"
                )

        # ==================================================
        # CONVERTIR CORTES
        # ==================================================

        def convertir_nota(valor):

            if valor in (
                None,
                "",
                "-"
            ):

                return None

            try:

                return float(valor)

            except (
                ValueError,
                TypeError
            ):

                return None

        corte1 = convertir_nota(corte1)
        corte2 = convertir_nota(corte2)
        corte3 = convertir_nota(corte3)
        corte4 = convertir_nota(corte4)

        cortes = [
            corte1,
            corte2,
            corte3,
            corte4
        ]

        cortes_validos = [

            nota

            for nota in cortes

            if nota is not None

        ]

        # ==================================================
        # NOTA FINAL
        # ==================================================

        if cortes_validos:

            nota_final = round(

                sum(cortes_validos)
                /
                len(cortes_validos),

                2

            )

        else:

            nota_final = 0

        # ==================================================
        # ESTADO
        # ==================================================

        if not cortes_validos:

            estado = "Pendiente"

        elif nota_final >= 60:

            estado = "Aprobado"

            aprobados += 1

        else:

            estado = "Reforzamiento"

            reforzamiento += 1

        suma_final += nota_final

        # ==================================================
        # MOSTRAR "-" PARA CORTES SIN NOTA
        # ==================================================

        valor_corte1 = (
            f"{corte1:.2f}"
            if corte1 is not None
            else "-"
        )

        valor_corte2 = (
            f"{corte2:.2f}"
            if corte2 is not None
            else "-"
        )

        valor_corte3 = (
            f"{corte3:.2f}"
            if corte3 is not None
            else "-"
        )

        valor_corte4 = (
            f"{corte4:.2f}"
            if corte4 is not None
            else "-"
        )

        # ==================================================
        # AGREGAR FILA
        # ==================================================

        datos.append([

            contador,

            estudiante.get(
                "nombre",
                "Estudiante"
            ),

            valor_corte1,

            valor_corte2,

            valor_corte3,

            valor_corte4,

            f"{nota_final:.2f}",

            estado

        ])

        contador += 1

    # ======================================================
    # CREAR TABLA PDF
    # ======================================================

    tabla = Table(

        datos,

        repeatRows=1,

        colWidths=[
            30,
            230,
            70,
            70,
            70,
            70,
            75,
            90
        ]

    )

    tabla.setStyle(

        TableStyle([

            # ENCABEZADO
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#0f172a")
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, 0),
                8
            ),

            # DATOS
            (
                "FONTSIZE",
                (0, 1),
                (-1, -1),
                8
            ),

            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER"
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    colors.HexColor("#f1f5f9")
                ]
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6
            )

        ])

    )

    elementos.append(
        tabla
    )

    elementos.append(
        Spacer(1, 15)
    )

    # ======================================================
    # RESUMEN
    # ======================================================

    total_estudiantes = len(
        estudiantes
    )

    if total_estudiantes > 0:

        promedio_general = round(

            suma_final
            /
            total_estudiantes,

            2

        )

    else:

        promedio_general = 0

    resumen = Table(

        [[

            f"Total estudiantes: "
            f"{total_estudiantes}",

            f"Promedio general: "
            f"{promedio_general:.2f}",

            f"Aprobados: "
            f"{aprobados}",

            f"Reforzamiento: "
            f"{reforzamiento}"

        ]],

        colWidths=[
            175,
            175,
            175,
            175
        ]

    )

    resumen.setStyle(

        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                colors.HexColor("#e2e8f0")
            ),

            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER"
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, -1),
                "Helvetica-Bold"
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                9
            ),

            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                8
            )

        ])

    )

    elementos.append(
        resumen
    )

    elementos.append(
        Spacer(1, 10)
    )

    # ======================================================
    # PIE DEL REPORTE
    # ======================================================

    elementos.append(

        Paragraph(

            "Documento generado desde CIEM Académico",

            ParagraphStyle(

                "Pie",

                parent=estilos["Normal"],

                alignment=TA_CENTER,

                fontSize=8,

                textColor=colors.grey

            )

        )

    )

    # ======================================================
    # GENERAR PDF
    # ======================================================

    documento.build(
        elementos
    )

    buffer.seek(0)

    print(
        "✅ PDF GENERADO CORRECTAMENTE"
    )

    # ======================================================
    # NOMBRE DEL ARCHIVO
    # ======================================================

    nombre_archivo = (

        "Reporte_Notas_"
        +
        nombre_asignatura
        .replace(" ", "_")
        .replace("/", "_")
        +
        ".pdf"

    )

    # ======================================================
    # DESCARGAR
    # ======================================================

    return send_file(

        buffer,

        as_attachment=True,

        download_name=nombre_archivo,

        mimetype="application/pdf"

    )    
# =====================================
# AULAS DEL DOCENTE
# =====================================

@docente_bp.route("/aulas")
@role_required("docente")
def aulas():

    usuario = session.get("usuario")

    # =====================================
    # BUSCAR DOCENTE
    # =====================================

    docente = db.docentes.find_one({
        "usuario": usuario
    })

    if not docente:

        flash(
            "Docente no encontrado",
            "danger"
        )

        return redirect(
            url_for("login")
        )

    # =====================================
    # ID OFICIAL DEL DOCENTE
    # =====================================
    #
    # La colección asignaciones_clase
    # utiliza el formato:
    #
    # DOC012
    #
    # Por eso utilizamos el código
    # del docente y construimos el ID oficial.
    # =====================================

    codigo_docente = str(
        docente.get("codigo", "")
    ).strip()

    docente_id = f"DOC{codigo_docente}"

    # =====================================
    # OBTENER ASIGNACIONES DE CLASE
    # =====================================
    #
    # FUENTE OFICIAL:
    #
    # asignaciones_clase
    #
    # Ya no utilizamos:
    # - asignaturas
    # - asignaciones
    # - cursos
    #
    # La colección asignaciones_clase
    # contiene toda la información necesaria.
    # =====================================

    clases = list(
        db.asignaciones_clase.find({
            "docente_id": docente_id,
            "activo": True
        }).sort(
            [
                ("nivel", 1),
                ("grado", 1),
                ("seccion", 1),
                ("asignatura_nombre", 1)
            ]
        )
    )

    # =====================================
    # INFORMACIÓN DE DEPURACIÓN
    # =====================================

    print("")
    print("========================================================")
    print("🏫 AULAS DEL DOCENTE")
    print("========================================================")
    print("USUARIO:", usuario)
    print("DOCENTE:", docente.get("nombre"))
    print("DOCENTE ID:", docente_id)
    print("TOTAL AULAS:", len(clases))
    print("========================================================")

    for clase in clases:

        print(
            clase.get("_id"),
            "|",
            clase.get("asignatura_codigo"),
            "|",
            clase.get("asignatura_nombre"),
            "| NIVEL:",
            clase.get("nivel"),
            "| GRADO:",
            clase.get("grado"),
            "| SECCIÓN:",
            clase.get("seccion"),
            "| DOCENTE:",
            clase.get("docente_id")
        )

    print("========================================================")

    # =====================================
    # MOSTRAR AULAS
    # =====================================

    return render_template(
        "docente/aulas.html",
        clases=clases,
        docente=docente,
        docente_id=docente_id
    )


# =====================================
# ESTUDIANTES DEL DOCENTE
# =====================================

@docente_bp.route("/estudiantes")
@role_required("docente")
def estudiantes():

    usuario = session.get("usuario")

    # =====================================
    # BUSCAR DOCENTE
    # =====================================

    docente = db.docentes.find_one({
        "usuario": usuario
    })

    if not docente:

        flash(
            "Docente no encontrado",
            "danger"
        )

        return redirect(
            url_for("login")
        )

    # =====================================
    # TODOS LOS ESTUDIANTES
    # =====================================

    estudiantes = list(
        db.estudiantes.find({})
    )

    # =====================================
    # ORDENAR
    # =====================================

    estudiantes.sort(
        key=lambda estudiante: str(
            estudiante.get(
                "nombre",
                ""
            )
        ).lower()
    )

    # =====================================
    # TOTAL
    # =====================================

    total_estudiantes = len(
        estudiantes
    )

    # =====================================
    # DEBUG
    # =====================================

    print("")
    print("=====================================")
    print("👨‍🏫 ESTUDIANTES DEL DOCENTE")
    print("=====================================")
    print("DOCENTE:", docente.get("nombre"))
    print("USUARIO:", usuario)
    print(
        "ID DOCENTE:",
        docente.get("codigo")
    )
    print(
        "TOTAL ESTUDIANTES:",
        total_estudiantes
    )
    print("=====================================")

    # =====================================
    # RENDERIZAR
    # =====================================

    return render_template(
        "docente/estudiante.html",
        estudiantes=estudiantes,
        total_estudiantes=total_estudiantes,
        docente=docente
    )
# =====================================
# SELECCIONAR CLASE PARA ASISTENCIA
# =====================================

@docente_bp.route("/asistencia")
@role_required("docente")
def lista_asistencia():

    usuario = session.get("usuario")


    docente = db.docentes.find_one({
        "usuario": usuario
    })


    if not docente:

        flash(
            "Docente no encontrado",
            "danger"
        )

        return redirect(
            url_for("login")
        )



    clases = list(
        db.asignaturas.find({
            "docente_id": docente["_id"]
        })
    )



    return render_template(
        "docente/seleccionar_asistencia.html",
        clases=clases
    )


# =====================================
# SELECCIONAR CLASE PARA NOTAS
# =====================================

@docente_bp.route("/calificaciones")
@role_required("docente")
def lista_calificaciones():

    usuario = session.get("usuario")


    docente = db.docentes.find_one({
        "usuario": usuario
    })



    if not docente:

        flash(
            "Docente no encontrado",
            "danger"
        )

        return redirect(
            url_for("login")
        )



    clases = list(
        db.asignaturas.find({
            "docente_id": docente["_id"]
        })
    )



    return render_template(
        "docente/seleccionar_calificaciones.html",
        clases=clases
    )


# =====================================
# SELECCIONAR CLASE PARA INCIDENCIAS
# =====================================

@docente_bp.route("/incidencias")
@role_required("docente")
def lista_incidencias():

    print("========================================")
    print("⚠️ LISTA DE INCIDENCIAS")
    print("========================================")

    usuario = session.get("usuario")

    # =====================================
    # BUSCAR DOCENTE
    # =====================================

    docente = db.docentes.find_one({
        "usuario": usuario
    })

    if not docente:

        flash(
            "Docente no encontrado",
            "danger"
        )

        return redirect(
            url_for("login")
        )

    docente_id = docente.get("_id")

    print(
        "👨‍🏫 DOCENTE:",
        docente_id
    )

    # =====================================
    # BUSCAR CLASES DEL DOCENTE
    # =====================================

    clases = list(
        db.asignaturas.find({
            "docente_id": docente_id,
            "activo": True
        })
    )

    print(
        "📚 TOTAL DE CLASES:",
        len(clases)
    )

    for clase in clases:

        print(
            "CLASE:",
            clase.get("nombre"),
            "| GRADO:",
            clase.get("grado"),
            "| SECCIÓN:",
            clase.get("seccion")
        )

    # =====================================
    # MOSTRAR CLASES
    # =====================================

    return render_template(
        "docente/seleccionar_incidencias.html",
        clases=clases,
        docente=docente
    )
# =====================================
# GUARDAR ASISTENCIA
# =====================================

@docente_bp.route(
    "/asistencia/guardar",
    methods=["POST"]
)
@role_required("docente")
def guardar_asistencia():

    print("========================================")
    print("💾 GUARDANDO ASISTENCIA")
    print("========================================")

    # =====================================
    # DATOS GENERALES
    # =====================================

    asignatura_id = request.form.get(
        "asignatura_id"
    )

    fecha = request.form.get(
        "fecha"
    )

    if not fecha:

        fecha = datetime.now().strftime(
            "%Y-%m-%d"
        )

    usuario = session.get(
        "usuario"
    )

    print(
        "📚 ASIGNACIÓN:",
        asignatura_id
    )

    print(
        "📅 FECHA:",
        fecha
    )

    print(
        "👨‍🏫 USUARIO:",
        usuario
    )

    # =====================================
    # BUSCAR DOCENTE
    # =====================================

    docente = db.docentes.find_one({
        "usuario": usuario
    })

    if not docente:

        flash(
            "Docente no encontrado.",
            "danger"
        )

        return redirect(
            url_for("login")
        )

    # =====================================
    # ID OFICIAL DEL DOCENTE
    # =====================================

    codigo_docente = str(
        docente.get("codigo", "")
    ).strip()

    docente_id = f"DOC{codigo_docente}"

    print(
        "🆔 DOCENTE ID:",
        docente_id
    )

    # =====================================
    # BUSCAR ASIGNACIÓN DE CLASE
    # =====================================
    #
    # IMPORTANTE:
    #
    # Ya NO utilizamos:
    #
    # db.asignaturas
    #
    # La fuente oficial es:
    #
    # db.asignaciones_clase
    # =====================================

    asignacion = db.asignaciones_clase.find_one({

        "_id": asignatura_id,

        "docente_id": docente_id,

        "activo": True

    })

    print(
        "📚 ASIGNACIÓN ENCONTRADA:",
        asignacion
    )

    if not asignacion:

        flash(
            "Asignación de clase no encontrada.",
            "danger"
        )

        return redirect(
            url_for("docente.aulas")
        )

    # =====================================
    # DATOS DE LA ASIGNACIÓN
    # =====================================

    grado = asignacion.get(
        "grado"
    )

    seccion = asignacion.get(
        "seccion"
    )

    nivel = asignacion.get(
        "nivel"
    )

    asignatura_codigo = asignacion.get(
        "asignatura_codigo"
    )

    asignatura_nombre = asignacion.get(
        "asignatura_nombre"
    )

    print(
        "📚 CÓDIGO:",
        asignatura_codigo
    )

    print(
        "📚 NOMBRE:",
        asignatura_nombre
    )

    print(
        "🎓 NIVEL:",
        nivel
    )

    print(
        "🎓 GRADO:",
        grado
    )

    print(
        "🏫 SECCIÓN:",
        seccion
    )

    # =====================================
    # CONVERTIR GRADO
    # =====================================

    mapa_grados = {

        "1": "1er Grado",
        "2": "2do Grado",
        "3": "3er Grado",
        "4": "4to Grado",
        "5": "5to Grado",
        "6": "6to Grado"

    }

    grado_estudiante = mapa_grados.get(
        str(grado),
        grado
    )

    print(
        "🔄 GRADO PARA ESTUDIANTES:",
        grado_estudiante
    )

    # =====================================
    # BUSCAR ESTUDIANTES
    # =====================================

    estudiantes = list(
        db.estudiantes.find({

            "grado":
                grado_estudiante,

            "seccion":
                seccion,

            "estado":
                "activo"

        })
    )

    print(
        "👥 ESTUDIANTES ENCONTRADOS:",
        len(estudiantes)
    )

    # =====================================
    # ESTADOS PERMITIDOS
    # =====================================

    estados_validos = [

        "Presente",

        "Ausente",

        "Justificada"

    ]

    # =====================================
    # GUARDAR CADA ESTUDIANTE
    # =====================================

    for estudiante in estudiantes:

        estudiante_id = estudiante.get(
            "_id"
        )

        # =================================
        # ESTADO
        # =================================

        estado = request.form.get(
            f"estado_{estudiante_id}"
        )

        # =================================
        # MOTIVO
        # =================================

        motivo = request.form.get(
            f"motivo_{estudiante_id}",
            ""
        ).strip()

        print("----------------------------------------")

        print(
            "👤 ESTUDIANTE:",
            estudiante.get("nombre")
        )

        print(
            "🆔 ID:",
            estudiante_id
        )

        print(
            "📌 ESTADO:",
            repr(estado)
        )

        print(
            "📝 MOTIVO:",
            motivo
        )

        # =================================
        # VALIDAR ESTADO
        # =================================

        if estado not in estados_validos:

            print(
                "❌ ESTADO INVÁLIDO:",
                repr(estado)
            )

            flash(
                f"Estado inválido para {estudiante.get('nombre')}.",
                "danger"
            )

            return redirect(
                url_for(
                    "docente.asistencia",
                    asignatura_id=asignatura_id
                )
            )

        # =================================
        # MOTIVO SOLO PARA JUSTIFICADA
        # =================================

        if estado != "Justificada":

            motivo = ""

        # =================================
        # GUARDAR EN MONGODB
        # =================================

        resultado = db.asistencias.update_one(

            {

                "asignatura_id":
                    asignatura_id,

                "estudiante_id":
                    estudiante_id,

                "fecha":
                    fecha

            },

            {

                "$set": {

                    "asignatura_id":
                        asignatura_id,

                    "estudiante_id":
                        estudiante_id,

                    "fecha":
                        fecha,

                    "estado":
                        estado,

                    "motivo":
                        motivo,

                    "docente":
                        usuario,

                    "docente_id":
                        docente_id,

                    "grado":
                        grado_estudiante,

                    "seccion":
                        seccion,

                    "nivel":
                        nivel,

                    "asignatura_codigo":
                        asignatura_codigo,

                    "asignatura":
                        asignatura_nombre

                }

            },

            upsert=True

        )

        print(
            "💾 GUARDADO:",
            estudiante.get("nombre"),
            "| ESTADO:",
            estado
        )

        print(
            "MATCHED:",
            resultado.matched_count
        )

        print(
            "MODIFIED:",
            resultado.modified_count
        )

        print(
            "UPSERTED:",
            resultado.upserted_id
        )

    # =====================================
    # FINALIZAR
    # =====================================

    print("========================================")
    print("✅ ASISTENCIA GUARDADA CORRECTAMENTE")
    print("========================================")

    flash(
        "La asistencia se guardó correctamente.",
        "success"
    )

    return redirect(
        url_for(
            "docente.asistencia",
            asignatura_id=asignatura_id
        )
    )


# =====================================
# ESTUDIANTES DE UNA CLASE
# =====================================

@docente_bp.route(
    "/incidencias/<asignatura_id>"
)
@role_required("docente")
def incidencia(asignatura_id):

    print("========================================")
    print("⚠️ ESTUDIANTES PARA INCIDENCIAS")
    print("========================================")

    print(
        "📚 ASIGNATURA ID:",
        asignatura_id
    )

    usuario = session.get("usuario")

    # =====================================
    # BUSCAR DOCENTE
    # =====================================

    docente = db.docentes.find_one({
        "usuario": usuario
    })

    if not docente:

        flash(
            "Docente no encontrado",
            "danger"
        )

        return redirect(
            url_for("login")
        )

    docente_id = docente.get("_id")

    # =====================================
    # BUSCAR ASIGNATURA
    # =====================================

    asignatura = db.asignaturas.find_one({
        "_id": asignatura_id,
        "docente_id": docente_id
    })

    if not asignatura:

        flash(
            "La asignatura no existe o no está asignada a este docente.",
            "danger"
        )

        return redirect(
            url_for(
                "docente.lista_incidencias"
            )
        )

    # =====================================
    # DATOS DE LA ASIGNATURA
    # =====================================

    grado_asignatura = asignatura.get(
        "grado"
    )

    seccion = asignatura.get(
        "seccion"
    )

    print(
        "📘 ASIGNATURA:",
        asignatura.get("nombre")
    )

    print(
        "🎓 GRADO:",
        repr(grado_asignatura)
    )

    print(
        "📍 SECCIÓN:",
        repr(seccion)
    )

    # =====================================
    # CONVERSIÓN DE GRADOS
    # =====================================

    mapa_grados = {

        1: "1ro Grado",
        2: "2do Grado",
        3: "3ro Grado",
        4: "4to Grado",
        5: "5to Grado",
        6: "6to Grado",

        "1": "1ro Grado",
        "2": "2do Grado",
        "3": "3ro Grado",
        "4": "4to Grado",
        "5": "5to Grado",
        "6": "6to Grado",

        "1ro": "1ro Grado",
        "2do": "2do Grado",
        "3ro": "3ro Grado",
        "4to": "4to Grado",
        "5to": "5to Grado",
        "6to": "6to Grado",

        "1ro Grado": "1ro Grado",
        "2do Grado": "2do Grado",
        "3ro Grado": "3ro Grado",
        "4to Grado": "4to Grado",
        "5to Grado": "5to Grado",
        "6to Grado": "6to Grado",

        "I Nivel": "I Nivel",
        "II Nivel": "II Nivel",
        "III Nivel": "III Nivel",

        "Primer Año": "Primer Año",
        "Segundo Año": "Segundo Año",
        "Tercer Año": "Tercer Año",
        "Cuarto Año": "Cuarto Año",
        "Quinto Año": "Quinto Año"
    }

    grado_estudiante = mapa_grados.get(
        grado_asignatura,
        grado_asignatura
    )

    print(
        "🎓 GRADO PARA ESTUDIANTE:",
        repr(grado_estudiante)
    )

    # =====================================
    # BUSCAR ESTUDIANTES
    # =====================================

    estudiantes = list(
        db.estudiantes.find({
            "grado": grado_estudiante,
            "seccion": seccion,
            "estado": "activo"
        }).sort(
            "nombre",
            1
        )
    )

    print(
        "👥 TOTAL ESTUDIANTES:",
        len(estudiantes)
    )

    for estudiante in estudiantes:

        print(
            "ESTUDIANTE:",
            estudiante.get("_id"),
            "|",
            estudiante.get("nombre")
        )

    # =====================================
    # FECHA ACTUAL
    # =====================================

    fecha = datetime.now().strftime(
        "%Y-%m-%d"
    )

    # =====================================
    # IDs DE LOS ESTUDIANTES
    # =====================================

    ids_estudiantes = [
        str(
            estudiante.get("_id")
        )
        for estudiante in estudiantes
    ]

    # =====================================
    # INCIDENCIAS EXISTENTES
    # =====================================

    incidencias = list(
        db.incidencias.find({
            "docente": usuario,
            "estudiante_id": {
                "$in": ids_estudiantes
            },
            "asignatura_id": str(
                asignatura_id
            )
        }).sort(
            "fecha",
            -1
        )
    )

    # =====================================
    # MOSTRAR PÁGINA
    # =====================================

    return render_template(
        "docente/incidencias.html",

        asignatura=asignatura,

        clase=asignatura,

        estudiantes=estudiantes,

        incidencias=incidencias,

        docente=docente,

        fecha=fecha
    )

    # =====================================
    # MOSTRAR ESTUDIANTES
    # =====================================

    return render_template(
        "docente/incidencias.html",
        clase=clase,
        estudiantes=estudiantes,
        incidencias=incidencias,
        docente=docente
    )


# =====================================
# GUARDAR INCIDENCIA
# =====================================

@docente_bp.route(
    "/incidencias/guardar",
    methods=["POST"]
)
@role_required("docente")
def guardar_incidencia():

    print("========================================")
    print("💾 GUARDANDO INCIDENCIA")
    print("========================================")

    usuario = session.get("usuario")

    # =====================================
    # DATOS DEL FORMULARIO
    # =====================================

    estudiante_id = request.form.get(
        "estudiante_id",
        ""
    ).strip()

    tipo = request.form.get(
        "tipo",
        ""
    ).strip()

    descripcion = request.form.get(
        "descripcion",
        ""
    ).strip()

    fecha = request.form.get(
        "fecha",
        ""
    ).strip()

    asignatura_id = request.form.get(
        "asignatura_id",
        ""
    ).strip()

    print(
        "👤 ESTUDIANTE:",
        estudiante_id
    )

    print(
        "⚠️ TIPO:",
        tipo
    )

    print(
        "📝 DESCRIPCIÓN:",
        descripcion
    )

    print(
        "📅 FECHA:",
        fecha
    )

    print(
        "📚 ASIGNATURA:",
        asignatura_id
    )

    # =====================================
    # VALIDACIONES
    # =====================================

    if not estudiante_id:

        flash(
            "Debe seleccionar un estudiante.",
            "warning"
        )

        if asignatura_id:

            return redirect(
                url_for(
                    "docente.incidencia",
                    asignatura_id=asignatura_id
                )
            )

        return redirect(
            url_for(
                "docente.lista_incidencias"
            )
        )

    if not tipo:

        flash(
            "Debe seleccionar el tipo de incidencia.",
            "warning"
        )

        if asignatura_id:

            return redirect(
                url_for(
                    "docente.incidencia",
                    asignatura_id=asignatura_id
                )
            )

        return redirect(
            url_for(
                "docente.lista_incidencias"
            )
        )

    if not descripcion:

        flash(
            "Debe ingresar una descripción.",
            "warning"
        )

        if asignatura_id:

            return redirect(
                url_for(
                    "docente.incidencia",
                    asignatura_id=asignatura_id
                )
            )

        return redirect(
            url_for(
                "docente.lista_incidencias"
            )
        )

    # =====================================
    # VERIFICAR DOCENTE
    # =====================================

    docente = db.docentes.find_one({
        "usuario": usuario
    })

    if not docente:

        flash(
            "Docente no encontrado.",
            "danger"
        )

        return redirect(
            url_for("login")
        )

    docente_id = docente.get("_id")

    # =====================================
    # VERIFICAR ESTUDIANTE
    # =====================================

    estudiante = db.estudiantes.find_one({
        "_id": estudiante_id,
        "estado": "activo"
    })

    if not estudiante:

        flash(
            "El estudiante seleccionado no existe o está inactivo.",
            "danger"
        )

        if asignatura_id:

            return redirect(
                url_for(
                    "docente.incidencia",
                    asignatura_id=asignatura_id
                )
            )

        return redirect(
            url_for(
                "docente.lista_incidencias"
            )
        )

    # =====================================
    # VERIFICAR ASIGNATURA
    # =====================================

    clase = None

    if asignatura_id:

        clase = db.asignaturas.find_one({
            "_id": asignatura_id,
            "docente_id": docente_id
        })

        if not clase:

            flash(
                "La asignatura seleccionada no es válida.",
                "danger"
            )

            return redirect(
                url_for(
                    "docente.lista_incidencias"
                )
            )

    # =====================================
    # CREAR INCIDENCIA
    # =====================================

    incidencia = {

        "estudiante_id":
            estudiante_id,

        "estudiante_nombre":
            estudiante.get("nombre"),

        "docente":
            usuario,

        "docente_id":
            docente_id,

        "docente_nombre":
            docente.get("nombre"),

        "tipo":
            tipo,

        "descripcion":
            descripcion,

        "fecha":
            fecha,

        "asignatura_id":
            asignatura_id,

        "asignatura":
            clase.get("nombre")
            if clase
            else "",

        "grado":
            estudiante.get("grado"),

        "seccion":
            estudiante.get("seccion"),

        "estado":
            "pendiente",

        "fecha_registro":
            datetime.now()
    }

    # =====================================
    # GUARDAR EN MONGODB
    # =====================================

    resultado = db.incidencias.insert_one(
        incidencia
    )

    print(
        "✅ INCIDENCIA GUARDADA:",
        resultado.inserted_id
    )

    # =====================================
    # MENSAJE
    # =====================================

    flash(
        "Incidencia registrada correctamente.",
        "success"
    )

    # =====================================
    # REGRESAR A LA CLASE
    # =====================================

    if asignatura_id:

        return redirect(
            url_for(
                "docente.incidencia",
                asignatura_id=asignatura_id
            )
        )

    return redirect(
        url_for(
            "docente.lista_incidencias"
        )
    )


    # =====================================
    # BUSCAR ASIGNATURA
    # =====================================

    asignatura = db.asignaturas.find_one({

        "_id": asignatura_id

    })


    if not asignatura:

        flash(
            "Asignatura no encontrada.",
            "danger"
        )

        return redirect(
            url_for(
                "docente.lista_incidencias"
            )
        )


    print(
        "📚 ASIGNATURA:",
        asignatura
    )


    grado = asignatura.get(
        "grado"
    )

    seccion = asignatura.get(
        "seccion"
    )


    print(
        "🎓 GRADO ASIGNATURA:",
        grado
    )

    print(
        "🏫 SECCIÓN:",
        seccion
    )


    # =====================================
    # CONVERTIR GRADO
    # =====================================

    mapa_grados = {

        "1": "1er Grado",
        "2": "2do Grado",
        "3": "3er Grado",
        "4": "4to Grado",
        "5": "5to Grado",
        "6": "6to Grado"

    }


    grado_estudiante = mapa_grados.get(

        str(grado),

        grado

    )


    print(
        "🔄 GRADO BUSCADO:",
        grado_estudiante
    )


    # =====================================
    # BUSCAR ESTUDIANTES ACTIVOS
    # =====================================

    estudiantes = list(

        db.estudiantes.find({

            "grado":
                grado_estudiante,

            "seccion":
                seccion,

            "estado":
                "activo"

        })

    )


    print(
        "👥 TOTAL ESTUDIANTES:",
        len(estudiantes)
    )


    # =====================================
    # MOSTRAR ESTUDIANTES
    # =====================================

    return render_template(

        "docente/incidencias.html",

        asignatura=asignatura,

        estudiantes=estudiantes

    )


# =====================================
# COMUNICACION CON PADRES
# =====================================

@docente_bp.route("/comunicacion")
@role_required("docente")
def comunicacion():

    print("====================================")
    print("📨 COMUNICACIÓN CON PADRES")
    print("====================================")

    usuario = session.get("usuario")

    print("USUARIO DOCENTE:", usuario)

    # =====================================
    # BUSCAR DOCENTE
    # =====================================

    docente = db.docentes.find_one({
        "usuario": usuario
    })

    if not docente:

        print("❌ DOCENTE NO ENCONTRADO")

        flash(
            "Docente no encontrado.",
            "danger"
        )

        return redirect(
            url_for("login")
        )

    docente_id = docente.get("_id")

    print("DOCENTE ENCONTRADO:", docente.get("nombre"))
    print("ID DOCENTE:", docente_id)

    # =====================================
    # BUSCAR ASIGNATURAS DEL DOCENTE
    # =====================================

    clases = list(
        db.asignaturas.find({
            "docente_id": docente_id
        })
    )

    print("------------------------------------")
    print("📚 ASIGNATURAS DEL DOCENTE")
    print("CANTIDAD:", len(clases))

    for clase in clases:

        print(
            clase.get("_id"),
            "|",
            clase.get("nombre"),
            "| GRADO:",
            clase.get("grado"),
            "| SECCIÓN:",
            clase.get("seccion")
        )

    # =====================================
    # OBTENER GRADOS DEL DOCENTE
    # =====================================

    grados_docente = []

    for clase in clases:

        grado = clase.get("grado")

        if grado is not None:

            grado = str(
                grado
            ).strip()

            if grado not in grados_docente:

                grados_docente.append(
                    grado
                )

    print("------------------------------------")
    print("GRADOS DEL DOCENTE:")
    print(grados_docente)

    # =====================================
    # NORMALIZAR GRADOS
    # =====================================

    mapa_grados = {

        "1": "1ro Grado",
        "2": "2do Grado",
        "3": "3ro Grado",
        "4": "4to Grado",
        "5": "5to Grado",
        "6": "6to Grado",

        "01": "1ro Grado",
        "02": "2do Grado",
        "03": "3ro Grado",
        "04": "4to Grado",
        "05": "5to Grado",
        "06": "6to Grado"

    }

    grados_busqueda = []

    for grado in grados_docente:

        grado_normalizado = mapa_grados.get(
            grado,
            grado
        )

        if grado_normalizado not in grados_busqueda:

            grados_busqueda.append(
                grado_normalizado
            )

    print("------------------------------------")
    print("GRADOS PARA BUSCAR ESTUDIANTES:")
    print(grados_busqueda)

    # =====================================
    # BUSCAR ESTUDIANTES
    # =====================================

    estudiantes = []

    if grados_busqueda:

        estudiantes = list(
            db.estudiantes.find({
                "grado": {
                    "$in": grados_busqueda
                },
                "estado": "activo"
            })
        )

    print("------------------------------------")
    print("👨‍🎓 ESTUDIANTES PARA COMUNICACIÓN")
    print("CANTIDAD:", len(estudiantes))

    # =====================================
    # MOSTRAR ESTUDIANTES EN CONSOLA
    # =====================================

    for estudiante in estudiantes:

        print(
            "ID:",
            estudiante.get("_id"),
            "| NOMBRE:",
            estudiante.get("nombre"),
            "| GRADO:",
            estudiante.get("grado"),
            "| SECCIÓN:",
            estudiante.get("seccion"),
            "| MADRE USUARIO:",
            estudiante.get("madre_usuario")
        )

    print("====================================")

    return render_template(
        "docente/comunicacion.html",
        estudiantes=estudiantes,
        docente=docente
    )


# =====================================
# GUARDAR COMUNICACION
# =====================================

@docente_bp.route(
    "/comunicacion/guardar",
    methods=["POST"]
)
@role_required("docente")
def guardar_comunicacion():

    print("====================================")
    print("📨 GUARDANDO COMUNICACIÓN")
    print("====================================")

    # =====================================
    # DOCENTE
    # =====================================

    usuario_docente = session.get(
        "usuario"
    )

    print(
        "USUARIO DOCENTE:",
        usuario_docente
    )

    # =====================================
    # DATOS DEL FORMULARIO
    # =====================================

    estudiante_id = request.form.get(
        "estudiante",
        ""
    ).strip()

    mensaje_texto = request.form.get(
        "mensaje",
        ""
    ).strip()

    print(
        "ESTUDIANTE ID:",
        estudiante_id
    )

    print(
        "MENSAJE:",
        mensaje_texto
    )

    # =====================================
    # VALIDAR ESTUDIANTE
    # =====================================

    if not estudiante_id:

        flash(
            "Debe seleccionar un estudiante.",
            "warning"
        )

        return redirect(
            url_for(
                "docente.comunicacion"
            )
        )

    # =====================================
    # VALIDAR MENSAJE
    # =====================================

    if not mensaje_texto:

        flash(
            "Debe escribir un mensaje.",
            "warning"
        )

        return redirect(
            url_for(
                "docente.comunicacion"
            )
        )

    # =====================================
    # BUSCAR ESTUDIANTE
    # =====================================

    estudiante = db.estudiantes.find_one({
        "_id": estudiante_id,
        "estado": "activo"
    })

    if not estudiante:

        print(
            "❌ ESTUDIANTE NO ENCONTRADO"
        )

        flash(
            "No se encontró el estudiante.",
            "danger"
        )

        return redirect(
            url_for(
                "docente.comunicacion"
            )
        )

    print("------------------------------------")
    print("✅ ESTUDIANTE ENCONTRADO")
    print(
        "ID:",
        estudiante.get("_id")
    )
    print(
        "NOMBRE:",
        estudiante.get("nombre")
    )
    print(
        "MADRE:",
        estudiante.get("madre")
    )
    print(
        "TUTOR:",
        estudiante.get("tutor")
    )
    print(
        "MADRE_USUARIO:",
        estudiante.get("madre_usuario")
    )

    # =====================================
    # OBTENER USUARIO DE LA MADRE
    # =====================================

    madre_usuario = estudiante.get(
        "madre_usuario"
    )

    if not madre_usuario:

        print(
            "❌ EL ESTUDIANTE NO TIENE madre_usuario"
        )

        flash(
            "Este estudiante no tiene una madre/tutora vinculada al sistema.",
            "danger"
        )

        return redirect(
            url_for(
                "docente.comunicacion"
            )
        )

    madre_usuario = str(
        madre_usuario
    ).strip()

    print(
        "USUARIO MADRE:",
        madre_usuario
    )

    # =====================================
    # BUSCAR USUARIO MADRE
    # =====================================

    usuario_madre = db.usuarios.find_one({
        "usuario": madre_usuario,
        "rol": "padre",
        "activo": True
    })

    print("------------------------------------")
    print("USUARIO MADRE EN MONGODB:")
    print(usuario_madre)

    if not usuario_madre:

        print(
            "❌ NO EXISTE USUARIO MADRE"
        )

        flash(
            "No se encontró la cuenta de la madre/tutora.",
            "danger"
        )

        return redirect(
            url_for(
                "docente.comunicacion"
            )
        )

    # =====================================
    # DATOS DEL DOCENTE
    # =====================================

    docente = db.docentes.find_one({
        "usuario": usuario_docente
    })

    if not docente:

        flash(
            "No se encontró el docente.",
            "danger"
        )

        return redirect(
            url_for(
                "login"
            )
        )

    docente_id = docente.get(
        "_id"
    )

    nombre_docente = (
        docente.get("nombre")
        or usuario_docente
    )

    # =====================================
    # NOMBRE DE LA MADRE
    # =====================================

    nombre_madre = (
        usuario_madre.get("nombre")
        or usuario_madre.get("nombre_completo")
        or madre_usuario
    )

    # =====================================
    # BUSCAR CONVERSACIÓN EXISTENTE
    # =====================================

    conversacion = db.conversaciones.find_one({

        "estudiante_id": estudiante_id,

        "docente_id": docente_id,

        "madre_usuario": madre_usuario

    })

    # =====================================
    # CREAR CONVERSACIÓN
    # =====================================

    if not conversacion:

        conversacion = {

            "estudiante_id":
                estudiante_id,

            "docente_id":
                docente_id,

            "estudiante":
                estudiante.get("nombre"),

            "docente":
                nombre_docente,

            "madre":
                nombre_madre,

            "madre_usuario":
                madre_usuario,

            "ultimo_mensaje":
                mensaje_texto,

            "fecha_creacion":
                datetime.now(),

            "ultima_actualizacion":
                datetime.now(),

            "no_leidos_docente":
                0,

            "no_leidos_padre":
                1

        }

        resultado_conversacion = (
            db.conversaciones.insert_one(
                conversacion
            )
        )

        conversacion_id = (
            resultado_conversacion.inserted_id
        )

        print(
            "✅ CONVERSACIÓN CREADA:",
            conversacion_id
        )

    else:

        conversacion_id = (
            conversacion.get("_id")
        )

        print(
            "✅ CONVERSACIÓN EXISTENTE:",
            conversacion_id
        )

        # =================================
        # ACTUALIZAR CONVERSACIÓN
        # =================================

        db.conversaciones.update_one(

            {
                "_id":
                    conversacion_id
            },

            {
                "$set": {

                    "ultimo_mensaje":
                        mensaje_texto,

                    "ultima_actualizacion":
                        datetime.now()

                },

                "$inc": {

                    "no_leidos_padre":
                        1

                }

            }

        )

     # =====================================
    # GUARDAR MENSAJE
    # =====================================

    print("🚨 LLEGAMOS A GUARDAR EL MENSAJE")
    print("MADRE USUARIO:", madre_usuario)
    print("ESTUDIANTE ID:", estudiante_id)
    print("DOCENTE ID:", docente_id)
    print("MENSAJE:", mensaje_texto)

    mensaje = {

        "conversacion_id":
            conversacion_id,

        "estudiante_id":
            estudiante_id,

        "docente_id":
            docente_id,

        "madre_usuario":
            madre_usuario,

        "emisor":
            usuario_docente,

        "mensaje":
            mensaje_texto,

        "fecha":
            datetime.now(),

        "leido":
            False
    }

    resultado_mensaje = db.mensajes.insert_one(
        mensaje
    )

    print("------------------------------------")
    print("✅ MENSAJE GUARDADO")
    print("ID MENSAJE:", resultado_mensaje.inserted_id)
    print("DESTINATARIO:", madre_usuario)
    print("ESTUDIANTE:", estudiante.get("nombre"))
    print("====================================")

    flash(
        f"Mensaje enviado correctamente a {nombre_madre}.",
        "success"
    )

    return redirect(
        url_for("docente.comunicacion")
    )

# ======================================================
#                INFORMES MINED
# ======================================================

@docente_bp.route("/informes")
@role_required("docente")
def informes_mined():

    return render_template(
        "docente/informes_mined.html"
    )


# ======================================================
# INFORME DE RETENCIÓN
# ======================================================

def informe_retencion():

    grados = [

        "I Nivel",
        "II Nivel",
        "III Nivel",

        "1",
        "2",
        "3",
        "4",
        "5",
        "6",

        "7",
        "8",
        "9",

        "10",
        "11"

    ]

    detalle = []

    total_matricula = 0
    total_actual = 0
    total_retiros = 0
    total_ingresos = 0

    for grado in grados:

        matricula = db.estudiantes.count_documents({

            "grado": grado

        })

        activos = db.estudiantes.count_documents({

            "grado": grado,

            "estado": "activo"

        })

        retiros = db.estudiantes.count_documents({

            "grado": grado,

            "estado": "retirado"

        })

        ingresos = 0

        incorporaciones = 0

        if matricula > 0:

            porcentaje = round(

                (activos / matricula) * 100,

                2

            )

        else:

            porcentaje = 0

        detalle.append({

            "grado": grado,

            "matricula_inicial": matricula,

            "nuevo_ingreso": ingresos,

            "matricula_total": matricula + ingresos,

            "retiros": retiros,

            "incorporaciones": incorporaciones,

            "matricula_actual": activos,

            "porcentaje": porcentaje

        })

        total_matricula += matricula
        total_actual += activos
        total_retiros += retiros
        total_ingresos += ingresos

    if total_matricula > 0:

        porcentaje_general = round(

            (total_actual / total_matricula) * 100,

            2

        )

    else:

        porcentaje_general = 0

    return {

        "detalle": detalle,

        "totales": {

            "matricula_inicial": total_matricula,

            "nuevo_ingreso": total_ingresos,

            "matricula_total": total_matricula + total_ingresos,

            "retiros": total_retiros,

            "incorporaciones": 0,

            "matricula_actual": total_actual,

            "porcentaje": porcentaje_general

        }

    }


# ======================================================
# VISTA PREVIA DEL INFORME
# ======================================================

@docente_bp.route("/informes/retencion")
@role_required("docente")
def vista_retencion():

    datos = informe_retencion()

    return render_template(

        "docente/retencion.html",

        detalle=datos["detalle"],

        totales=datos["totales"]

    )


# ======================================================
# PDF INFORME MINED
# ======================================================

@docente_bp.route("/informes/retencion/pdf")
@role_required("docente")
def reporte_mined_pdf():

    datos = informe_retencion()

    detalle = datos["detalle"]

    totales = datos["totales"]

    archivo = "Retencion_MINED.pdf"

    doc = SimpleDocTemplate(archivo)

    elementos = []

    estilos = getSampleStyleSheet()

    elementos.append(

        Paragraph(

            "<b>COLEGIO INTEGRAL EMANUEL</b>",

            estilos["Title"]

        )

    )

    elementos.append(

        Paragraph(

            "INFORME OFICIAL DE RETENCIÓN ESCOLAR",

            estilos["Heading2"]

        )

    )

    elementos.append(Spacer(1,20))

    tabla = [[

        "Grado",

        "Matrícula Inicial",

        "Nuevo Ingreso",

        "Matrícula Total",

        "Retiros",

        "Incorporaciones",

        "Matrícula Actual",

        "%"

    ]]

    for fila in detalle:

        tabla.append([

            fila["grado"],

            fila["matricula_inicial"],

            fila["nuevo_ingreso"],

            fila["matricula_total"],

            fila["retiros"],

            fila["incorporaciones"],

            fila["matricula_actual"],

            f'{fila["porcentaje"]}%'

        ])

    tabla.append([

        "TOTAL",

        totales["matricula_inicial"],

        totales["nuevo_ingreso"],

        totales["matricula_total"],

        totales["retiros"],

        totales["incorporaciones"],

        totales["matricula_actual"],

        f'{totales["porcentaje"]}%'

    ])

    t = Table(tabla)

    t.setStyle(

        TableStyle([

            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#0D2A52")),

            ("TEXTCOLOR",(0,0),(-1,0),colors.white),

            ("GRID",(0,0),(-1,-1),0.5,colors.black),

            ("ALIGN",(0,0),(-1,-1),"CENTER"),

            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),

            ("BACKGROUND",(0,-1),(-1,-1),colors.lightgrey)

        ])

    )

    elementos.append(t)

    doc.build(elementos)

    return send_file(

        archivo,

        as_attachment=True

    )



# ======================================================
# INFORME RENDIMIENTO ACADÉMICO
# ======================================================

def informe_rendimiento():

    grados = [

        "I Nivel",
        "II Nivel",
        "III Nivel",

        "1",
        "2",
        "3",
        "4",
        "5",
        "6",

        "7",
        "8",
        "9",

        "10",
        "11"

    ]


    detalle = []

    asignaturas_detalle = []


    estudiantes_global = set()


    for grado in grados:


        notas_grado = list(

            db.notas.find({

                "grado": grado,

                "año_lectivo": "2026"

            })

        )


        estudiantes = set()



        for nota in notas_grado:

            estudiantes.add(
                nota.get("estudiante_id")
            )

            estudiantes_global.add(
                nota.get("estudiante_id")
            )



        aprobados = 0

        reprobados = 0

        suma_promedios = 0



        for estudiante in estudiantes:


            notas_estudiante = list(

                db.notas.find({

                    "estudiante_id": estudiante,

                    "grado": grado,

                    "año_lectivo":"2026"

                })

            )



            if notas_estudiante:


                promedio_estudiante = round(

                    sum(

                        n.get("promedio",0)

                        for n in notas_estudiante

                    )

                    /

                    len(notas_estudiante),

                    2

                )



                suma_promedios += promedio_estudiante



                if promedio_estudiante >= 6:

                    aprobados += 1

                else:

                    reprobados += 1




        cantidad = len(estudiantes)



        promedio_grado = 0


        if cantidad > 0:


            promedio_grado = round(

                suma_promedios / cantidad,

                2

            )



        detalle.append({

            "grado": grado,

            "estudiantes": cantidad,

            "promedio": promedio_grado,

            "aprobados": aprobados,

            "reprobados": reprobados

        })


        # ==========================================
        # RENDIMIENTO POR ASIGNATURA
        # ==========================================


        asignaturas = db.notas.distinct(

            "asignatura_nombre",

            {

                "grado": grado,

                "año_lectivo": "2026"

            }

        )


        for asignatura in asignaturas:


            registros = list(

                db.notas.find({

                    "grado": grado,

                    "asignatura_nombre": asignatura,

                    "año_lectivo": "2026"

                })

            )


            if registros:


                promedio_asignatura = round(

                    sum(

                        n.get("promedio",0)

                        for n in registros

                    )

                    /

                    len(registros),

                    2

                )


                asignaturas_detalle.append({

                    "grado": grado,

                    "asignatura": asignatura,

                    "promedio": promedio_asignatura

                })

    # ==========================================
    # TOTALES GENERALES
    # ==========================================


    promedio_general = 0


    if detalle:

        promedio_general = round(

            sum(

                item["promedio"]

                for item in detalle

            )
            /

            len(detalle),

            2

        )



    return {


        "detalle": detalle,


        "asignaturas": asignaturas_detalle,


        "totales": {


            "estudiantes": len(estudiantes_global),


            "promedio_general": promedio_general


        }


    }

# ======================================================
# VISTA RENDIMIENTO
# ======================================================

@docente_bp.route("/informes/rendimiento")
@role_required("docente")
def vista_rendimiento():

    datos = informe_rendimiento()

    return render_template(
        "docente/rendimiento.html",
        detalle=datos.get("detalle", []),
        asignaturas=datos.get("asignaturas", []),
        totales=datos.get("totales", {})
    )


# ======================================================
# PDF RENDIMIENTO ACADÉMICO
# ======================================================
print("CARGANDO INFORME RENDIMIENTO")
@docente_bp.route("/informes/rendimiento/pdf")
@role_required("docente")
def reporte_rendimiento_pdf():

    datos = informe_rendimiento()

    archivo = "Rendimiento_Academico_CIEM.pdf"

    doc = SimpleDocTemplate(
        archivo,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    elementos = []

    estilos = getSampleStyleSheet()

    # aquí continúa tu código para crear el PDF

    # ==========================================
    # ENCABEZADO CON LOGOS
    # ==========================================


    logo_ciem = Image(

        "static/img/logo.jpg",

        width=70,

        height=70

    )


    logo_mined = Image(

    "static/img/MINED.jpg",

    width=70,

    height=70

)



    titulo = Paragraph(

        """
        <b>COLEGIO INTEGRAL EMANUEL</b><br/>
        INFORME DE RENDIMIENTO ACADÉMICO<br/>
        Año Lectivo 2026
        """,

        estilos["Title"]

    )



    encabezado = Table(

        [

            [

                logo_ciem,

                titulo,

                logo_mined

            ]

        ],

        colWidths=[90,300,90]

    )



    encabezado.setStyle(

        TableStyle([

            (
                "VALIGN",
                (0,0),
                (-1,-1),
                "MIDDLE"
            ),

            (
                "ALIGN",
                (0,0),
                (-1,-1),
                "CENTER"
            )

        ])

    )



    elementos.append(encabezado)


    elementos.append(

        Spacer(1,20)

    )



    # ==========================================
    # TABLA RESUMEN POR GRADO
    # ==========================================


    elementos.append(

        Paragraph(

            "Resumen por grado",

            estilos["Heading2"]

        )

    )


    tabla_grado = [

        [

            "Grado",

            "Estudiantes",

            "Promedio",

            "Aprobados",

            "Reprobados"

        ]

    ]



    for fila in datos["detalle"]:


        tabla_grado.append(

            [

                fila["grado"],

                fila["estudiantes"],

                fila["promedio"],

                fila["aprobados"],

                fila["reprobados"]

            ]

        )



    tabla1 = Table(tabla_grado)



    tabla1.setStyle(

        TableStyle([


            (
                "GRID",
                (0,0),
                (-1,-1),
                0.5,
                colors.black
            ),


            (
                "BACKGROUND",
                (0,0),
                (-1,0),
                colors.lightgrey
            ),


            (
                "ALIGN",
                (0,0),
                (-1,-1),
                "CENTER"
            )


        ])

    )


    elementos.append(tabla1)


    elementos.append(

        Spacer(1,20)

    )



    # ==========================================
    # TABLA POR ASIGNATURA
    # ==========================================


    elementos.append(

        Paragraph(

            "Rendimiento por asignatura",

            estilos["Heading2"]

        )

    )



    tabla_asignaturas = [

        [

            "Grado",

            "Asignatura",

            "Promedio"

        ]

    ]



    for fila in datos["asignaturas"]:


        tabla_asignaturas.append(

            [

                fila["grado"],

                fila["asignatura"],

                fila["promedio"]

            ]

        )



    tabla2 = Table(tabla_asignaturas)



    tabla2.setStyle(

        TableStyle([


            (
                "GRID",
                (0,0),
                (-1,-1),
                0.5,
                colors.black
            ),


            (
                "BACKGROUND",
                (0,0),
                (-1,0),
                colors.lightgrey
            ),


            (
                "ALIGN",
                (0,0),
                (-1,-1),
                "CENTER"
            )


        ])

    )



    elementos.append(tabla2)


    elementos.append(

        Spacer(1,20)

    )



    # ==========================================
    # TOTALES
    # ==========================================


    elementos.append(

        Paragraph(

            f"""
            <b>Total estudiantes evaluados:</b>
            {datos["totales"]["estudiantes"]}
            <br/>
            <b>Promedio general:</b>
            {datos["totales"]["promedio_general"]}
            """,

            estilos["Normal"]

        )

    )



    doc.build(elementos)



    return send_file(

        archivo,

        as_attachment=True

    )
# ======================================================
#        INFORME PROMOCIÓN ESCOLAR
# ======================================================


def informe_promocion():


    grados = [

        "I Nivel",
        "II Nivel",
        "III Nivel",

        "1",
        "2",
        "3",
        "4",
        "5",
        "6",

        "7",
        "8",
        "9",

        "10",
        "11"

    ]


    detalle = []


    total_estudiantes = 0
    total_promovidos = 0
    total_no_promovidos = 0



    for grado in grados:


        registros = list(

            db.notas.find({

                "grado": grado,

                "año_lectivo": "2026"

            })

        )


        estudiantes = set()



        for nota in registros:


            estudiantes.add(

                nota.get("estudiante_id")

            )



        promovidos = 0

        no_promovidos = 0



        for estudiante in estudiantes:



            notas_estudiante = list(

                db.notas.find({

                    "estudiante_id": estudiante,

                    "grado": grado,

                    "año_lectivo": "2026"

                })

            )



            if notas_estudiante:


                promedio_general = round(

                    sum(

                        nota.get(
                            "promedio",
                            0
                        )

                        for nota in notas_estudiante

                    )

                    /

                    len(notas_estudiante),

                    2

                )



                # Escala CIEM sobre 10

                if promedio_general >= 6:


                    promovidos += 1


                else:


                    no_promovidos += 1





        matricula = len(estudiantes)



        if matricula > 0:


            porcentaje = round(

                (promovidos / matricula) * 100,

                2

            )


        else:

            porcentaje = 0




        detalle.append({

            "grado": grado,

            "matricula": matricula,

            "promovidos": promovidos,

            "no_promovidos": no_promovidos,

            "porcentaje": porcentaje

        })



        total_estudiantes += matricula

        total_promovidos += promovidos

        total_no_promovidos += no_promovidos





    if total_estudiantes > 0:


        porcentaje_general = round(

            (total_promovidos / total_estudiantes) * 100,

            2

        )


    else:

        porcentaje_general = 0





    return {


        "detalle": detalle,


        "totales": {


            "matricula": total_estudiantes,

            "promovidos": total_promovidos,

            "no_promovidos": total_no_promovidos,

            "porcentaje": porcentaje_general

        }


    }
# ======================================================
# VISTA PROMOCIÓN ESCOLAR
# ======================================================


@docente_bp.route("/informes/promocion")
@role_required("docente")
def vista_promocion():


    datos = informe_promocion()


    return render_template(

        "docente/promocion.html",

        detalle=datos["detalle"],

        totales=datos["totales"]

    )

# ======================================================
# PDF INFORME DE PROMOCIÓN ESCOLAR
# ======================================================

@docente_bp.route("/informes/promocion/pdf")
@role_required("docente")
def reporte_promocion_pdf():

    datos = informe_promocion()

    detalle = datos["detalle"]
    totales = datos["totales"]

    archivo = "Promocion_Escolar_CIEM.pdf"

    doc = SimpleDocTemplate(
        archivo,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    elementos = []

    estilos = getSampleStyleSheet()

    # ==================================================
    # LOGOS
    # ==================================================

    logo_ciem = Image(
        "static/img/logo.jpg",
        width=65,
        height=65
    )

    logo_mined = Image(
        "static/img/MINED.jpg",
        width=65,
        height=65
    )

    # ==================================================
    # TÍTULO
    # ==================================================

    titulo = Paragraph(
        """
        <b>COLEGIO INTEGRAL EMANUEL</b><br/>
        INFORME DE PROMOCIÓN ESCOLAR<br/>
        Año Lectivo 2026
        """,
        estilos["Title"]
    )

    encabezado = Table(
        [
            [
                logo_ciem,
                titulo,
                logo_mined
            ]
        ],
        colWidths=[80, 320, 80]
    )

    encabezado.setStyle(
        TableStyle([
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),
            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER"
            )
        ])
    )

    elementos.append(encabezado)

    elementos.append(
        Spacer(1, 20)
    )

    # ==================================================
    # RESUMEN
    # ==================================================

    elementos.append(
        Paragraph(
            "Resumen de Promoción Escolar",
            estilos["Heading2"]
        )
    )

    elementos.append(
        Spacer(1, 10)
    )

    # ==================================================
    # TABLA DE PROMOCIÓN
    # ==================================================

    tabla_promocion = [

        [
            "Grado",
            "Matrícula",
            "Promovidos",
            "No Promovidos",
            "% Promoción"
        ]

    ]

    for fila in detalle:

        tabla_promocion.append(

            [
                fila["grado"],
                fila["matricula"],
                fila["promovidos"],
                fila["no_promovidos"],
                f'{fila["porcentaje"]}%'
            ]

        )

    # ==================================================
    # TOTAL GENERAL
    # ==================================================

    tabla_promocion.append(

        [
            "TOTAL",
            totales["matricula"],
            totales["promovidos"],
            totales["no_promovidos"],
            f'{totales["porcentaje"]}%'
        ]

    )

    tabla = Table(
        tabla_promocion,
        repeatRows=1
    )

    tabla.setStyle(

        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#0D2A52")
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),

            (
                "BACKGROUND",
                (0, -1),
                (-1, -1),
                colors.lightgrey
            ),

            (
                "FONTNAME",
                (0, -1),
                (-1, -1),
                "Helvetica-Bold"
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.black
            ),

            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER"
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "PADDING",
                (0, 0),
                (-1, -1),
                7
            )

        ])

    )

    elementos.append(tabla)

    elementos.append(
        Spacer(1, 20)
    )

    # ==================================================
    # RESUMEN GENERAL
    # ==================================================

    elementos.append(

        Paragraph(

            f"""
            <b>Total de estudiantes:</b>
            {totales["matricula"]}
            <br/>
            <b>Total promovidos:</b>
            {totales["promovidos"]}
            <br/>
            <b>Total no promovidos:</b>
            {totales["no_promovidos"]}
            <br/>
            <b>Porcentaje general de promoción:</b>
            {totales["porcentaje"]}%
            """,

            estilos["Normal"]

        )

    )

    elementos.append(
        Spacer(1, 30)
    )

    # ==================================================
    # FIRMAS
    # ==================================================

    firmas = Table(

        [

            [
                "________________________",
                "________________________"
            ],

            [
                "Dirección Académica",
                "Responsable del Informe"
            ]

        ],

        colWidths=[220, 220]

    )

    firmas.setStyle(

        TableStyle([

            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER"
            ),

            (
                "FONTNAME",
                (0, 1),
                (-1, 1),
                "Helvetica-Bold"
            )

        ])

    )

    elementos.append(firmas)

    # ==================================================
    # GENERAR PDF
    # ==================================================

    doc.build(elementos)

    return send_file(
        archivo,
        as_attachment=True,
        download_name="Promocion_Escolar_CIEM_2026.pdf",
        mimetype="application/pdf"
    )
# ======================================================
# CIEM ASISTE IA
# ======================================================

@docente_bp.route("/ciem-ai")
@role_required("docente")
def ciem_ai():

    return render_template(
        "docente/ciem_ai.html"
    )
# ======================================================
# GENERADOR CIEM IA
# ======================================================

@docente_bp.route("/ciem-ia/generar", methods=["POST"])
@role_required("docente")
def generar_ciem_ai():

    solicitud = request.form.get("solicitud","").lower()

    if "rúbrica" in solicitud or "rubrica" in solicitud:

        respuesta = """
RÚBRICA DE EVALUACIÓN

CRITERIOS

✔ Funcionalidad................................30 puntos

✔ Lógica del programa..........................20 puntos

✔ Uso de estructuras...........................20 puntos

✔ Interfaz.....................................15 puntos

✔ Documentación................................15 puntos

TOTAL.........................................100 puntos
"""

    elif "cotejo" in solicitud:

        respuesta = """
LISTA DE COTEJO

☐ Presentó el programa

☐ Compila correctamente

☐ Utiliza variables

☐ Utiliza arreglos

☐ Utiliza estructuras

☐ Entrega documentación

☐ Cumple todos los requisitos
"""

    elif "práctica" in solicitud or "practica" in solicitud:

        respuesta = """
PRÁCTICA DE LABORATORIO

Desarrolle un sistema de ventas en C#

Debe incluir:

• Menú principal

• Registro de productos

• Registro de ventas

• Reporte final

• Uso de arreglos

• Uso de estructuras
"""

    elif "cuestionario" in solicitud:

        respuesta = """
CUESTIONARIO

1. ¿Qué es un arreglo?

2. ¿Qué es una estructura?

3. Diferencia entre ambos.

4. Explique el uso del ciclo foreach.

5. Desarrolle un ejemplo en C#.
"""

    else:

        respuesta = f"""
No encontré una plantilla para:

{solicitud}

Puede intentar con:

• Rúbrica

• Lista de cotejo

• Práctica

• Cuestionario
"""

    return render_template(

        "docente/ciem_ai.html",

        respuesta=respuesta

    )


# =====================================
# PERFIL DEL ESTUDIANTE
# =====================================

@docente_bp.route("/estudiante/<estudiante_id>")
@role_required("docente")
def perfil_estudiante(estudiante_id):


    estudiante = db.estudiantes.find_one(
        {
            "_id": estudiante_id
        }
    )


    if not estudiante:

        flash(
            "Estudiante no encontrado",
            "danger"
        )

        return redirect(
            url_for("docente.estudiantes")
        )


    return render_template(
        "docente/perfil_estudiante.html",
        estudiante=estudiante
    )



# =====================================
# ASISTENCIA DEL ESTUDIANTE
# =====================================

@docente_bp.route("/asistencia-estudiante/<estudiante_id>")
@role_required("docente")
def asistencia_estudiante(estudiante_id):

    estudiante = db.estudiantes.find_one(
        {
            "_id": ObjectId(estudiante_id)
        }
    )

    if not estudiante:
        flash(
            "Estudiante no encontrado",
            "danger"
        )

        return redirect(
            url_for("docente.estudiantes")
        )


    asistencias = list(
        db.asistencias.find(
            {
                "estudiante_id": estudiante_id
            }
        )
    )


    return render_template(
        "docente/asistencia_estudiante.html",
        estudiante=estudiante,
        asistencias=asistencias
    )


# ==========================================================
# GENERAR PDF DEL BOLETÍN DEL ESTUDIANTE - DOCENTE
# WEASYPRINT
# ==========================================================

@docente_bp.route(
    "/boletin-pdf-estudiante/<estudiante_id>"
)
@role_required("docente")
def boletin_pdf_estudiante(estudiante_id):

    # ======================================================
    # BUSCAR ESTUDIANTE
    # ======================================================

    estudiante = db.estudiantes.find_one({
        "_id": estudiante_id
    })

    if not estudiante:

        flash(
            "Estudiante no encontrado",
            "danger"
        )

        return redirect(
            url_for("docente.estudiantes")
        )

    # ======================================================
    # BUSCAR NOTAS
    # ======================================================

    notas = list(
        db.notas.find({
            "estudiante_id": estudiante_id
        })
    )

    # ======================================================
    # CONSTRUIR BOLETÍN
    # ======================================================

    boletin = []

    for nota in notas:

        asignatura_id = nota.get(
            "asignatura_id"
        )

        asignatura = db.asignaturas.find_one({
            "_id": asignatura_id
        })

        if asignatura:

            nombre_asignatura = (
                asignatura.get("nombre")
                or asignatura.get("asignatura")
                or asignatura.get("nombre_asignatura")
                or str(asignatura_id)
            )

        else:

            nombre_asignatura = (
                str(asignatura_id)
                if asignatura_id
                else "Sin asignatura"
            )

        promedio = nota.get(
            "promedio"
        )

        # ==================================================
        # DETERMINAR ESTADO
        # ==================================================

        if promedio is None:

            estado = "Pendiente"

        elif promedio >= 60:

            estado = "Aprobado"

        else:

            estado = "Reforzamiento"

        boletin.append({

            "asignatura": nombre_asignatura,

            "corte1": nota.get("corte1"),

            "corte2": nota.get("corte2"),

            "corte3": nota.get("corte3"),

            "corte4": nota.get("corte4"),

            "promedio": promedio,

            "estado": estado
        })

    # ======================================================
    # PROMEDIO GENERAL
    # ======================================================

    promedios = [

        item["promedio"]

        for item in boletin

        if item.get("promedio") is not None
    ]

    if promedios:

        promedio_general = round(
            sum(promedios) / len(promedios),
            2
        )

    else:

        promedio_general = None

    # ======================================================
    # ESTADO GENERAL
    # ======================================================

    if promedio_general is None:

        estado_general = "Pendiente"

    elif promedio_general >= 60:

        estado_general = "Aprobado"

    else:

        estado_general = "Reforzamiento"

    # ======================================================
    # OBSERVACIÓN AUTOMÁTICA
    # ======================================================

    if promedio_general is None:

        observacion = (
            "Aún no se han registrado calificaciones "
            "para este estudiante."
        )

    elif promedio_general >= 90:

        observacion = (
            "El estudiante presenta un desempeño académico "
            "excelente durante el período evaluado. "
            "Se recomienda continuar fortaleciendo sus "
            "hábitos de estudio, participación y compromiso."
        )

    elif promedio_general >= 60:

        observacion = (
            "El estudiante presenta un desempeño académico "
            "satisfactorio durante el período evaluado. "
            "Se recomienda continuar fortaleciendo sus "
            "hábitos de estudio y participación en las "
            "diferentes actividades académicas."
        )

    else:

        observacion = (
            "El estudiante requiere reforzamiento académico. "
            "Se recomienda brindar acompañamiento y "
            "fortalecer los hábitos de estudio para mejorar "
            "su desempeño."
        )

    # ======================================================
    # RENDERIZAR HTML
    # ======================================================

    html_boletin = render_template(
        "boletin.html",
        estudiante=estudiante,
        notas=notas,
        boletin=boletin,
        promedio_general=promedio_general,
        estado_general=estado_general,
        observacion=observacion
    )

    # ======================================================
    # CONVERTIR HTML A PDF
    # ======================================================

    pdf_bytes = HTML(
        string=html_boletin,
        base_url=request.url_root
    ).write_pdf()

    # ======================================================
    # CREAR BUFFER
    # ======================================================

    buffer = BytesIO(
        pdf_bytes
    )

    buffer.seek(0)

    # ======================================================
    # NOMBRE DEL ESTUDIANTE
    # ======================================================

    nombre_estudiante = (
        estudiante.get(
            "nombre",
            "estudiante"
        )
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )

    # ======================================================
    # DESCARGAR PDF
    # ======================================================

    return send_file(

        buffer,

        as_attachment=True,

        download_name=(
            f"Boletin_"
            f"{nombre_estudiante}"
            f"_2026.pdf"
        ),

        mimetype="application/pdf"
    )
# =====================================
# MATERIALES DEL ESTUDIANTE
# =====================================

@docente_bp.route("/materiales-estudiante/<estudiante_id>")
@role_required("docente")
def materiales_estudiante(estudiante_id):


    estudiante = db.estudiantes.find_one(
        {
            "_id": ObjectId(estudiante_id)
        }
    )


    if not estudiante:

        flash(
            "Estudiante no encontrado",
            "danger"
        )

        return redirect(
            url_for("docente.estudiantes")
        )


    materiales = list(
        db.materiales.find(
            {
                "grado": estudiante.get("grado")
            }
        )
    )


    return render_template(
        "docente/materiales_estudiante.html",
        estudiante=estudiante,
        materiales=materiales
    )
# =====================================
# TOMAR ASISTENCIA DESDE PERFIL ESTUDIANTE
# =====================================

@docente_bp.route("/estudiante/asistencia/<estudiante_id>")
@role_required("docente")
def seleccionar_asistencia_estudiante(estudiante_id):

    # Buscar estudiante por ID (STRING)
    estudiante = db.estudiantes.find_one({
        "_id": estudiante_id
    })

    if not estudiante:
        flash("Estudiante no encontrado", "danger")
        return redirect(url_for("docente.estudiantes"))

    docente = db.docentes.find_one({
        "usuario": session.get("usuario")
    })

    if not docente:
        flash("Docente no encontrado", "danger")
        return redirect(url_for("docente.estudiantes"))

    asignatura = db.asignaturas.find_one({
        "grado": estudiante.get("grado"),
        "seccion": estudiante.get("seccion")
    })

    if not asignatura:
        flash(
            "No existe una asignatura asignada para este estudiante.",
            "warning"
        )
        return redirect(url_for("docente.estudiantes"))

    return redirect(
        url_for(
            "docente.asistencia",
            asignatura_id=asignatura["_id"]
        )
    )
    
# ==========================================================
# RESPONDER MENSAJE DESDE CHAT
# ==========================================================

@docente_bp.route("/responder_mensaje/<id>", methods=["POST"])
@role_required("docente")
def responder_mensaje(id):


    conversacion_id = id


    texto = request.form.get(
        "respuesta"
    )


    if not texto:

        flash(
            "Debe escribir una respuesta",
            "warning"
        )

        return redirect(request.referrer)



    mensajes = db.mensajes


    conversaciones = db.conversaciones



    nuevo = {


        "conversacion_id":

            ObjectId(conversacion_id),


        "emisor":

            "docente",


        "mensaje":

            texto,


        "fecha":

            datetime.now(),


        "leido":

            False

    }



    mensajes.insert_one(nuevo)



    conversaciones.update_one(

        {

            "_id":

                ObjectId(conversacion_id)

        },


        {

            "$set":

            {

                "ultimo_mensaje":

                    texto,


                "ultima_actualizacion":

                    datetime.now(),


                "no_leidos_padre":

                    1

            }

        }

    )


    flash(
        "Respuesta enviada correctamente",
        "success"
    )


    return redirect(

        url_for(

            "mensajes.chat",

            conversacion_id=conversacion_id

        )

    )


# ==========================================
# CONFIGURACIÓN DEL DOCENTE
# ==========================================

@docente_bp.route("/configuracion")
@role_required("docente")
def configuracion():

    usuario = session.get("usuario")

    # ==========================================
    # BUSCAR USUARIO
    # ==========================================

    datos_usuario = db.usuarios.find_one({
        "usuario": usuario
    })

    # ==========================================
    # VALIDAR USUARIO
    # ==========================================

    if not datos_usuario:

        flash(
            "No se encontró la información de la cuenta.",
            "danger"
        )

        return redirect(
            url_for("docente.dashboard_docente")
        )

    # ==========================================
    # DEPURACIÓN
    # ==========================================

    print("=====================================")
    print("CONFIGURACIÓN DOCENTE")
    print("USUARIO:", usuario)
    print("CORREO:", datos_usuario.get("correo"))
    print("=====================================")

    # ==========================================
    # MOSTRAR CONFIGURACIÓN
    # ==========================================

    return render_template(
        "docente/configuracion.html",
        usuario=datos_usuario
    )
# ==========================================================
# CAMBIAR CORREO DEL DOCENTE
# ==========================================================

@docente_bp.route(
    "/cambiar-correo",
    methods=["POST"]
)
@role_required("docente")
def cambiar_correo():

    usuario = session.get("usuario")

    nuevo_correo = request.form.get(
        "correo",
        ""
    ).strip().lower()

    print("====================================")
    print("📧 CAMBIO DE CORREO DOCENTE")
    print("USUARIO:", usuario)
    print("NUEVO CORREO:", nuevo_correo)
    print("====================================")

    # ======================================================
    # VALIDAR
    # ======================================================

    if not nuevo_correo:

        flash(
            "Debe ingresar un correo electrónico.",
            "danger"
        )

        return redirect(
            url_for("docente.configuracion")
        )

    # ======================================================
    # BUSCAR USUARIO
    # ======================================================

    usuario_db = db.usuarios.find_one({
        "usuario": usuario
    })

    if not usuario_db:

        flash(
            "No se encontró el usuario.",
            "danger"
        )

        return redirect(
            url_for("docente.configuracion")
        )

    # ======================================================
    # ACTUALIZAR CORREO
    # ======================================================

    resultado = db.usuarios.update_one(
        {
            "usuario": usuario
        },
        {
            "$set": {
                "correo": nuevo_correo
            }
        }
    )

    print("DOCUMENTOS MODIFICADOS:")
    print(resultado.modified_count)

    # ======================================================
    # RESULTADO
    # ======================================================

    if resultado.modified_count > 0:

        flash(
            "Correo actualizado correctamente.",
            "success"
        )

    else:

        flash(
            "El correo ya tenía ese valor.",
            "warning"
        )

    return redirect(
        url_for("docente.configuracion")
    )


# ==========================================================
# CAMBIAR CONTRASEÑA DEL DOCENTE
# ==========================================================

@docente_bp.route(
    "/cambiar-password",
    methods=["POST"]
)
@role_required("docente")
def cambiar_password():

    usuario = session.get("usuario")

    password_actual = request.form.get(
        "password_actual",
        ""
    ).strip()

    password_nueva = request.form.get(
        "password_nueva",
        ""
    ).strip()

    password_confirmar = request.form.get(
        "password_confirmar",
        ""
    ).strip()

    print("====================================")
    print("🔐 CAMBIO DE CONTRASEÑA DOCENTE")
    print("USUARIO:", usuario)
    print("====================================")

    # ======================================================
    # VALIDAR CAMPOS
    # ======================================================

    if not password_actual:

        flash(
            "Debe ingresar su contraseña actual.",
            "danger"
        )

        return redirect(
            url_for("docente.configuracion")
        )

    if not password_nueva:

        flash(
            "Debe ingresar una nueva contraseña.",
            "danger"
        )

        return redirect(
            url_for("docente.configuracion")
        )

    if not password_confirmar:

        flash(
            "Debe confirmar la nueva contraseña.",
            "danger"
        )

        return redirect(
            url_for("docente.configuracion")
        )

    # ======================================================
    # CONFIRMAR CONTRASEÑA
    # ======================================================

    if password_nueva != password_confirmar:

        flash(
            "Las nuevas contraseñas no coinciden.",
            "danger"
        )

        return redirect(
            url_for("docente.configuracion")
        )

    # ======================================================
    # LONGITUD
    # ======================================================

    if len(password_nueva) < 6:

        flash(
            "La nueva contraseña debe tener al menos 6 caracteres.",
            "danger"
        )

        return redirect(
            url_for("docente.configuracion")
        )

    # ======================================================
    # BUSCAR USUARIO
    # ======================================================

    usuario_db = db.usuarios.find_one({
        "usuario": usuario
    })

    if not usuario_db:

        flash(
            "No se encontró el usuario.",
            "danger"
        )

        return redirect(
            url_for("docente.configuracion")
        )

    # ======================================================
    # CONTRASEÑA GUARDADA
    # ======================================================

    password_guardada = usuario_db.get(
        "password"
    )

    # ======================================================
    # VERIFICAR CONTRASEÑA ACTUAL
    # ======================================================

    if password_guardada != password_actual:

        flash(
            "La contraseña actual es incorrecta.",
            "danger"
        )

        return redirect(
            url_for("docente.configuracion")
        )

    # ======================================================
    # ACTUALIZAR CONTRASEÑA
    # ======================================================

    resultado = db.usuarios.update_one(
        {
            "usuario": usuario
        },
        {
            "$set": {
                "password": password_nueva
            }
        }
    )

    print("DOCUMENTOS MODIFICADOS:")
    print(resultado.modified_count)

    # ======================================================
    # RESULTADO
    # ======================================================

    if resultado.modified_count > 0:

        flash(
            "Contraseña actualizada correctamente.",
            "success"
        )

    else:

        flash(
            "La contraseña no sufrió cambios.",
            "warning"
        )

    return redirect(
        url_for("docente.configuracion")
    )