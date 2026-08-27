from flask import (
    Blueprint,
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_file,
    make_response,
    current_app
)

from io import BytesIO
from datetime import datetime
from functools import wraps
import os

from bson import ObjectId

from flask_pymongo import PyMongo

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image
)

from weasyprint import HTML

from config.database import db

from routes.mined import (
    datos_mined,
    estadistica_grado,
    informe_retencion
)

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
    # OBTENER CLASES REALES DEL DOCENTE
    # ============================================================

    def obtener_clases_docente(docente_id):

        docente_id = str(docente_id).strip().upper()

        print("============================================================")
        print("🔎 OBTENIENDO CLASES REALES DEL DOCENTE")
        print("👨‍🏫 DOCENTE ID:", docente_id)
        print("📂 FUENTE: asignaciones_clase")
        print("============================================================")

        # --------------------------------------------------------
        # BUSCAR ÚNICAMENTE LAS ASIGNACIONES DEL DOCENTE
        # --------------------------------------------------------

        clases = list(
            db.asignaciones_clase.find({
                "docente_id": docente_id,
                "estado": "Activa"
            })
        )

        # --------------------------------------------------------
        # ORDENAR LAS CLASES
        # --------------------------------------------------------

        clases.sort(
            key=lambda clase: (
                str(clase.get("nivel", "")),
                str(clase.get("grado", "")),
                str(clase.get("seccion", "")),
                str(
                    clase.get(
                        "asignatura",
                        clase.get("asignatura_nombre", "")
                    )
                ).lower()
            )
        )

        # --------------------------------------------------------
        # MOSTRAR EN CONSOLA LO QUE REALMENTE SE ENVIARÁ
        # AL DASHBOARD
        # --------------------------------------------------------

        print("📚 CLASES ENCONTRADAS:", len(clases))

        for clase in clases:

            print(
                "➡️",
                clase.get(
                    "codigo_asignatura",
                    clase.get("codigo", "")
                ),
                "|",
                clase.get(
                    "asignatura",
                    clase.get("asignatura_nombre", "")
                ),
                "| Grado:",
                clase.get("grado", ""),
                "| Sección:",
                clase.get("seccion", "")
            )

        print("============================================================")

        return clases

#===========================================================
# DASHBOARD DOCENTE
# ============================================================

@docente_bp.route("/")
@role_required("docente")
def dashboard_docente():

    print("========================================================")
    print("📊 DASHBOARD DOCENTE")
    print("========================================================")

    # ========================================================
    # 1. USUARIO
    # ========================================================

    usuario = session.get("usuario")

    print("👤 USUARIO:", usuario)

    if not usuario:

        print("❌ NO HAY USUARIO EN LA SESIÓN")

        flash(
            "La sesión ha expirado.",
            "warning"
        )

        return redirect(
            url_for("login")
        )

    # ========================================================
    # 2. BUSCAR DOCENTE
    # ========================================================

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

    # ========================================================
    # 3. ID OFICIAL DEL DOCENTE
    # ========================================================

    codigo_docente = str(
        docente.get(
            "codigo",
            ""
        )
    ).strip().upper()

    if codigo_docente.startswith("DOC"):

        docente_id = codigo_docente

    else:

        docente_id = "DOC" + codigo_docente

    print(
        "👨‍🏫 DOCENTE:",
        docente.get(
            "nombre",
            ""
        )
    )

    print(
        "🔢 CÓDIGO:",
        codigo_docente
    )

    print(
        "🆔 ID DOCENTE:",
        docente_id
    )

    print("========================================================")


    # ========================================================
    # 4. BUSCAR CLASES REALES DEL DOCENTE
    # ========================================================

    print("🔎 BUSCANDO CLASES DEL DOCENTE")
    print("========================================================")

    # --------------------------------------------------------
    # GENERAR POSIBLES IDs DEL DOCENTE
    # --------------------------------------------------------

    codigo_limpio = codigo_docente.replace("DOC", "").strip()

    ids_docente = [
        docente_id,
        codigo_limpio,
        "DOC" + codigo_limpio
    ]

    # Eliminar duplicados
    ids_docente = list(
        dict.fromkeys(ids_docente)
    )

    print(
        "👨‍🏫 IDs A BUSCAR:",
        ids_docente
    )

    # --------------------------------------------------------
    # BUSCAR EN ASIGNACIONES_CLASE
    #
    # NO FILTRAMOS POR ESTADO AQUÍ.
    # Primero obtenemos las asignaciones reales.
    # --------------------------------------------------------

    clases = list(
        db.asignaciones_clase.find({
            "docente_id": {
                "$in": ids_docente
            }
        }).sort(
            "asignatura",
            1
        )
    )

    print(
        "📂 COLECCIÓN: asignaciones_clase"
    )

    print(
        "📚 ASIGNACIONES ENCONTRADAS:",
        len(clases)
    )

    # --------------------------------------------------------
    # MOSTRAR LAS CLASES ENCONTRADAS
    # --------------------------------------------------------

    for clase in clases:

        print(
            "➡️",
            clase.get(
                "codigo_asignatura",
                ""
            ),
            "|",
            clase.get(
                "asignatura",
                ""
            ),
            "| Nivel:",
            clase.get(
                "nivel",
                ""
            ),
            "| Grado:",
            clase.get(
                "grado",
                ""
            ),
            "| Sección:",
            clase.get(
                "seccion",
                ""
            ),
            "| Docente:",
            clase.get(
                "docente_id",
                ""
            ),
            "| Estado:",
            clase.get(
                "estado",
                ""
            )
        )

    print("========================================================")

    # ========================================================
    # 5. PREPARAR CLASES PARA EL DASHBOARD
    # ========================================================

    for clase in clases:

        # ID REAL DEL DOCUMENTO
        clase["id_str"] = str(
            clase.get(
                "_id",
                ""
            )
        )

        # CÓDIGO DE ASIGNATURA
        clase["codigo"] = clase.get(
            "codigo_asignatura",
            ""
        )

        # NOMBRE DE ASIGNATURA
        clase["nombre"] = clase.get(
            "asignatura",
            ""
        )

        # ID DE ASIGNATURA
        clase["asignatura_id"] = clase.get(
            "asignatura_id",
            clase.get(
                "_id"
            )
        )

        clase["asignatura_id"] = str(
            clase["asignatura_id"]
        )

        # DOCENTE
        clase["docente_id"] = clase.get(
            "docente_id",
            docente_id
        )

        clase["docente_nombre"] = clase.get(
            "docente",
            docente.get(
                "nombre",
                ""
            )
        )

        # NIVEL
        clase["nivel"] = clase.get(
            "nivel",
            ""
        )

        # GRADO
        clase["grado"] = clase.get(
            "grado",
            ""
        )

        # SECCIÓN
        clase["seccion"] = clase.get(
            "seccion",
            ""
        )

        # ESTADO REAL DE MONGODB
        clase["estado"] = clase.get(
            "estado",
            "Activa"
        )

    # ========================================================
    # 6. TOTAL FINAL
    # ========================================================

    total_asignaturas = len(
        clases
    )

    print(
        "📚 TOTAL FINAL CLASES:",
        total_asignaturas
    )

    print("========================================================")

    # ========================================================
    # 6. MOSTRAR CLASES PREPARADAS
    # ========================================================

    print("📋 CLASES PREPARADAS PARA EL HTML")
    print("========================================================")

    for clase in clases:

        print(
            "🆔 ID:",
            clase.get(
                "id_str",
                ""
            )
        )

        print(
            "🔤 CÓDIGO:",
            clase.get(
                "codigo",
                ""
            )
        )

        print(
            "📖 ASIGNATURA:",
            clase.get(
                "nombre",
                ""
            )
        )

        print(
            "🎓 NIVEL:",
            clase.get(
                "nivel",
                ""
            )
        )

        print(
            "🎓 GRADO:",
            clase.get(
                "grado",
                ""
            )
        )

        print(
            "🏫 SECCIÓN:",
            clase.get(
                "seccion",
                ""
            )
        )

        print(
            "👨‍🏫 DOCENTE:",
            clase.get(
                "docente_id",
                ""
            )
        )

        print(
            "📌 ESTADO:",
            clase.get(
                "estado",
                ""
            )
        )

        print("----------------------------------------")

    # ========================================================
    # 7. TOTAL DE ASIGNATURAS
    # ========================================================

    total_asignaturas = len(
        clases
    )

    print(
        "📚 TOTAL ASIGNATURAS:",
        total_asignaturas
    )

    # ========================================================
    # 8. ESTUDIANTES
    #
    # Se mantiene el total general del sistema.
    # ========================================================

    total_estudiantes = db.estudiantes.count_documents({})

    # ========================================================
    # 9. ASISTENCIAS
    # ========================================================

    total_asistencias = db.asistencias.count_documents({})

    # ========================================================
    # 10. NOTAS
    # ========================================================

    total_notas = db.notas.count_documents({})

    # ========================================================
    # 11. INCIDENCIAS
    # ========================================================

    total_incidencias = 0

    try:

        total_incidencias = db.incidencias.count_documents({
            "docente_id": docente_id
        })

    except Exception as e:

        print(
            "⚠️ ERROR INCIDENCIAS:",
            e
        )

        total_incidencias = 0

    # ========================================================
    # 12. CONVERSACIONES
    # ========================================================

    total_conversaciones = 0

    try:

        total_conversaciones = db.conversaciones.count_documents({
            "docente_id": docente_id
        })

    except Exception as e:

        print(
            "⚠️ ERROR CONVERSACIONES:",
            e
        )

        total_conversaciones = 0

    # ========================================================
    # 13. MENSAJES PENDIENTES
    # ========================================================

    mensajes_pendientes = 0

    try:

        mensajes_pendientes = db.mensajes.count_documents({
            "destinatario_id": docente_id,
            "leido": False
        })

    except Exception as e:

        print(
            "⚠️ ERROR MENSAJES:",
            e
        )

        mensajes_pendientes = 0

    # ========================================================
    # 14. CLASES HOY
    #
    # Por ahora utiliza las clases asignadas al docente.
    # ========================================================

    clases_hoy = clases

    # ========================================================
    # 15. ESTADÍSTICA
    # ========================================================

    estadistica = {

        "total_asignaturas":
            total_asignaturas,

        "total_estudiantes":
            total_estudiantes,

        "incidencias":
            total_incidencias,

        "comunicaciones":
            total_conversaciones

    }

    # ========================================================
    # 16. RESUMEN FINAL
    # ========================================================

    print("========================================================")
    print("📊 RESUMEN DASHBOARD DOCENTE")
    print("========================================================")

    print(
        "👨‍🏫 DOCENTE:",
        docente.get(
            "nombre",
            ""
        )
    )

    print(
        "🆔 DOCENTE ID:",
        docente_id
    )

    print(
        "📚 CLASES:",
        total_asignaturas
    )

    print(
        "👥 ESTUDIANTES:",
        total_estudiantes
    )

    print(
        "📋 ASISTENCIAS:",
        total_asistencias
    )

    print(
        "📝 NOTAS:",
        total_notas
    )

    print(
        "⚠️ INCIDENCIAS:",
        total_incidencias
    )

    print(
        "💬 CONVERSACIONES:",
        total_conversaciones
    )

    print(
        "💬 MENSAJES PENDIENTES:",
        mensajes_pendientes
    )

    print("========================================================")

    # ========================================================
    # 17. ENVIAR DATOS AL HTML
    # ========================================================

    return render_template(

        "docente/dashboard_docente.html",

        docente=docente,

        docente_id=docente_id,

        clases=clases,

        clases_hoy=clases_hoy,

        estadistica=estadistica,

        total_asignaturas=total_asignaturas,

        total_estudiantes=total_estudiantes,

        total_asistencias=total_asistencias,

        total_notas=total_notas,

        total_incidencias=total_incidencias,

        total_conversaciones=total_conversaciones,

        mensajes_pendientes=mensajes_pendientes

    )

# ============================================================
# SELECCIONAR CLASE PARA INCIDENCIAS
# ============================================================

@docente_bp.route("/incidencias")
@role_required("docente")
def lista_incidencias():

    print("========================================================")
    print("⚠️ SELECCIÓN DE CLASE PARA INCIDENCIAS")
    print("========================================================")

    # ========================================================
    # 1. USUARIO
    # ========================================================

    usuario = session.get("usuario")

    if not usuario:

        flash(
            "La sesión ha expirado.",
            "warning"
        )

        return redirect(
            url_for("login")
        )

    print("👤 USUARIO:", usuario)

    # ========================================================
    # 2. BUSCAR DOCENTE
    # ========================================================

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

    # ========================================================
    # 3. ID OFICIAL DEL DOCENTE
    # ========================================================

    codigo_docente = str(
        docente.get(
            "codigo",
            ""
        )
    ).strip().upper()

    if codigo_docente.startswith("DOC"):

        docente_id = codigo_docente

    else:

        docente_id = "DOC" + codigo_docente

    print(
        "👨‍🏫 DOCENTE:",
        docente.get(
            "nombre",
            ""
        )
    )

    print(
        "🆔 DOCENTE ID:",
        docente_id
    )

    # ========================================================
    # 4. BUSCAR CLASES
    #
    # MISMA FUENTE QUE DASHBOARD,
    # CALIFICACIONES Y ASISTENCIA
    # ========================================================

    filtro_clases = {

        "docente_id": docente_id,

        "activo": True

    }

    # ========================================================
    # DOC014
    #
    # INFORMÁTICA NO PERTENECE A ASLEY
    # ========================================================

    if docente_id == "DOC014":

        filtro_clases["asignatura_codigo"] = {

            "$ne": "INF"

        }

    clases = list(

        db.asignaciones_clase.find(
            filtro_clases
        ).sort(
            "asignatura_nombre",
            1
        )

    )

    # ========================================================
    # 5. PREPARAR DATOS
    # ========================================================

    for clase in clases:

        clase["id_str"] = str(
            clase.get("_id")
        )

        clase["codigo"] = clase.get(
            "asignatura_codigo",
            ""
        )

        clase["nombre"] = clase.get(
            "asignatura_nombre",
            ""
        )

        clase["asignatura_id"] = str(
            clase.get("_id")
        )

        clase["docente_id"] = clase.get(
            "docente_id",
            docente_id
        )

        clase["docente_nombre"] = clase.get(
            "docente_nombre",
            docente.get(
                "nombre",
                ""
            )
        )

        clase["nivel"] = clase.get(
            "nivel",
            ""
        )

        clase["grado"] = clase.get(
            "grado",
            ""
        )

        clase["seccion"] = clase.get(
            "seccion",
            ""
        )

        clase["estado"] = (

            "Activo"

            if clase.get(
                "activo",
                True
            )

            else "Inactivo"

        )

    # ========================================================
    # 6. MOSTRAR CLASES
    # ========================================================

    print("========================================================")
    print("📚 CLASES PARA INCIDENCIAS")
    print("========================================================")

    for clase in clases:

        print(
            "🆔",
            clase.get("id_str"),
            "|",
            clase.get("codigo"),
            "|",
            clase.get("nombre"),
            "| NIVEL:",
            clase.get("nivel"),
            "| GRADO:",
            clase.get("grado"),
            "| SECCIÓN:",
            clase.get("seccion")
        )

    print("========================================================")

    print(
        "📚 TOTAL CLASES PARA INCIDENCIAS:",
        len(clases)
    )

    print("========================================================")

    # ========================================================
    # 7. HTML
    # ========================================================

    return render_template(

        "docente/seleccionar_incidencias.html",

        clases=clases,

        docente=docente,

        docente_id=docente_id,

        total_asignaturas=len(clases)

    )

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

    codigo_docente = str(
        docente.get("codigo", "")
    ).strip().upper()

    if codigo_docente.startswith("DOC"):
        docente_id = codigo_docente
    else:
        docente_id = f"DOC{codigo_docente}"

    ids_busqueda = [asignatura_id]

    try:
        ids_busqueda.append(ObjectId(asignatura_id))
    except Exception:
        pass

    asignatura = db.asignaciones_clase.find_one({
        "_id": {
            "$in": ids_busqueda
        },
        "docente_id": docente_id,
        "activo": True
    })
# =====================================
# CERRAR SESIÓN DOCENTE
# =====================================

@docente_bp.route("/logout")
def logout():

    session.clear()

    return redirect("/login")

# ============================================================
# SELECCIONAR CLASE PARA ASISTENCIA
# ============================================================

@docente_bp.route("/asistencia")
@role_required("docente")
def lista_asistencia():

    print("========================================================")
    print("📋 SELECCIÓN DE CLASE PARA ASISTENCIA")
    print("========================================================")

    # ========================================================
    # 1. USUARIO
    # ========================================================

    usuario = session.get("usuario")

    if not usuario:

        flash(
            "La sesión ha expirado.",
            "warning"
        )

        return redirect(
            url_for("login")
        )

    print("👤 USUARIO:", usuario)

    # ========================================================
    # 2. BUSCAR DOCENTE
    # ========================================================

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

    # ========================================================
    # 3. ID OFICIAL DEL DOCENTE
    # ========================================================

    codigo_docente = str(
        docente.get(
            "codigo",
            ""
        )
    ).strip().upper()

    if codigo_docente.startswith("DOC"):

        docente_id = codigo_docente

    else:

        docente_id = "DOC" + codigo_docente

    print("👨‍🏫 DOCENTE:", docente.get("nombre"))
    print("🆔 DOCENTE ID:", docente_id)

    # ========================================================
    # 4. BUSCAR CLASES
    #
    # MISMA FUENTE QUE CALIFICACIONES
    # ========================================================

    filtro_clases = {

        "docente_id": docente_id,

        "activo": True

    }

    # ========================================================
    # DOC014
    #
    # Asley NO tiene Informática Educativa.
    # ========================================================

    if docente_id == "DOC014":

        filtro_clases["asignatura_codigo"] = {
            "$ne": "INF"
        }

    clases = list(
        db.asignaciones_clase.find(
            filtro_clases
        ).sort(
            "asignatura_nombre",
            1
        )
    )

    # ========================================================
    # 5. PREPARAR DATOS
    # ========================================================

    for clase in clases:

        clase["id_str"] = str(
            clase.get("_id")
        )

        clase["codigo"] = clase.get(
            "asignatura_codigo",
            ""
        )

        clase["nombre"] = clase.get(
            "asignatura_nombre",
            ""
        )

        clase["asignatura_id"] = str(
            clase.get("_id")
        )

        clase["docente_id"] = clase.get(
            "docente_id",
            docente_id
        )

        clase["docente_nombre"] = clase.get(
            "docente_nombre",
            docente.get(
                "nombre",
                ""
            )
        )

        clase["estado"] = (
            "Activo"
            if clase.get(
                "activo",
                True
            )
            else "Inactivo"
        )

    # ========================================================
    # 6. MOSTRAR RESULTADO
    # ========================================================

    print("========================================================")
    print("📚 CLASES DE ASISTENCIA")
    print("========================================================")

    for clase in clases:

        print(
            "🆔",
            clase.get("id_str"),
            "|",
            clase.get("codigo"),
            "|",
            clase.get("nombre"),
            "|",
            clase.get("nivel"),
            "| GRADO:",
            clase.get("grado"),
            "| SECCIÓN:",
            clase.get("seccion")
        )

    print("========================================================")

    print(
        "📚 TOTAL CLASES PARA ASISTENCIA:",
        len(clases)
    )

    print("========================================================")

    # ========================================================
    # 7. ENVIAR AL HTML
    # ========================================================

    return render_template(

        "docente/seleccionar_asistencia.html",

        clases=clases,

        docente=docente,

        docente_id=docente_id,

        total_asignaturas=len(clases)

    )

# =====================================
# ABRIR ASISTENCIA
# =====================================

@docente_bp.route("/asistencia/<asignatura_id>")
@role_required("docente")
def asistencia(asignatura_id):

    print("========================================")
    print("🔥 ABRIENDO ASISTENCIA")
    print("🆔 ASIGNACIÓN ID:", repr(asignatura_id))
    print("========================================")

    # =====================================
    # 1. USUARIO
    # =====================================

    usuario = session.get("usuario")

    if not usuario:

        flash(
            "La sesión ha expirado.",
            "warning"
        )

        return redirect(
            url_for("login")
        )

    # =====================================
    # 2. BUSCAR DOCENTE
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
    # 3. CONSTRUIR ID DOCENTE
    # =====================================

    codigo_docente = str(
        docente.get(
            "codigo",
            ""
        )
    ).strip().upper()

    if codigo_docente.startswith("DOC"):

        docente_id = codigo_docente

    else:

        docente_id = "DOC" + codigo_docente

    print(
        "👨‍🏫 DOCENTE:",
        docente.get(
            "nombre",
            ""
        )
    )

    print(
        "🆔 DOCENTE ID:",
        docente_id
    )

    # =====================================
    # 4. BUSCAR ASIGNACIÓN
    #
    # MISMA FUENTE QUE DASHBOARD Y
    # CALIFICACIONES
    # =====================================

    print("========================================")
    print("🔎 BUSCANDO ASIGNACIÓN")
    print("📂 COLECCIÓN: asignaciones_clase")
    print("========================================")

    asignacion = None

    # =====================================
    # 4.1 BUSCAR POR ID STRING
    # =====================================

    asignacion = db.asignaciones_clase.find_one({

        "_id": asignatura_id,

        "docente_id": docente_id,

        "activo": True

    })

    # =====================================
    # 4.2 BUSCAR POR OBJECTID
    # =====================================

    if not asignacion:

        try:

            from bson import ObjectId

            if ObjectId.is_valid(asignatura_id):

                asignacion = db.asignaciones_clase.find_one({

                    "_id": ObjectId(asignatura_id),

                    "docente_id": docente_id,

                    "activo": True

                })

        except Exception as e:

            print(
                "⚠️ ERROR OBJECTID:",
                e
            )

    # =====================================
    # 4.3 CORRECCIÓN PARA DOC014
    #
    # INF NO PERTENECE A ASLEY
    # =====================================

    if asignacion:

        codigo_asignatura = str(
            asignacion.get(
                "asignatura_codigo",
                ""
            )
        ).strip().upper()

        if (

            docente_id == "DOC014"
            and
            codigo_asignatura == "INF"

        ):

            print(
                "❌ INF NO PERTENECE A DOC014"
            )

            asignacion = None

    # =====================================
    # 5. VALIDAR ASIGNACIÓN
    # =====================================

    if not asignacion:

        print("❌ ASIGNACIÓN NO ENCONTRADA")

        flash(
            "Asignación de clase no encontrada.",
            "danger"
        )

        return redirect(
            url_for("docente.aulas")
        )

    print("✅ ASIGNACIÓN ENCONTRADA")

    print(
        "🆔 ID:",
        asignacion.get("_id")
    )

    print(
        "🔤 CÓDIGO:",
        asignacion.get(
            "asignatura_codigo",
            ""
        )
    )

    print(
        "📖 ASIGNATURA:",
        asignacion.get(
            "asignatura_nombre",
            ""
        )
    )

    # =====================================
    # 6. DATOS DE LA CLASE
    # =====================================

    grado = asignacion.get(
        "grado",
        ""
    )

    seccion = asignacion.get(
        "seccion",
        ""
    )

    nivel = asignacion.get(
        "nivel",
        ""
    )

    asignatura_codigo = asignacion.get(
        "asignatura_codigo",
        ""
    )

    asignatura_nombre = asignacion.get(
        "asignatura_nombre",
        ""
    )

    # =====================================
    # 7. NORMALIZAR GRADO
    # =====================================

    grado_texto = str(
        grado
    ).strip()

    equivalencias_grado = {

        "1": [
            "1",
            "1ro",
            "1ro Grado",
            "1er Grado"
        ],

        "1ro": [
            "1",
            "1ro",
            "1ro Grado",
            "1er Grado"
        ],

        "1ro Grado": [
            "1",
            "1ro",
            "1ro Grado",
            "1er Grado"
        ],

        "1er Grado": [
            "1",
            "1ro",
            "1ro Grado",
            "1er Grado"
        ],

        "2": [
            "2",
            "2do",
            "2do Grado"
        ],

        "2do": [
            "2",
            "2do",
            "2do Grado"
        ],

        "2do Grado": [
            "2",
            "2do",
            "2do Grado"
        ],

        "3": [
            "3",
            "3ro",
            "3ro Grado",
            "3er Grado"
        ],

        "3ro": [
            "3",
            "3ro",
            "3ro Grado",
            "3er Grado"
        ],

        "3ro Grado": [
            "3",
            "3ro",
            "3ro Grado",
            "3er Grado"
        ],

        "3er Grado": [
            "3",
            "3ro",
            "3ro Grado",
            "3er Grado"
        ],

        "4": [
            "4",
            "4to",
            "4to Grado"
        ],

        "4to": [
            "4",
            "4to",
            "4to Grado"
        ],

        "4to Grado": [
            "4",
            "4to",
            "4to Grado"
        ],

        "5": [
            "5",
            "5to",
            "5to Grado"
        ],

        "5to": [
            "5",
            "5to",
            "5to Grado"
        ],

        "5to Grado": [
            "5",
            "5to",
            "5to Grado"
        ],

        "6": [
            "6",
            "6to",
            "6to Grado"
        ],

        "6to": [
            "6",
            "6to",
            "6to Grado"
        ],

        "6to Grado": [
            "6",
            "6to",
            "6to Grado"
        ],

        "I Nivel": [
            "I Nivel"
        ],

        "II Nivel": [
            "II Nivel"
        ],

        "III Nivel": [
            "III Nivel"
        ],

        "Primer Año": [
            "Primer Año"
        ],

        "Segundo Año": [
            "Segundo Año"
        ],

        "Tercer Año": [
            "Tercer Año"
        ],

        "Cuarto Año": [
            "Cuarto Año"
        ],

        "Quinto Año": [
            "Quinto Año"
        ]

    }

    grados_busqueda = equivalencias_grado.get(
        grado_texto,
        [grado_texto]
    )

    # =====================================
    # 8. BUSCAR ESTUDIANTES
    # =====================================

    filtro_estudiantes = {

        "grado": {
            "$in": grados_busqueda
        },

        "estado": "activo"

    }

    if seccion:

        filtro_estudiantes["seccion"] = seccion

    print("========================================")
    print("🔎 FILTRO ESTUDIANTES")
    print(
        filtro_estudiantes
    )
    print("========================================")

    estudiantes = list(
        db.estudiantes.find(
            filtro_estudiantes
        ).sort(
            "nombre",
            1
        )
    )

    print(
        "👥 ESTUDIANTES ENCONTRADOS:",
        len(estudiantes)
    )

    # =====================================
    # 9. FECHA
    # =====================================

    fecha = datetime.now().strftime(
        "%Y-%m-%d"
    )

    # =====================================
    # 10. BUSCAR ASISTENCIAS GUARDADAS
    # =====================================

    asistencias_guardadas = list(
        db.asistencias.find({

            "asignatura_id":
                asignatura_id,

            "fecha":
                fecha

        })
    )

    print(
        "📋 ASISTENCIAS GUARDADAS:",
        len(asistencias_guardadas)
    )

    # =====================================
    # 11. CONSTRUIR DICCIONARIO
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

        asistencia[estudiante_id] = {

            "estado": str(
                registro.get(
                    "estado",
                    "Presente"
                )
            ),

            "motivo": str(
                registro.get(
                    "motivo",
                    ""
                )
            )

        }

    # =====================================
    # 12. OBJETO PARA HTML
    # =====================================

    asignatura = {

        "_id":
            asignacion.get("_id"),

        "codigo":
            asignatura_codigo,

        "nombre":
            asignatura_nombre,

        "nivel":
            nivel,

        "grado":
            grado,

        "seccion":
            seccion,

        "docente_id":
            docente_id

    }

    # =====================================
    # 13. RESUMEN
    # =====================================

    print("========================================")
    print("📦 DATOS PARA ASISTENCIA")
    print("========================================")

    print(
        "ASIGNATURA:",
        asignatura
    )

    print(
        "ESTUDIANTES:",
        len(estudiantes)
    )

    print(
        "ASISTENCIAS:",
        len(asistencia)
    )

    print("========================================")

    # =====================================
    # 14. HTML
    # =====================================

    return render_template(

        "docente/asistencia.html",

        asignatura=asignatura,

        estudiantes=estudiantes,

        fecha=fecha,

        asistencia=asistencia,

        docente=docente

    )

# ==========================================================
# NOTAS
# ==========================================================

@docente_bp.route("/notas/<asignatura_id>")
@role_required("docente")
def notas(asignatura_id):

    print("========================================")
    print("📝 NOTAS")
    print("ASIGNACIÓN ID:", asignatura_id)
    print("========================================")

    usuario = session.get("usuario")

    docente = db.docentes.find_one({
        "usuario": usuario
    })

    if not docente:
        flash("Docente no encontrado.", "danger")
        return redirect(url_for("login"))

    codigo_docente = str(
        docente.get("codigo", "")
    ).strip()

    docente_id = f"DOC{codigo_docente}"

    ids_busqueda = [asignatura_id]

    try:
        ids_busqueda.append(ObjectId(asignatura_id))
    except Exception:
        pass

    asignacion = db.asignaciones_clase.find_one({
        "_id": {
            "$in": ids_busqueda
        },
        "docente_id": docente_id,
        "activo": True
    })

    if not asignacion:

        print("❌ ASIGNACIÓN NO ENCONTRADA")

        flash(
            "Asignación de clase no encontrada.",
            "danger"
        )

        return redirect(
            url_for("docente.aulas")
        )

    grado = asignacion.get("grado")
    seccion = asignacion.get("seccion")

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

    # ======================================================
    # NOTAS EXISTENTES
    # ======================================================

    notas_existentes = list(
        db.notas.find({
            "asignatura_id": asignatura_id
        })
    )

    # ======================================================
    # ORGANIZAR NOTAS POR ESTUDIANTE Y EVALUACIÓN
    # ======================================================

    notas_mapa = {}

    for nota in notas_existentes:

        estudiante_id = str(
            nota.get("estudiante_id", "")
        )

        periodo = nota.get(
            "periodo",
            ""
        )

        evaluacion = nota.get(
            "evaluacion",
            ""
        )

        clave = (
            estudiante_id,
            periodo,
            evaluacion
        )

        notas_mapa[clave] = nota

    # ======================================================
    # ASIGNATURA
    # ======================================================

    asignatura = {
        "_id": asignacion.get("_id"),
        "codigo": asignacion.get(
            "asignatura_codigo"
        ),
        "nombre": asignacion.get(
            "asignatura_nombre"
        ),
        "nivel": asignacion.get(
            "nivel"
        ),
        "grado": grado,
        "seccion": seccion,
        "docente_id": docente_id
    }

    print("========================================")
    print("📚 ASIGNATURA:", asignatura["nombre"])
    print("👥 ESTUDIANTES:", len(estudiantes))
    print("📝 NOTAS EXISTENTES:", len(notas_existentes))
    print("========================================")

    return render_template(
        "docente/notas.html",
        asignatura=asignatura,
        estudiantes=estudiantes,
        notas_existentes=notas_existentes,
        notas_mapa=notas_mapa,
        docente=docente
    )


# ==========================================================
# GUARDAR NOTAS
# ==========================================================

@docente_bp.route(
    "/notas/guardar",
    methods=["POST"]
)
@role_required("docente")
def guardar_notas():

    print("========================================")
    print("💾 GUARDAR NOTAS")
    print("========================================")

    asignatura_id = request.form.get(
        "asignatura_id"
    )

    periodo = request.form.get(
        "periodo"
    )

    evaluacion = request.form.get(
        "evaluacion"
    )

    if not asignatura_id:
        flash(
            "No se recibió la asignación.",
            "danger"
        )

        return redirect(
            url_for("docente.aulas")
        )

    if not periodo or not evaluacion:

        flash(
            "Debe seleccionar período y evaluación.",
            "warning"
        )

        return redirect(
            url_for(
                "docente.notas",
                asignatura_id=asignatura_id
            )
        )

    # ======================================================
    # DOCENTE
    # ======================================================

    usuario = session.get("usuario")

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

    codigo_docente = str(
        docente.get("codigo", "")
    ).strip()

    docente_id = f"DOC{codigo_docente}"

    # ======================================================
    # ASIGNACIÓN
    # ======================================================

    ids_busqueda = [asignatura_id]

    # Si el ID recibido puede ser un ObjectId,
    # también lo agregamos a la búsqueda.
    try:
        ids_busqueda.append(ObjectId(asignatura_id))
    except Exception:
        pass

    asignacion = db.asignaciones_clase.find_one({
        "_id": {
            "$in": ids_busqueda
        },
        "docente_id": docente_id,
        "activo": True
    })

    if not asignacion:

        flash(
            "Asignación de clase no encontrada.",
            "danger"
        )

        return redirect(
            url_for("docente.aulas")
        )

    # ======================================================
    # ESTUDIANTES
    # ======================================================

    grado = asignacion.get("grado")
    seccion = asignacion.get("seccion")

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

    # ======================================================
    # CORTE
    # ======================================================

    campo_corte = None

    if periodo == "I Semestre":

        if evaluacion == "Primer Parcial":
            campo_corte = "corte1"

        elif evaluacion == "Segundo Parcial":
            campo_corte = "corte2"

    elif periodo == "II Semestre":

        if evaluacion == "Tercer Parcial":
            campo_corte = "corte3"

        elif evaluacion == "Cuarto Parcial":
            campo_corte = "corte4"

    if not campo_corte:

        flash(
            "Período o evaluación inválidos.",
            "warning"
        )

        return redirect(
            url_for(
                "docente.notas",
                asignatura_id=asignatura_id
            )
        )

    # ======================================================
    # GUARDAR
    # ======================================================

    guardados = 0

    for estudiante in estudiantes:

        estudiante_id = str(
            estudiante.get("_id")
        )

        acumulados = {}

        # --------------------------------------------------
        # EP1 - EP10
        # --------------------------------------------------

        for numero in range(1, 11):

            campo = (
                f"ep{numero}_{estudiante_id}"
            )

            valor = request.form.get(
                campo
            )

            if valor is None or valor == "":
                valor = 0

            try:
                nota = float(valor)
            except (
                ValueError,
                TypeError
            ):
                nota = 0

            nota = max(
                0,
                min(
                    10,
                    nota
                )
            )

            acumulados[
                f"ep{numero}"
            ] = nota

        # --------------------------------------------------
        # ACUMULADO
        # --------------------------------------------------

        acumulado = round(
            sum(acumulados.values()),
            2
        )

        promedio = round(
            acumulado / 10,
            2
        )

        estado = (
            "Aprobado"
            if acumulado >= 60
            else "Reforzamiento"
        )

        # --------------------------------------------------
        # DATOS
        # --------------------------------------------------

        datos = {

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
                usuario,

            "docente_id":
                docente_id,

            "acumulado":
                acumulado,

            "promedio":
                promedio,

            "nota":
                acumulado,

            "estado":
                estado,

            campo_corte:
                acumulado,

            "fecha":
                datetime.now()

        }

        datos.update(
            acumulados
        )

        # --------------------------------------------------
        # GUARDAR / ACTUALIZAR
        # --------------------------------------------------

        db.notas.update_one(

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
                    datos
            },

            upsert=True
        )

        guardados += 1

    print("========================================")
    print(
        "✅ TOTAL GUARDADOS:",
        guardados
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
# REPORTE DE NOTAS
# ==========================================================

@docente_bp.route("/notas/reporte/<asignatura_id>")
@role_required("docente")
def reporte_notas(asignatura_id):

    print("========================================")
    print("📊 REPORTE DE NOTAS")
    print("ASIGNACIÓN ID:", asignatura_id)
    print("========================================")

    usuario = session.get("usuario")

    if not usuario:
        flash("La sesión ha expirado.", "warning")
        return redirect(url_for("login"))

    # ======================================================
    # DOCENTE
    # ======================================================

    docente = db.docentes.find_one({
        "usuario": usuario
    })

    if not docente:
        flash("Docente no encontrado.", "danger")
        return redirect(url_for("login"))

    codigo_docente = str(
        docente.get("codigo", "")
    ).strip().upper()

    if codigo_docente.startswith("DOC"):
        docente_id = codigo_docente
    else:
        docente_id = "DOC" + codigo_docente

    # ======================================================
    # BUSCAR ASIGNACIÓN
    # ======================================================

    ids_busqueda = [asignatura_id]

    try:
        ids_busqueda.append(
            ObjectId(asignatura_id)
        )
    except Exception:
        pass

    asignacion = db.asignaciones_clase.find_one({
        "_id": {
            "$in": ids_busqueda
        },
        "docente_id": docente_id,
        "activo": True
    })

    if not asignacion:

        flash(
            "Asignación de clase no encontrada.",
            "danger"
        )

        return redirect(
            url_for("docente.lista_calificaciones")
        )

    # ======================================================
    # DATOS DE LA ASIGNATURA
    # ======================================================

    grado = asignacion.get("grado", "")
    seccion = asignacion.get("seccion", "")

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

    # ======================================================
    # ESTUDIANTES
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

    # ======================================================
    # NOTAS
    # ======================================================

    notas = list(
        db.notas.find({
            "asignatura_id": asignatura_id
        })
    )

    # ======================================================
    # ORGANIZAR NOTAS
    # ======================================================

    notas_mapa = {}

    for nota in notas:

        estudiante_id = str(
            nota.get("estudiante_id", "")
        )

        periodo = nota.get(
            "periodo",
            ""
        )

        evaluacion = nota.get(
            "evaluacion",
            ""
        )

        notas_mapa[
            (
                estudiante_id,
                periodo,
                evaluacion
            )
        ] = nota

    # ======================================================
    # DATOS PARA EL REPORTE
    # ======================================================

    reporte = []

    evaluaciones = [
        "Primer Parcial",
        "Segundo Parcial",
        "Tercer Parcial",
        "Cuarto Parcial"
    ]

    for estudiante in estudiantes:

        estudiante_id = str(
            estudiante.get("_id")
        )

        parciales = []

        for evaluacion in evaluaciones:

            nota = notas_mapa.get(
                (
                    estudiante_id,
                    "I Semestre",
                    evaluacion
                ),
                {}
            )

            suma = sum(
                float(
                    nota.get(
                        f"ep{i}",
                        0
                    ) or 0
                )
                for i in range(1, 11)
            )

            parciales.append(suma)

        acumulado = sum(parciales)

        promedio = (
            acumulado / 4
            if acumulado > 0
            else 0
        )

        if acumulado >= 240:
            estado = "Aprobado"

        elif acumulado > 0:
            estado = "Reforzamiento"

        else:
            estado = "Pendiente"

        reporte.append({
            "nombre": estudiante.get(
                "nombre",
                ""
            ),
            "parcial1": parciales[0],
            "parcial2": parciales[1],
            "parcial3": parciales[2],
            "parcial4": parciales[3],
            "acumulado": acumulado,
            "promedio": promedio,
            "estado": estado
        })

    print(
        "📚 ESTUDIANTES EN REPORTE:",
        len(reporte)
    )

    # ======================================================
    # MOSTRAR REPORTE
    # ======================================================

    return render_template(
        "docente/reporte_notas.html",

        docente=docente,

        asignatura={
            "id": str(asignacion.get("_id")),
            "codigo": asignacion.get(
                "asignatura_codigo",
                ""
            ),
            "nombre": asignacion.get(
                "asignatura_nombre",
                ""
            ),
            "nivel": asignacion.get(
                "nivel",
                ""
            ),
            "grado": grado,
            "seccion": seccion
        },

        reporte=reporte
    )

# ==========================================================
# REPORTE DE NOTAS - PDF
# ==========================================================

@docente_bp.route("/notas/reporte/<asignatura_id>/pdf")
@role_required("docente")
def reporte_notas_pdf(asignatura_id):

    print("========================================")
    print("📄 REPORTE DE NOTAS PDF")
    print("ASIGNACIÓN ID:", asignatura_id)
    print("========================================")

    usuario = session.get("usuario")

    if not usuario:
        flash(
            "La sesión ha expirado.",
            "warning"
        )
        return redirect(
            url_for("login")
        )

    # ======================================================
    # DOCENTE
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

    codigo_docente = str(
        docente.get("codigo", "")
    ).strip().upper()

    if codigo_docente.startswith("DOC"):
        docente_id = codigo_docente
    else:
        docente_id = "DOC" + codigo_docente

    # ======================================================
    # BUSCAR ASIGNACIÓN
    # ======================================================

    ids_busqueda = [asignatura_id]

    try:
        ids_busqueda.append(
            ObjectId(asignatura_id)
        )
    except Exception:
        pass

    asignacion = db.asignaciones_clase.find_one({
        "_id": {
            "$in": ids_busqueda
        },
        "docente_id": docente_id,
        "activo": True
    })

    if not asignacion:

        flash(
            "Asignación de clase no encontrada.",
            "danger"
        )

        return redirect(
            url_for(
                "docente.lista_calificaciones"
            )
        )

    # ======================================================
    # DATOS DE LA ASIGNATURA
    # ======================================================

    grado = asignacion.get(
        "grado",
        ""
    )

    seccion = asignacion.get(
        "seccion",
        ""
    )

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

    # ======================================================
    # ESTUDIANTES
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

    # ======================================================
    # NOTAS
    # ======================================================

    notas = list(
        db.notas.find({
            "asignatura_id": asignatura_id
        })
    )

    # ======================================================
    # ORGANIZAR NOTAS
    # ======================================================

    notas_mapa = {}

    for nota in notas:

        estudiante_id = str(
            nota.get(
                "estudiante_id",
                ""
            )
        )

        periodo = nota.get(
            "periodo",
            ""
        )

        evaluacion = nota.get(
            "evaluacion",
            ""
        )

        notas_mapa[
            (
                estudiante_id,
                periodo,
                evaluacion
            )
        ] = nota

    # ======================================================
    # CREAR PDF
    # ======================================================

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=25
    )

    estilos = getSampleStyleSheet()

    titulo = ParagraphStyle(
        "TituloReporte",
        parent=estilos["Title"],
        alignment=TA_CENTER,
        fontSize=18,
        leading=22,
        spaceAfter=8
    )

    subtitulo = ParagraphStyle(
        "SubtituloReporte",
        parent=estilos["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        leading=13,
        spaceAfter=4
    )

    elementos = []

    # ======================================================
    # ENCABEZADO
    # ======================================================

    elementos.append(
        Paragraph(
            "CIEM ACADÉMICO",
            titulo
        )
    )

    elementos.append(
        Paragraph(
            "REPORTE DE CALIFICACIONES",
            titulo
        )
    )

    elementos.append(
        Paragraph(
            f"<b>Asignatura:</b> "
            f"{asignacion.get('asignatura_nombre', '')}",
            subtitulo
        )
    )

    elementos.append(
        Paragraph(
            f"<b>Nivel:</b> "
            f"{asignacion.get('nivel', '')} "
            f"&nbsp;&nbsp;&nbsp; "
            f"<b>Grado:</b> {grado} "
            f"&nbsp;&nbsp;&nbsp; "
            f"<b>Sección:</b> {seccion}",
            subtitulo
        )
    )

    elementos.append(
        Paragraph(
            f"<b>Docente:</b> "
            f"{docente.get('nombre', '')}",
            subtitulo
        )
    )

    elementos.append(
        Paragraph(
            f"<b>Fecha de emisión:</b> "
            f"{datetime.now().strftime('%d/%m/%Y %H:%M')}",
            subtitulo
        )
    )

    elementos.append(
        Spacer(1, 15)
    )

    # ======================================================
    # ENCABEZADO DE TABLA
    # ======================================================

    datos = [[
        "#",
        "Estudiante",
        "I Corte",
        "II Corte",
        "III Corte",
        "IV Corte",
        "Acumulado",
        "Promedio",
        "Estado"
    ]]

    evaluaciones = [
        "Primer Parcial",
        "Segundo Parcial",
        "Tercer Parcial",
        "Cuarto Parcial"
    ]

    # ======================================================
    # ESTUDIANTES Y CALIFICACIONES
    # ======================================================

    for indice, estudiante in enumerate(
        estudiantes,
        start=1
    ):

        estudiante_id = str(
            estudiante.get("_id")
        )

        parciales = []

        for evaluacion in evaluaciones:

            nota = notas_mapa.get(
                (
                    estudiante_id,
                    "I Semestre",
                    evaluacion
                ),
                {}
            )

            suma = sum(
                float(
                    nota.get(
                        f"ep{i}",
                        0
                    ) or 0
                )
                for i in range(1, 11)
            )

            parciales.append(suma)

        acumulado = sum(
            parciales
        )

        promedio = (
            acumulado / 4
            if acumulado > 0
            else 0
        )

        if acumulado >= 240:

            estado = "Aprobado"

        elif acumulado > 0:

            estado = "Reforzamiento"

        else:

            estado = "Pendiente"

        datos.append([
            indice,
            estudiante.get(
                "nombre",
                ""
            ),
            f"{parciales[0]:.1f}",
            f"{parciales[1]:.1f}",
            f"{parciales[2]:.1f}",
            f"{parciales[3]:.1f}",
            f"{acumulado:.1f}",
            f"{promedio:.2f}",
            estado
        ])

    # ======================================================
    # TABLA
    # ======================================================

    tabla = Table(
        datos,
        repeatRows=1,
        colWidths=[
            30,
            220,
            65,
            65,
            65,
            65,
            80,
            70,
            100
        ]
    )

    tabla.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#0d2a52")
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
                "FONTNAME",
                (0, 1),
                (-1, -1),
                "Helvetica"
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8
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
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                5
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                5
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
    # PIE DEL REPORTE
    # ======================================================

    elementos.append(
        Paragraph(
            "CIEM Académico - Reporte generado por el sistema",
            subtitulo
        )
    )

    # ======================================================
    # GENERAR PDF
    # ======================================================

    doc.build(
        elementos
    )

    buffer.seek(0)

    nombre_archivo = (
        "Reporte_Notas_"
        + str(
            asignacion.get(
                "asignatura_codigo",
                "asignatura"
            )
        )
        + "_"
        + str(grado)
        + "_"
        + str(seccion)
        + ".pdf"
    )

    print(
        "✅ PDF GENERADO:",
        nombre_archivo
    )

    return send_file(
        buffer,
        as_attachment=True,
        download_name=nombre_archivo,
        mimetype="application/pdf"
    )

# ==========================================================
# DESCARGAR REPORTE DE NOTAS EN PDF
# ==========================================================

@docente_bp.route("/notas/pdf/<asignatura_id>")
@role_required("docente")
def descargar_reporte_notas(asignatura_id):

    print("========================================")
    print("📄 DESCARGANDO PDF DE NOTAS")
    print("ASIGNACIÓN ID:", asignatura_id)
    print("========================================")

    usuario = session.get("usuario")

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

    codigo_docente = str(
        docente.get("codigo", "")
    ).strip().upper()

    if codigo_docente.startswith("DOC"):
        docente_id = codigo_docente
    else:
        docente_id = "DOC" + codigo_docente

    # ======================================================
    # BUSCAR ASIGNACIÓN
    # ======================================================

    ids_busqueda = [asignatura_id]

    try:
        ids_busqueda.append(
            ObjectId(asignatura_id)
        )
    except Exception:
        pass

    asignacion = db.asignaciones_clase.find_one({
        "_id": {
            "$in": ids_busqueda
        },
        "docente_id": docente_id,
        "activo": True
    })

    if not asignacion:

        flash(
            "Asignación no encontrada.",
            "danger"
        )

        return redirect(
            url_for("docente.lista_calificaciones")
        )

    grado = asignacion.get(
        "grado",
        ""
    )

    seccion = asignacion.get(
        "seccion",
        ""
    )

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

    # ======================================================
    # ESTUDIANTES
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

    # ======================================================
    # NOTAS
    # ======================================================

    notas = list(
        db.notas.find({
            "asignatura_id": asignatura_id
        })
    )

    notas_mapa = {}

    for nota in notas:

        clave = (
            str(
                nota.get(
                    "estudiante_id",
                    ""
                )
            ),
            nota.get(
                "periodo",
                ""
            ),
            nota.get(
                "evaluacion",
                ""
            )
        )

        notas_mapa[clave] = nota

    # ======================================================
    # CREAR PDF
    # ======================================================

    import io

    buffer = io.BytesIO()

    documento = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=25,
        leftMargin=25,
        topMargin=30,
        bottomMargin=30
    )

    estilos = getSampleStyleSheet()

    titulo = estilos["Title"]
    titulo.alignment = TA_CENTER

    elementos = []

    elementos.append(
        Paragraph(
            "CIEM ACADÉMICO",
            titulo
        )
    )

    elementos.append(
        Spacer(1, 10)
    )

    elementos.append(
        Paragraph(
            f"<b>Reporte de Calificaciones</b>",
            estilos["Heading2"]
        )
    )

    elementos.append(
        Paragraph(
            f"Asignatura: "
            f"{asignacion.get('asignatura_nombre', '')}",
            estilos["Normal"]
        )
    )

    elementos.append(
        Paragraph(
            f"Grado: {grado} | "
            f"Sección: {seccion}",
            estilos["Normal"]
        )
    )

    elementos.append(
        Paragraph(
            f"Docente: "
            f"{docente.get('nombre', '')}",
            estilos["Normal"]
        )
    )

    elementos.append(
        Spacer(1, 15)
    )

    # ======================================================
    # TABLA
    # ======================================================

    datos = [

        [
            "#",
            "Estudiante",
            "I Parcial",
            "II Parcial",
            "III Parcial",
            "IV Parcial",
            "Acumulado",
            "Promedio",
            "Estado"
        ]

    ]

    for indice, estudiante in enumerate(
        estudiantes,
        start=1
    ):

        estudiante_id = str(
            estudiante.get("_id")
        )

        parciales = []

        for evaluacion in [
            "Primer Parcial",
            "Segundo Parcial",
            "Tercer Parcial",
            "Cuarto Parcial"
        ]:

            nota = notas_mapa.get(
                (
                    estudiante_id,
                    "I Semestre",
                    evaluacion
                ),
                {}
            )

            suma = sum(
                float(
                    nota.get(
                        f"ep{i}",
                        0
                    ) or 0
                )
                for i in range(1, 11)
            )

            parciales.append(suma)

        acumulado = sum(parciales)

        promedio = (
            acumulado / 4
            if acumulado > 0
            else 0
        )

        if acumulado >= 240:
            estado = "Aprobado"

        elif acumulado > 0:
            estado = "Reforzamiento"

        else:
            estado = "Pendiente"

        datos.append([
            indice,
            estudiante.get(
                "nombre",
                ""
            ),
            f"{parciales[0]:.1f}",
            f"{parciales[1]:.1f}",
            f"{parciales[2]:.1f}",
            f"{parciales[3]:.1f}",
            f"{acumulado:.1f}",
            f"{promedio:.2f}",
            estado
        ])

    tabla = Table(
        datos,
        repeatRows=1,
        colWidths=[
            30,
            210,
            70,
            70,
            70,
            70,
            75,
            65,
            90
        ]
    )

    tabla.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#08142c")
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
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER"
            ),

            (
                "ALIGN",
                (1, 1),
                (1, -1),
                "LEFT"
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "FONTNAME",
                (0, 1),
                (-1, -1),
                "Helvetica"
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                9
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                7
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                7
            )

        ])
    )

    elementos.append(tabla)

    elementos.append(
        Spacer(1, 15)
    )

    elementos.append(
        Paragraph(
            "CIEM Académico - Sistema de Gestión Académica",
            estilos["Normal"]
        )
    )

    documento.build(elementos)

    buffer.seek(0)

    respuesta = make_response(
        buffer.getvalue()
    )

    respuesta.headers[
        "Content-Type"
    ] = "application/pdf"

    nombre_archivo = (
        "Reporte_Notas_"
        + str(
            asignacion.get(
                "asignatura_codigo",
                "Asignatura"
            )
        )
        + "_"
        + str(grado)
        + str(seccion)
        + ".pdf"
    )

    respuesta.headers[
        "Content-Disposition"
    ] = (
        "attachment; filename="
        + nombre_archivo
    )

    return respuesta
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

    codigo_docente = str(
        docente.get("codigo", "")
    ).strip().upper()

    if codigo_docente.startswith("DOC"):

        docente_id = codigo_docente

    else:

        docente_id = f"DOC{codigo_docente}"

    # =====================================
    # OBTENER ASIGNACIONES
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
    # DEPURACIÓN
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

    print("")
    print("========== VERIFICACIÓN REAL DE IDs ==========")

    for clase in clases:

        id_clase = clase.get("_id")

        print(
            "ID:",
            repr(id_clase),
            "| TIPO:",
            type(id_clase),
            "| EXISTE:",
            db.asignaciones_clase.count_documents({
                "_id": id_clase
            })
        )

    print("==============================================")
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

# ============================================================
# SELECCIONAR CLASE PARA CALIFICACIONES
# ============================================================

@docente_bp.route("/calificaciones")
@role_required("docente")
def lista_calificaciones():

    print("========================================================")
    print("📋 SELECCIÓN DE CLASE PARA CALIFICACIONES")
    print("========================================================")

    # ========================================================
    # 1. USUARIO DE LA SESIÓN
    # ========================================================

    usuario = session.get("usuario")

    print("👤 USUARIO:", usuario)

    if not usuario:

        print("❌ NO HAY USUARIO EN LA SESIÓN")

        flash(
            "La sesión ha expirado.",
            "warning"
        )

        return redirect(
            url_for("login")
        )

    # ========================================================
    # 2. BUSCAR DOCENTE
    # ========================================================

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

    # ========================================================
    # 3. CONSTRUIR ID OFICIAL DEL DOCENTE
    # ========================================================

    codigo_docente = str(
        docente.get(
            "codigo",
            ""
        )
    ).strip().upper()

    if not codigo_docente:

        print("❌ EL DOCENTE NO TIENE CÓDIGO")

        flash(
            "El docente no tiene un código asignado.",
            "danger"
        )

        return redirect(
            url_for("login")
        )

    if codigo_docente.startswith("DOC"):

        docente_id = codigo_docente

    else:

        docente_id = "DOC" + codigo_docente

    print(
        "👨‍🏫 DOCENTE:",
        docente.get(
            "nombre",
            ""
        )
    )

    print(
        "🔢 CÓDIGO:",
        codigo_docente
    )

    print(
        "🆔 DOCENTE ID:",
        docente_id
    )
    # ========================================================
    # 4. BUSCAR CLASES
    # ========================================================

    print("========================================================")
    print("🔎 BUSCANDO CLASES DEL DOCENTE")
    print("========================================================")

    # --------------------------------------------------------
    # FUENTE OFICIAL DEL DASHBOARD:
    # asignaciones_clase
    # --------------------------------------------------------

    filtro_clases = {
        "docente_id": docente_id,
        "activo": True
    }

    # --------------------------------------------------------
    # CORRECCIÓN:
    # Informática Educativa NO pertenece a Asley (DOC014).
    #
    # Asley debe tener únicamente sus 4 clases:
    # AEP, CV, DDM y HIN.
    #
    # DOC015 será quien tenga Informática Educativa.
    # --------------------------------------------------------

    if docente_id == "DOC014":

        filtro_clases["asignatura_codigo"] = {
            "$ne": "INF"
        }

    clases = list(
        db.asignaciones_clase.find(
            filtro_clases
        ).sort(
            "asignatura_nombre",
            1
        )
    )

    print(
        "📂 COLECCIÓN: asignaciones_clase"
    )

    print(
        "👨‍🏫 DOCENTE ID:",
        repr(docente_id)
    )

    print(
        "📚 TOTAL CLASES ENCONTRADAS:",
        len(clases)
    )

    # --------------------------------------------------------
    # MOSTRAR LAS CLASES ENCONTRADAS
    # --------------------------------------------------------

    for clase in clases:

        print("----------------------------------------")

        print(
            "🆔 ID:",
            clase.get("_id")
        )

        print(
            "🔤 CÓDIGO:",
            clase.get(
                "asignatura_codigo",
                ""
            )
        )

        print(
            "📖 ASIGNATURA:",
            clase.get(
                "asignatura_nombre",
                ""
            )
        )

        print(
            "🎓 NIVEL:",
            clase.get(
                "nivel",
                ""
            )
        )

        print(
            "🎓 GRADO:",
            clase.get(
                "grado",
                ""
            )
        )

        print(
            "🏫 SECCIÓN:",
            clase.get(
                "seccion",
                ""
            )
        )

        print(
            "👨‍🏫 DOCENTE:",
            clase.get(
                "docente_id",
                ""
            )
        )

        print(
            "📌 ACTIVO:",
            clase.get(
                "activo",
                False
            )
        )

    print("========================================================")

    # ========================================================
    # 5. PREPARAR DATOS PARA EL HTML
    # ========================================================

    for clase in clases:

        # ----------------------------------------------------
        # ID DE LA ASIGNACIÓN
        # ----------------------------------------------------

        clase["id_str"] = str(
            clase.get("_id")
        )

        # ----------------------------------------------------
        # CÓDIGO
        # ----------------------------------------------------

        clase["codigo"] = clase.get(
            "asignatura_codigo",
            ""
        )

        # ----------------------------------------------------
        # NOMBRE
        # ----------------------------------------------------

        clase["nombre"] = clase.get(
            "asignatura_nombre",
            ""
        )

        # ----------------------------------------------------
        # ASIGNATURA_ID
        #
        # La colección asignaciones_clase utiliza su propio
        # _id como identificador de la asignación.
        # ----------------------------------------------------

        clase["asignatura_id"] = str(
            clase.get("_id")
        )

        # ----------------------------------------------------
        # DOCENTE
        # ----------------------------------------------------

        clase["docente_id"] = clase.get(
            "docente_id",
            docente_id
        )

        clase["docente_nombre"] = clase.get(
            "docente_nombre",
            docente.get(
                "nombre",
                ""
            )
        )

        # ----------------------------------------------------
        # NIVEL
        # ----------------------------------------------------

        clase["nivel"] = clase.get(
            "nivel",
            ""
        )

        # ----------------------------------------------------
        # GRADO
        # ----------------------------------------------------

        clase["grado"] = clase.get(
            "grado",
            ""
        )

        # ----------------------------------------------------
        # SECCIÓN
        # ----------------------------------------------------

        clase["seccion"] = clase.get(
            "seccion",
            ""
        )

        # ----------------------------------------------------
        # ESTADO
        # ----------------------------------------------------

        clase["estado"] = (
            "Activo"
            if clase.get("activo", True)
            else "Inactivo"
        )

    # ========================================================
    # 6. MOSTRAR LAS CLASES EN CONSOLA
    # ========================================================

    for clase in clases:

        print("----------------------------------------")

        print(
            "🆔 ID:",
            clase.get("_id")
        )

        print(
            "🔤 CÓDIGO:",
            clase.get(
                "codigo",
                ""
            )
        )

        print(
            "📖 ASIGNATURA:",
            clase.get(
                "nombre",
                ""
            )
        )

        print(
            "👨‍🏫 DOCENTE:",
            clase.get(
                "docente_id",
                ""
            )
        )

        print(
            "🎓 NIVEL:",
            clase.get(
                "nivel",
                ""
            )
        )

        print(
            "🎓 GRADO:",
            clase.get(
                "grado",
                ""
            )
        )

        print(
            "🏫 SECCIÓN:",
            clase.get(
                "seccion",
                ""
            )
        )

        print(
            "📌 ESTADO:",
            clase.get(
                "estado",
                ""
            )
        )

    print("========================================================")

    # ========================================================
    # 7. TOTAL DE CLASES
    # ========================================================

    total_asignaturas = len(
        clases
    )

    print(
        "📚 TOTAL CLASES PARA CALIFICACIONES:",
        total_asignaturas
    )

    # ========================================================
    # 8. RESUMEN FINAL
    # ========================================================

    print("========================================================")
    print("📋 RESUMEN DE CALIFICACIONES")
    print("========================================================")

    for clase in clases:

        print(
            clase.get(
                "id_str",
                ""
            ),
            "|",
            clase.get(
                "codigo",
                ""
            ),
            "|",
            clase.get(
                "nombre",
                ""
            ),
            "| NIVEL:",
            clase.get(
                "nivel",
                ""
            ),
            "| GRADO:",
            clase.get(
                "grado",
                ""
            ),
            "| SECCIÓN:",
            clase.get(
                "seccion",
                ""
            ),
            "| DOCENTE:",
            clase.get(
                "docente_id",
                ""
            )
        )

    print("========================================================")

    # ========================================================
    # 9. MOSTRAR PANTALLA
    # ========================================================

    return render_template(

        "docente/seleccionar_calificaciones.html",

        clases=clases,

        docente=docente,

        docente_id=docente_id,

        total_asignaturas=total_asignaturas

    )
# ============================================================
# GUARDAR INCIDENCIA
# ============================================================

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

    # ========================================================
    # 1. DATOS DEL FORMULARIO
    # ========================================================

    estudiante_id = str(
        request.form.get(
            "estudiante_id",
            ""
        )
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

    asignatura_id = str(
        request.form.get(
            "asignatura_id",
            ""
        )
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
        "📚 ASIGNACIÓN:",
        asignatura_id
    )

    # ========================================================
    # 2. FUNCIÓN PARA REGRESAR A LA CLASE
    # ========================================================

    def regresar():

        if asignatura_id:

            return redirect(
                url_for(
                    "docente.registrar_incidencia",
                    asignatura_id=asignatura_id
                )
            )

        return redirect(
            url_for(
                "docente.lista_incidencias"
            )
        )

    # ========================================================
    # 3. VALIDAR ESTUDIANTE
    # ========================================================

    if not estudiante_id:

        flash(
            "Debe seleccionar un estudiante.",
            "warning"
        )

        return regresar()

    # ========================================================
    # 4. VALIDAR TIPO
    # ========================================================

    if not tipo:

        flash(
            "Debe seleccionar el tipo de incidencia.",
            "warning"
        )

        return regresar()

    # ========================================================
    # 5. VALIDAR DESCRIPCIÓN
    # ========================================================

    if not descripcion:

        flash(
            "Debe escribir una descripción.",
            "warning"
        )

        return regresar()

    # ========================================================
    # 6. VALIDAR FECHA
    # ========================================================

    if not fecha:

        flash(
            "Debe indicar la fecha.",
            "warning"
        )

        return regresar()

    # ========================================================
    # 7. BUSCAR DOCENTE
    # ========================================================

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

    # ========================================================
    # 8. OBTENER ID OFICIAL DEL DOCENTE
    # ========================================================

    codigo_docente = str(
        docente.get("codigo", "")
    ).strip().upper()

    if codigo_docente.startswith("DOC"):

        docente_id = codigo_docente

    else:

        docente_id = f"DOC{codigo_docente}"

    print(
        "👨‍🏫 DOCENTE:",
        docente.get("nombre")
    )

    print(
        "🆔 DOCENTE ID:",
        docente_id
    )

    # ========================================================
    # 9. BUSCAR ESTUDIANTE
    # ========================================================

    ids_estudiante = [
        estudiante_id
    ]

    try:

        ids_estudiante.append(
            ObjectId(estudiante_id)
        )

    except Exception:

        pass

    estudiante = db.estudiantes.find_one({

        "_id": {
            "$in": ids_estudiante
        },

        "estado": "activo"

    })

    if not estudiante:

        flash(
            "El estudiante seleccionado no existe o está inactivo.",
            "danger"
        )

        return regresar()

    print(
        "✅ ESTUDIANTE ENCONTRADO:",
        estudiante.get("nombre")
    )

    # ========================================================
    # 10. BUSCAR ASIGNACIÓN
    # ========================================================

    ids_asignacion = [
        asignatura_id
    ]

    try:

        ids_asignacion.append(
            ObjectId(asignatura_id)
        )

    except Exception:

        pass

    asignacion = db.asignaciones_clase.find_one({

        "_id": {
            "$in": ids_asignacion
        },

        "docente_id": docente_id,

        "activo": True

    })

    print("========================================")
    print("📚 ASIGNACIÓN ENCONTRADA:")
    print(asignacion)
    print("========================================")

    if not asignacion:

        flash(
            "La clase seleccionada no es válida.",
            "danger"
        )

        return redirect(
            url_for(
                "docente.lista_incidencias"
            )
        )

    # ========================================================
    # 11. DATOS DE LA ASIGNACIÓN
    # ========================================================

    asignacion_id_real = str(
        asignacion.get("_id")
    )

    asignatura_nombre = asignacion.get(
        "asignatura_nombre",
        ""
    )

    asignatura_codigo = asignacion.get(
        "asignatura_codigo",
        ""
    )

    grado = asignacion.get(
        "grado",
        estudiante.get("grado", "")
    )

    seccion = asignacion.get(
        "seccion",
        estudiante.get("seccion", "")
    )

    # ========================================================
    # 12. CREAR INCIDENCIA
    # ========================================================

    incidencia = {

        "estudiante_id":
            str(
                estudiante.get("_id")
            ),

        "estudiante_nombre":
            estudiante.get(
                "nombre",
                ""
            ),

        "docente":
            usuario,

        "docente_id":
            docente_id,

        "docente_nombre":
            docente.get(
                "nombre",
                ""
            ),

        "tipo":
            tipo,

        "descripcion":
            descripcion,

        "fecha":
            fecha,

        "asignatura_id":
            asignacion_id_real,

        "asignatura":
            asignatura_nombre,

        "asignatura_codigo":
            asignatura_codigo,

        "grado":
            grado,

        "seccion":
            seccion,

        "estado":
            "pendiente",

        "fecha_registro":
            datetime.now()

    }

    # ========================================================
    # 13. GUARDAR EN MONGODB
    # ========================================================

    resultado = db.incidencias.insert_one(
        incidencia
    )

    print("========================================")
    print("✅ INCIDENCIA GUARDADA")
    print(
        "🆔 ID:",
        resultado.inserted_id
    )
    print(
        "👤 ESTUDIANTE:",
        estudiante.get("nombre")
    )
    print(
        "📚 ASIGNATURA:",
        asignatura_nombre
    )
    print(
        "⚠️ TIPO:",
        tipo
    )
    print("========================================")

    # ========================================================
    # 14. MENSAJE
    # ========================================================

    flash(
        "Incidencia registrada correctamente.",
        "success"
    )

    # ========================================================
    # 15. REGRESAR
    # ========================================================

    return regresar()

# =========================================================
# REGISTRAR INCIDENCIA PARA UNA CLASE
# =========================================================

@docente_bp.route(
    "/incidencias/registrar/<asignatura_id>"
)
@role_required("docente")
def registrar_incidencia(asignatura_id):

    print("========================================")
    print("⚠️ REGISTRAR INCIDENCIA")
    print("ASIGNACIÓN:", asignatura_id)
    print("========================================")

    usuario = session.get("usuario")

    # =====================================================
    # 1. BUSCAR DOCENTE
    # =====================================================

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

    # =====================================================
    # 2. OBTENER ID OFICIAL DEL DOCENTE
    # =====================================================

    codigo_docente = str(
        docente.get("codigo", "")
    ).strip().upper()

    if codigo_docente.startswith("DOC"):

        docente_id = codigo_docente

    else:

        docente_id = f"DOC{codigo_docente}"

    print("👨‍🏫 DOCENTE:", docente.get("nombre"))
    print("🆔 DOCENTE ID:", docente_id)

    # =====================================================
    # 3. PREPARAR ID DE ASIGNACIÓN
    # =====================================================

    ids_busqueda = [
        str(asignatura_id)
    ]

    try:

        ids_busqueda.append(
            ObjectId(str(asignatura_id))
        )

    except Exception:

        pass

    print("🔎 IDS PARA BUSCAR:", ids_busqueda)

    # =====================================================
    # 4. BUSCAR ASIGNACIÓN
    # =====================================================

    asignacion = db.asignaciones_clase.find_one({

        "_id": {
            "$in": ids_busqueda
        },

        "docente_id": docente_id,

        "activo": True

    })

    print("📚 ASIGNACIÓN ENCONTRADA:")
    print(asignacion)

    # =====================================================
    # 5. VALIDAR ASIGNACIÓN
    # =====================================================

    if not asignacion:

        print("❌ ASIGNACIÓN NO ENCONTRADA")
        print("❌ ID RECIBIDO:", asignatura_id)
        print("❌ DOCENTE:", docente_id)

        flash(
            "La clase seleccionada no existe o no está asignada al docente.",
            "danger"
        )

        return redirect(
            url_for(
                "docente.lista_incidencias"
            )
        )

    # =====================================================
    # 6. INFORMACIÓN DE LA CLASE
    # =====================================================

    grado = asignacion.get(
        "grado",
        ""
    )

    seccion = asignacion.get(
        "seccion",
        ""
    )

    asignatura_codigo = asignacion.get(
        "asignatura_codigo",
        ""
    )

    asignatura_nombre = asignacion.get(
        "asignatura_nombre",
        ""
    )

    print("========================================")
    print("✅ CLASE ENCONTRADA")
    print("🆔 ID:", asignacion.get("_id"))
    print("📚 CÓDIGO:", asignatura_codigo)
    print("📖 NOMBRE:", asignatura_nombre)
    print("🎓 GRADO:", grado)
    print("🏫 SECCIÓN:", seccion)
    print("👨‍🏫 DOCENTE:", docente_id)
    print("========================================")

    # =====================================================
    # 7. CONVERTIR GRADO
    # =====================================================

    mapa_grados = {

        "1": "1er Grado",
        "2": "2do Grado",
        "3": "3er Grado",
        "4": "4to Grado",
        "5": "5to Grado",
        "6": "6to Grado"

    }

    grado_estudiante = mapa_grados.get(
        str(grado).strip(),
        grado
    )

    print(
        "🎓 GRADO PARA ESTUDIANTES:",
        grado_estudiante
    )

    print(
        "🏫 SECCIÓN PARA ESTUDIANTES:",
        seccion
    )

    # =====================================================
    # 8. BUSCAR ESTUDIANTES
    # =====================================================

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
            estudiante.get("_id"),
            "|",
            estudiante.get("nombre"),
            "| GRADO:",
            estudiante.get("grado"),
            "| SECCIÓN:",
            estudiante.get("seccion")
        )

    # =====================================================
    # 9. BUSCAR INCIDENCIAS EXISTENTES
    # =====================================================

    incidencia_id = str(
        asignacion.get("_id")
    )

    incidencias = list(
        db.incidencias.find({

            "asignatura_id": incidencia_id

        }).sort(
            "fecha",
            -1
        )
    )

    print(
        "⚠️ INCIDENCIAS EXISTENTES:",
        len(incidencias)
    )

    # =====================================================
    # 10. PREPARAR DATOS PARA EL HTML
    # =====================================================

    asignatura = {

        "_id":
            asignacion.get("_id"),

        "codigo":
            asignatura_codigo,

        "nombre":
            asignatura_nombre,

        "nivel":
            asignacion.get(
                "nivel",
                ""
            ),

        "grado":
            grado,

        "seccion":
            seccion,

        "docente_id":
            docente_id

    }

    # =====================================================
    # 11. FECHA ACTUAL
    # =====================================================

    fecha = datetime.now().strftime(
        "%Y-%m-%d"
    )

    # =====================================================
    # 12. MOSTRAR FORMULARIO
    # =====================================================

    print("========================================")
    print("✅ ABRIENDO FORMULARIO DE INCIDENCIA")
    print("📚 ASIGNATURA:", asignatura_nombre)
    print("👥 ESTUDIANTES:", len(estudiantes))
    print("========================================")

    return render_template(

        "docente/incidencias.html",

        clase=asignacion,

        asignatura=asignatura,

        estudiantes=estudiantes,

        incidencias=incidencias,

        docente=docente,

        docente_id=docente_id,

        fecha=fecha

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

    print("========================================")
    print("📋 ASISTENCIA DESDE PERFIL DEL ESTUDIANTE")
    print("========================================")

    # =====================================
    # BUSCAR ESTUDIANTE
    # =====================================

    estudiante = db.estudiantes.find_one({
        "_id": estudiante_id
    })

    if not estudiante:

        flash(
            "Estudiante no encontrado.",
            "danger"
        )

        return redirect(
            url_for("docente.estudiantes")
        )

    # =====================================
    # BUSCAR DOCENTE
    # =====================================

    docente = db.docentes.find_one({
        "usuario": session.get("usuario")
    })

    if not docente:

        flash(
            "Docente no encontrado.",
            "danger"
        )

        return redirect(
            url_for("docente.estudiantes")
        )

    # =====================================
    # ID OFICIAL DEL DOCENTE
    # =====================================

    codigo_docente = str(
        docente.get("codigo", "")
    ).strip().upper()

    if codigo_docente.startswith("DOC"):

        docente_id = codigo_docente

    else:

        docente_id = f"DOC{codigo_docente}"

    print("👨‍🏫 DOCENTE:", docente.get("nombre"))
    print("🆔 DOCENTE ID:", docente_id)

    # =====================================
    # DATOS DEL ESTUDIANTE
    # =====================================

    grado = estudiante.get("grado")
    seccion = estudiante.get("seccion")

    print("🎓 GRADO:", grado)
    print("🏫 SECCIÓN:", seccion)

    # =====================================
    # BUSCAR CLASE EN ASIGNACIONES_CLASE
    # =====================================
    #
    # YA NO BUSCAMOS EN db.asignaturas
    #
    # La colección oficial es:
    #
    # db.asignaciones_clase
    # =====================================

    asignacion = db.asignaciones_clase.find_one({

        "docente_id": docente_id,

        "grado": grado,

        "seccion": seccion,

        "activo": True

    })

    # =====================================
    # SI NO ENCUENTRA
    # =====================================

    if not asignacion:

        print(
            "❌ NO SE ENCONTRÓ ASIGNACIÓN"
        )

        flash(
            "No existe una clase asignada a este docente para el grado y sección del estudiante.",
            "warning"
        )

        return redirect(
            url_for("docente.estudiantes")
        )

    # =====================================
    # MOSTRAR INFORMACIÓN
    # =====================================

    print("✅ ASIGNACIÓN ENCONTRADA")
    print(
        "ID:",
        asignacion.get("_id")
    )

    print(
        "ASIGNATURA:",
        asignacion.get("asignatura_nombre")
    )

    print(
        "GRADO:",
        asignacion.get("grado")
    )

    print(
        "SECCIÓN:",
        asignacion.get("seccion")
    )

    # =====================================
    # IR A LA ASISTENCIA
    # =====================================

    return redirect(
        url_for(
            "docente.asistencia",
            asignatura_id=str(
                asignacion.get("_id")
            )
        )
    )
# =========================================================
# GUARDAR ASISTENCIA
# =========================================================

@docente_bp.route(
    "/asistencia/guardar",
    methods=["POST"]
)
@role_required("docente")
def guardar_asistencia():

    print("========================================")
    print("💾 GUARDANDO ASISTENCIA")
    print("========================================")

    # =====================================================
    # DATOS DEL FORMULARIO
    # =====================================================

    asignacion_id = request.form.get(
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
        asignacion_id
    )

    print(
        "📅 FECHA:",
        fecha
    )

    print(
        "👤 USUARIO:",
        usuario
    )

    # =====================================================
    # BUSCAR DOCENTE
    # =====================================================

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

    # =====================================================
    # CONSTRUIR ID OFICIAL DEL DOCENTE
    # =====================================================

    codigo_docente = str(
        docente.get(
            "codigo",
            ""
        )
    ).strip().upper()

    if codigo_docente.startswith("DOC"):

        docente_id = codigo_docente

    else:

        docente_id = (
            f"DOC{codigo_docente}"
        )

    print(
        "🆔 DOCENTE ID:",
        docente_id
    )

    # =====================================================
    # BUSCAR ASIGNACIÓN
    # =====================================================

    asignacion = None

    # -----------------------------------------------------
    # PRIMERO COMO STRING
    # -----------------------------------------------------

    if asignacion_id:

        asignacion = (
            db.asignaciones_clase.find_one({
                "_id": asignacion_id,
                "docente_id": docente_id,
                "activo": True
            })
        )

    # -----------------------------------------------------
    # DESPUÉS COMO OBJECTID
    # -----------------------------------------------------

    if not asignacion:

        try:

            from bson import ObjectId

            if ObjectId.is_valid(
                str(asignacion_id)
            ):

                asignacion = (
                    db.asignaciones_clase.find_one({
                        "_id": ObjectId(
                            str(asignacion_id)
                        ),
                        "docente_id": docente_id,
                        "activo": True
                    })
                )

        except Exception as e:

            print(
                "⚠️ Error ObjectId:",
                e
            )

    # =====================================================
    # VALIDAR ASIGNACIÓN
    # =====================================================

    if not asignacion:

        print(
            "❌ ASIGNACIÓN NO ENCONTRADA"
        )

        print(
            "ID RECIBIDO:",
            asignacion_id
        )

        print(
            "DOCENTE:",
            docente_id
        )

        flash(
            "La asignación de clase no existe o no pertenece a este docente.",
            "danger"
        )

        return redirect(
            url_for(
                "docente.lista_asistencia"
            )
        )

    # =====================================================
    # DATOS DE LA CLASE
    # =====================================================

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
        "asignatura_codigo",
        ""
    )

    asignatura_nombre = asignacion.get(
        "asignatura_nombre",
        ""
    )

    print(
        "📚 ASIGNATURA:",
        asignatura_codigo,
        "|",
        asignatura_nombre
    )

    print(
        "🎓 NIVEL:",
        nivel
    )

    print(
        "📖 GRADO:",
        grado
    )

    print(
        "🏫 SECCIÓN:",
        seccion
    )

    # =====================================================
    # CONVERTIR GRADO
    # =====================================================

    mapa_grados = {

        "1": "1er Grado",
        "2": "2do Grado",
        "3": "3er Grado",
        "4": "4to Grado",
        "5": "5to Grado",
        "6": "6to Grado",

        "1er Grado": "1er Grado",
        "2do Grado": "2do Grado",
        "3er Grado": "3er Grado",
        "4to Grado": "4to Grado",
        "5to Grado": "5to Grado",
        "6to Grado": "6to Grado"

    }

    grado_estudiante = mapa_grados.get(
        str(grado),
        grado
    )

    print(
        "🔄 GRADO ESTUDIANTE:",
        grado_estudiante
    )

    # =====================================================
    # BUSCAR ESTUDIANTES
    # =====================================================

    grado_asignacion = str(
        grado
    ).strip()

    # Grados equivalentes
    grados_equivalentes = {

        "1": [
            "1",
            "1er Grado",
            "1ro Grado",
            "Primer Grado"
        ],

        "2": [
            "2",
            "2do Grado",
            "2do grado",
            "Segundo Grado"
        ],

        "3": [
            "3",
            "3er Grado",
            "3ro Grado",
            "Tercer Grado"
        ],

        "4": [
            "4",
            "4to Grado",
            "Cuarto Grado"
        ],

        "5": [
            "5",
            "5to Grado",
            "Quinto Grado"
        ],

        "6": [
            "6",
            "6to Grado",
            "Sexto Grado"
        ],

        "I Nivel": [
            "I Nivel"
        ],

        "II Nivel": [
            "II Nivel"
        ],

        "III Nivel": [
            "III Nivel"
        ],

        "1 Año": [
            "1 Año",
            "Primer Año"
        ],

        "2 Año": [
            "2 Año",
            "Segundo Año"
        ],

        "3 Año": [
            "3 Año",
            "Tercer Año"
        ],

        "4 Año": [
            "4 Año",
            "Cuarto Año"
        ],

        "5 Año": [
            "5 Año",
            "Quinto Año"
        ]
    }

    grados_busqueda = grados_equivalentes.get(
        grado_asignacion,
        [grado_asignacion]
    )

    print("========================================")
    print("🎓 GRADO DE LA ASIGNACIÓN:",
        repr(grado_asignacion))

    print("🎓 GRADOS A BUSCAR:",
        grados_busqueda)

    print("🏫 SECCIÓN:",
        repr(seccion))
    print("========================================")

    estudiantes = list(
        db.estudiantes.find({

            "grado": {
                "$in": grados_busqueda
            },

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
            "👤",
            estudiante.get("nombre"),
            "| GRADO:",
            estudiante.get("grado"),
            "| SECCIÓN:",
            estudiante.get("seccion")
        )
    # =====================================================
    # ESTADOS PERMITIDOS
    # =====================================================

    estados_validos = [

        "Presente",

        "Ausente",

        "Justificada"

    ]

    # =====================================================
    # GUARDAR ASISTENCIA
    # =====================================================

    for estudiante in estudiantes:

        estudiante_id = estudiante.get(
            "_id"
        )

        estado = request.form.get(
            f"estado_{estudiante_id}"
        )

        motivo = request.form.get(
            f"motivo_{estudiante_id}",
            ""
        ).strip()

        # -------------------------------------------------
        # VALIDAR ESTADO
        # -------------------------------------------------

        if estado not in estados_validos:

            flash(
                f"Estado inválido para {estudiante.get('nombre')}.",
                "danger"
            )

            return redirect(
                url_for(
                    "docente.asistencia",
                    asignatura_id=str(
                        asignacion.get("_id")
                    )
                )
            )

        # -------------------------------------------------
        # MOTIVO
        # -------------------------------------------------

        if estado != "Justificada":

            motivo = ""

        # -------------------------------------------------
        # GUARDAR
        # -------------------------------------------------

        db.asistencias.update_one(

            {

                "asignacion_id":
                    str(
                        asignacion.get("_id")
                    ),

                "estudiante_id":
                    estudiante_id,

                "fecha":
                    fecha

            },

            {

                "$set": {

                    "asignacion_id":
                        str(
                            asignacion.get("_id")
                        ),

                    "asignatura_id":
                        str(
                            asignacion.get("_id")
                        ),

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

                    "nivel":
                        nivel,

                    "grado":
                        grado_estudiante,

                    "seccion":
                        seccion,

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
            "|",
            estado
        )

    # =====================================================
    # FINALIZAR
    # =====================================================

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
            asignatura_id=str(
                asignacion.get("_id")
            )
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