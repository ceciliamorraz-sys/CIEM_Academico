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
from datetime import datetime
from flask_pymongo import PyMongo
from routes.mined import datos_mined, estadistica_grado
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app


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


# ==========================
# DASHBOARD DOCENTE
# ==========================

@docente_bp.route("/")
@role_required("docente")
def dashboard_docente():

    usuario = session.get("usuario")

    # ==========================================
    # BUSCAR DOCENTE
    # ==========================================

    docente = db.docentes.find_one({
        "usuario": usuario
    })

    # ==========================================
    # VALIDAR DOCENTE
    # ==========================================

    if not docente:

        flash(
            "Docente no encontrado",
            "danger"
        )

        return redirect(
            url_for("login")
        )

    # ==========================================
    # IDENTIFICAR DOCENTE
    # ==========================================

    docente_id = docente.get("_id")

    # ==========================================
    # CONVERSACIONES DEL DOCENTE
    # ==========================================

    conversaciones = list(
        db.conversaciones.find({
            "docente_id": docente_id
        }).sort(
            "ultima_actualizacion",
            -1
        )
    )

    # ==========================================
    # MENSAJES PENDIENTES
    # ==========================================

    mensajes_pendientes = db.conversaciones.count_documents({
        "docente_id": docente_id,
        "no_leidos_docente": {
            "$gt": 0
        }
    })

    # ==========================================
    # CLASES DEL DOCENTE
    # ==========================================

    clases = list(
        db.asignaturas.find({
            "docente_id": docente_id
        })
    )

    total_asignaturas = len(clases)

    # ==========================================
    # OBTENER ESTUDIANTES
    # SEGÚN GRADO Y SECCIÓN
    # ==========================================

    estudiantes = []

    ids_estudiantes = set()

    for clase in clases:

        grado = clase.get("grado")
        seccion = clase.get("seccion")

        print("====================================")
        print("BUSCANDO ESTUDIANTES")
        print("GRADO:", grado)
        print("SECCIÓN:", seccion)
        print("====================================")

        lista_estudiantes = db.estudiantes.find({

            "grado": grado,

            "seccion": seccion,

            "estado": "activo"

        })

        for estudiante in lista_estudiantes:

            estudiante_id = str(
                estudiante.get("_id")
            )

            if estudiante_id not in ids_estudiantes:

                estudiantes.append(
                    estudiante
                )

                ids_estudiantes.add(
                    estudiante_id
                )

    # ==========================================
    # TOTAL DE ESTUDIANTES
    # ==========================================

    total_estudiantes = len(estudiantes)

    # ==========================================
    # DEPURACIÓN
    # ==========================================

    print("==========================================")
    print("DASHBOARD DOCENTE")
    print("==========================================")

    print(
        "DOCENTE:",
        docente.get("nombre")
    )

    print(
        "USUARIO:",
        usuario
    )

    print(
        "ID DOCENTE:",
        docente_id
    )

    print(
        "TOTAL ASIGNATURAS:",
        total_asignaturas
    )

    print(
        "TOTAL ESTUDIANTES:",
        total_estudiantes
    )

    for estudiante in estudiantes:

        print(
            "ESTUDIANTE:",
            estudiante.get("_id"),
            estudiante.get("nombre"),
            estudiante.get("grado"),
            estudiante.get("seccion")
        )

    print("==========================================")

    # ==========================================
    # ASISTENCIAS
    # ==========================================

    total_asistencias = db.asistencias.count_documents({
        "docente": usuario
    })

    # ==========================================
    # ASISTENCIAS PENDIENTES
    # ==========================================

    pendientes = list(
        db.asistencias.find({
            "docente": usuario
        })
    )

    # ==========================================
    # ESTADÍSTICA
    # ==========================================

    estadistica = {

        "total_asignaturas":
            total_asignaturas,

        "total_estudiantes":
            total_estudiantes,

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
            total_asistencias
    }

    # ==========================================
    # AVISOS
    # ==========================================

    avisos = [

        "Recuerda registrar la asistencia diariamente.",

        "Mantén actualizadas las calificaciones.",

        "Consulta las incidencias de tus estudiantes."

    ]

    # ==========================================
    # CLASES DE HOY
    # ==========================================

    clases_hoy = clases

    # ==========================================
    # RENDER DASHBOARD
    # ==========================================

    return render_template(
    "docente/dashboard_docente.html",

    docente=docente,
    fecha_hoy=datetime.now(),
    estadistica=estadistica,
    pendientes=pendientes,
    avisos=avisos,
    clases_hoy=clases_hoy,
    mensajes_pendientes=mensajes_pendientes,
    conversaciones=conversaciones,

    estudiantes=estudiantes,
    total_estudiantes=total_estudiantes
)


# ==========================================================
# MIS CLASES
# ==========================================================

@docente_bp.route("/mis_clases")
@role_required("docente")
def mis_clases():

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

    clases = list(
        db.asignaciones.aggregate([

            {
                "$match": {
                    "docente_id": docente["_id"]
                }
            },

            {
                "$lookup": {
                    "from": "asignaturas",
                    "localField": "asignatura_id",
                    "foreignField": "_id",
                    "as": "asignatura"
                }
            },

            {
                "$lookup": {
                    "from": "cursos",
                    "localField": "curso_id",
                    "foreignField": "_id",
                    "as": "curso"
                }
            }

        ])
    )

    return render_template(
        "docente/mis_clases.html",
        clases=clases
    )


# ==============================
# DETALLE DE UNA CLASE
# ==============================

@docente_bp.route("/clase/<asignatura_id>")
@role_required("docente")
def detalle_clase(asignatura_id):

    usuario = session.get("usuario")


    docente = db.docentes.find_one({
        "usuario": usuario
    })


    if not docente:
        flash(
            "Docente no encontrado",
            "danger"
        )
        return redirect(url_for("login"))



    asignatura = db.asignaturas.find_one({
        "_id": asignatura_id,
        "docente_id": docente["_id"]
    })


    if not asignatura:

        flash(
            "Asignatura no encontrada",
            "danger"
        )

        return redirect(
            url_for("docente.mis_clases")
        )


    estudiantes = list(
        db.estudiantes.find({
            "grado": asignatura["grado"],
            "seccion": asignatura["seccion"],
            "estado":"activo"
        })
    )

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

    print("🎓 GRADO ASIGNATURA:", grado)
    print("🏫 SECCIÓN ASIGNATURA:", seccion)


    # =====================================
    # CONVERTIR GRADO DE ASIGNATURA
    # AL FORMATO UTILIZADO POR ESTUDIANTES
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
    # FECHA
    # =====================================

    fecha = datetime.now().strftime("%Y-%m-%d")


    # =====================================
    # MOSTRAR ASISTENCIA
    # =====================================

    return render_template(
        "docente/asistencia.html",
        asignatura=asignatura,
        estudiantes=estudiantes,
        fecha=fecha,
        asistencia={}
    )

# =====================================
# GUARDAR ASISTENCIA
# =====================================

@docente_bp.route("/asistencia/guardar", methods=["POST"])
@role_required("docente")
def guardar_asistencia():

    print("========================================")
    print("💾 GUARDANDO ASISTENCIA")
    print("========================================")

    asignatura_id = request.form.get("asignatura_id")
    fecha = request.form.get("fecha")

    if not fecha:
        fecha = datetime.now().strftime("%Y-%m-%d")

    print("📚 ASIGNATURA:", asignatura_id)
    print("📅 FECHA:", fecha)

    asignatura = db.asignaturas.find_one({
        "_id": asignatura_id
    })

    if not asignatura:

        flash(
            "Asignatura no encontrada",
            "danger"
        )

        return redirect(
            url_for("docente.aulas")
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

    grado = asignatura.get("grado")
    seccion = asignatura.get("seccion")

    grado_estudiante = mapa_grados.get(
        str(grado),
        grado
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

    print(
        "👥 ESTUDIANTES A GUARDAR:",
        len(estudiantes)
    )

    # =====================================
    # GUARDAR
    # =====================================

    for estudiante in estudiantes:

        estudiante_id = estudiante.get("_id")

        estado = request.form.get(
            f"estado_{estudiante_id}"
        )

        observacion = request.form.get(
            f"observacion_{estudiante_id}",
            ""
        )

        print(
            "➡️",
            estudiante.get("nombre"),
            "|",
            estado
        )

        db.asistencias.update_one(

            {
                "asignatura_id": asignatura_id,
                "estudiante_id": estudiante_id,
                "fecha": fecha
            },

            {
                "$set": {
                    "asignatura_id": asignatura_id,
                    "estudiante_id": estudiante_id,
                    "fecha": fecha,
                    "estado": estado,
                    "observacion": observacion,
                    "docente": session.get("usuario")
                }
            },

            upsert=True
        )

    flash(
        "Asistencia guardada correctamente",
        "success"
    )

    return redirect(
        url_for(
            "docente.asistencia",
            asignatura_id=asignatura_id
        )
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

# =====================================
# AULAS DEL DOCENTE
# =====================================

@docente_bp.route("/aulas")
@role_required("docente")
def aulas():

    usuario = session.get("usuario")

    docente = db.docentes.find_one({
        "usuario": usuario
    })

    if not docente:
        flash(
            "Docente no encontrado",
            "danger"
        )
        return redirect(url_for("login"))


    clases = list(
        db.asignaturas.find({
            "docente_id": docente["_id"]
        })
    )


    return render_template(
        "docente/aulas.html",
        clases=clases
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
    # ID DEL DOCENTE
    # =====================================

    docente_id = docente.get("_id")

    print("=====================================")
    print("PRUEBA DOCENTE ACTUAL")
    print("USUARIO:", usuario)
    print("DOCENTE ID:", docente_id)
    print("DOCENTE NOMBRE:", docente.get("nombre"))
    print("=====================================")

    # =====================================
    # BUSCAR CLASES DEL DOCENTE
    # =====================================

    clases = list(
        db.asignaturas.find({
            "docente_id": docente_id
        })
    )

    print(
        "CLASES ENCONTRADAS:",
        len(clases)
    )

    # =====================================
    # LISTA DE ESTUDIANTES
    # =====================================

    estudiantes = []

    ids_estudiantes = set()

    # =====================================
    # OBTENER ESTUDIANTES DE LAS CLASES
    # DEL DOCENTE
    # =====================================

    estudiantes = []

    ids_estudiantes = set()

    # =====================================
    # CONVERSIÓN DE GRADOS
    # =====================================

    mapa_grados = {
        "1": "1er Grado",
        "2": "2do Grado",
        "3": "3er Grado",
        "4": "4to Grado",
        "5": "5to Grado",
        "6": "6to Grado"
    }

    # =====================================
    # RECORRER CLASES DEL DOCENTE
    # =====================================

    for clase in clases:

        grado = str(
            clase.get("grado", "")
        ).strip()

        seccion = str(
            clase.get("seccion", "")
        ).strip()

        grado_busqueda = mapa_grados.get(
            grado,
            grado
        )

        print("=====================================")
        print("BUSCANDO ESTUDIANTES")
        print(
            "GRADO ASIGNATURA:",
            grado
        )
        print(
            "GRADO ESTUDIANTE:",
            grado_busqueda
        )
        print(
            "SECCIÓN:",
            seccion
        )
        print("=====================================")

        # =====================================
        # BUSCAR ESTUDIANTES
        # =====================================

        lista_estudiantes = db.estudiantes.find({

            "grado": grado_busqueda,

            "seccion": seccion,

            "estado": "activo"

        })

        encontrados = 0

        for estudiante in lista_estudiantes:

            encontrados += 1

            estudiante_id = str(
                estudiante.get("_id")
            )

            # =================================
            # EVITAR DUPLICADOS
            # =================================

            if estudiante_id not in ids_estudiantes:

                estudiantes.append(
                    estudiante
                )

                ids_estudiantes.add(
                    estudiante_id
                )

                print(
                    "ESTUDIANTE ENCONTRADO:",
                    estudiante.get("nombre")
                )

        print(
            "TOTAL ENCONTRADOS:",
            encontrados
        )

    # =====================================
    # TOTAL DE ESTUDIANTES
    # =====================================

    total_estudiantes = len(
        estudiantes
    )

    print("=====================================")
    print(
        "TOTAL ESTUDIANTES:",
        total_estudiantes
    )
    print("=====================================")


    # =====================================
    # MOSTRAR ESTUDIANTES
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
            estudiante.get("seccion")
        )

    print("=====================================")


    # =====================================
    # BUSCAR ESTUDIANTES
    # =====================================

    for clase in clases:

        grado = clase.get("grado")
        seccion = clase.get("seccion")

        print("=====================================")
        print("BUSCANDO ESTUDIANTES")
        print("GRADO:", repr(grado))
        print("SECCIÓN:", repr(seccion))
        print("=====================================")

        lista_estudiantes = db.estudiantes.find({
            "grado": grado,
            "seccion": seccion,
            "estado": "activo"
        })

        encontrados = 0

        for estudiante in lista_estudiantes:

            encontrados += 1

            estudiante_id = str(
                estudiante.get("_id")
            )

            if estudiante_id not in ids_estudiantes:

                estudiantes.append(
                    estudiante
                )

                ids_estudiantes.add(
                    estudiante_id
                )

                print(
                    "ESTUDIANTE ENCONTRADO:",
                    estudiante.get("nombre")
                )

        print(
            "TOTAL ENCONTRADOS:",
            encontrados
        )

    # =====================================
    # TOTAL ESTUDIANTES
    # =====================================

    total_estudiantes = len(
        estudiantes
    )

    print("=====================================")
    print(
        "TOTAL ESTUDIANTES:",
        total_estudiantes
    )
    print("=====================================")

    # =====================================
    # MOSTRAR ESTUDIANTES
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
            estudiante.get("seccion")
        )

    print("=====================================")

    # =====================================
    # RENDERIZAR PÁGINA
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

    print(
        "👨‍🏫 DOCENTE:",
        docente.get("_id")
    )


    # =====================================
    # BUSCAR CLASES DEL DOCENTE
    # =====================================

    clases = list(
        db.asignaturas.find({
            "docente_id": docente.get("_id"),
            "activo": True
        })
    )


    print(
        "📚 TOTAL DE CLASES:",
        len(clases)
    )


    # =====================================
    # MOSTRAR CLASES
    # =====================================

    return render_template(
        "docente/seleccionar_incidencias.html",
        clases=clases
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


    estudiante_id = request.form.get(
        "estudiante_id"
    )

    tipo = request.form.get(
        "tipo"
    )

    descripcion = request.form.get(
        "descripcion"
    )

    fecha = request.form.get(
        "fecha"
    )


    print(
        "👤 ESTUDIANTE:",
        estudiante_id
    )

    print(
        "⚠️ TIPO:",
        tipo
    )

    print(
        "📅 FECHA:",
        fecha
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
                "docente.lista_incidencias"
            )
        )


    # =====================================
    # CREAR INCIDENCIA
    # =====================================

    incidencia = {

        "estudiante_id":
            estudiante_id,

        "docente":
            session.get("usuario"),

        "tipo":
            tipo,

        "descripcion":
            descripcion,

        "fecha":
            fecha

    }


    # =====================================
    # GUARDAR EN MONGODB
    # =====================================

    db.incidencias.insert_one(
        incidencia
    )


    print(
        "✅ INCIDENCIA GUARDADA"
    )


    flash(
        "Incidencia registrada correctamente.",
        "success"
    )


    return redirect(
        url_for(
            "docente.lista_incidencias"
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

    usuario = session.get("usuario")


    docente = db.docentes.find_one({
        "usuario": usuario
    })


    estudiantes = list(
        db.estudiantes.find({
            "estado":"activo"
        })
    )


    return render_template(
        "docente/comunicacion.html",
        estudiantes=estudiantes,
        docente=docente
    )

# =====================================
# COMUNICACIÓN POR ESTUDIANTE
# =====================================
@docente_bp.route("/comunicacion/guardar", methods=["POST"])
@role_required("docente")
def guardar_comunicacion():


    db.comunicaciones.insert_one({

        "de":
            session.get("usuario"),


        "para":
            request.form.get("padre"),


        "mensaje":
            request.form.get("mensaje"),


        "fecha":
            datetime.now().strftime("%Y-%m-%d")

    })


    flash(
        "Mensaje enviado correctamente",
        "success"
    )


    return redirect(
        url_for(
            "docente.comunicacion"
        )
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


# ==========================================
# BOLETÍN DEL ESTUDIANTE
# ==========================================

@docente_bp.route("/boletin-estudiante/<estudiante_id>")
@role_required("docente")
def boletin_estudiante(estudiante_id):

    # ==========================================
    # BUSCAR ESTUDIANTE
    # ==========================================

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

    # ==========================================
    # BUSCAR NOTAS
    # ==========================================

    notas = list(
        db.notas.find({
            "estudiante_id": estudiante_id
        })
    )

    # ==========================================
    # CONSTRUIR BOLETÍN
    # ==========================================

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
                or asignatura_id
            )

        else:

            nombre_asignatura = (
                asignatura_id
                or "Sin asignatura"
            )

        boletin.append({

            "asignatura": nombre_asignatura,

            "corte1": nota.get("corte1"),

            "corte2": nota.get("corte2"),

            "corte3": nota.get("corte3"),

            "corte4": nota.get("corte4"),

            "promedio": nota.get("promedio"),

            "estado": nota.get("estado")
        })

    # ==========================================
    # PROMEDIO GENERAL
    # ==========================================

    promedios = [

        b["promedio"]

        for b in boletin

        if b["promedio"] is not None
    ]

    if promedios:

        promedio_general = round(
            sum(promedios) / len(promedios),
            2
        )

    else:

        promedio_general = None

    # ==========================================
    # DEBUG
    # ==========================================

    print("====================================")
    print("BOLETÍN DOCENTE")
    print(
        "ESTUDIANTE:",
        estudiante.get("nombre")
    )
    print(
        "ESTUDIANTE ID:",
        estudiante_id
    )
    print(
        "BOLETÍN:",
        boletin
    )
    print(
        "PROMEDIO GENERAL:",
        promedio_general
    )
    print("====================================")

    # ==========================================
    # MOSTRAR BOLETÍN
    # ==========================================

    return render_template(
        "docente/boletin_estudiante.html",

        estudiante=estudiante,

        boletin=boletin,

        promedio_general=promedio_general
    )


# ==========================================================
# GENERAR PDF DEL BOLETÍN DEL ESTUDIANTE - DOCENTE
# ==========================================================

@docente_bp.route(
    "/boletin-pdf-estudiante/<estudiante_id>"
)
@role_required("docente")
def boletin_pdf_estudiante(estudiante_id):

    # ==========================================
    # BUSCAR ESTUDIANTE
    # ==========================================

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

    # ==========================================
    # BUSCAR NOTAS
    # ==========================================

    notas = list(
        db.notas.find({
            "estudiante_id": estudiante_id
        })
    )

    # ==========================================
    # CONSTRUIR BOLETÍN
    # ==========================================

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
                or asignatura_id
            )

        else:

            nombre_asignatura = (
                asignatura_id
                or "Sin asignatura"
            )

        boletin.append({

            "asignatura": nombre_asignatura,

            "corte1": nota.get("corte1"),

            "corte2": nota.get("corte2"),

            "corte3": nota.get("corte3"),

            "corte4": nota.get("corte4"),

            "promedio": nota.get("promedio"),

            "estado": nota.get("estado")
        })

    # ==========================================
    # PROMEDIO GENERAL
    # ==========================================

    promedios = [

        b["promedio"]

        for b in boletin

        if b["promedio"] is not None
    ]

    if promedios:

        promedio_general = round(
            sum(promedios) / len(promedios),
            2
        )

    else:

        promedio_general = None

    # ==========================================
    # CREAR PDF
    # ==========================================

    buffer = BytesIO()

    documento = SimpleDocTemplate(

        buffer,

        pagesize=letter,

        rightMargin=35,
        leftMargin=35,
        topMargin=35,
        bottomMargin=35
    )

    estilos = getSampleStyleSheet()

    titulo = estilos["Title"]
    titulo.alignment = TA_CENTER

    subtitulo = estilos["Heading2"]
    subtitulo.alignment = TA_CENTER

    normal = estilos["Normal"]

    elementos = []

    # ==========================================
    # ENCABEZADO INSTITUCIONAL
    # ==========================================

    logo_path = os.path.join(

        current_app.root_path,

        "static",

        "img",

        "logo.jpg"
    )

    if os.path.exists(logo_path):

        logo = Image(

            logo_path,

            width=70,

            height=70
        )

        logo.hAlign = "CENTER"

        elementos.append(
            logo
        )

        elementos.append(
            Spacer(1, 8)
        )

    elementos.append(
        Paragraph(
            "COLEGIO INTEGRAL EMANUEL",
            titulo
        )
    )

    elementos.append(
        Paragraph(
            "CIEM ONE",
            subtitulo
        )
    )

    estilo_centro = estilos["Normal"]
    estilo_centro.alignment = TA_CENTER

    elementos.append(
        Paragraph(
            "Formación Integral para una Educación de Excelencia",
            estilo_centro
        )
    )

    elementos.append(
        Paragraph(
            "Matagalpa, Nicaragua",
            normal
        )
    )

    elementos.append(
        Spacer(1, 10)
    )

    elementos.append(
        Paragraph(
            "BOLETÍN ACADÉMICO",
            subtitulo
        )
    )

    elementos.append(
        Spacer(1, 15)
    )

    # ==========================================
    # DATOS DEL ESTUDIANTE
    # ==========================================

    datos_estudiante = [

        [
            "Estudiante",
            estudiante.get(
                "nombre",
                "No disponible"
            )
        ],

        [
            "Grado",
            estudiante.get(
                "grado",
                "No disponible"
            )
        ],

        [
            "Sección",
            estudiante.get(
                "seccion",
                "No disponible"
            )
        ],

        [
            "Año lectivo",
            "2026"
        ]
    ]

    tabla_datos = Table(

        datos_estudiante,

        colWidths=[
            120,
            350
        ]
    )

    tabla_datos.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.HexColor(
                    "#08142C"
                )
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (0, -1),
                colors.white
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, -1),
                "Helvetica"
            ),

            (
                "FONTNAME",
                (0, 0),
                (0, -1),
                "Helvetica-Bold"
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "PADDING",
                (0, 0),
                (-1, -1),
                8
            )
        ])
    )

    elementos.append(
        tabla_datos
    )

    elementos.append(
        Spacer(1, 20)
    )

    # ==========================================
    # TABLA DE NOTAS
    # ==========================================

    encabezados = [

        "Asignatura",
        "I Corte",
        "II Corte",
        "III Corte",
        "IV Corte",
        "Promedio",
        "Estado"
    ]

    filas = [
        encabezados
    ]

    for item in boletin:

        promedio = item.get(
            "promedio"
        )

        if promedio is not None:

            estado = (

                "Aprobado"

                if promedio >= 60

                else "Reforzamiento"
            )

        else:

            estado = "Pendiente"

        filas.append([

            item["asignatura"],

            item["corte1"]
            if item["corte1"] is not None
            else "—",

            item["corte2"]
            if item["corte2"] is not None
            else "—",

            item["corte3"]
            if item["corte3"] is not None
            else "—",

            item["corte4"]
            if item["corte4"] is not None
            else "—",

            promedio
            if promedio is not None
            else "—",

            estado
        ])

    if not boletin:

        filas.append([

            "Sin asignatura",

            "—",

            "—",

            "—",

            "—",

            "—",

            "Pendiente"
        ])

    tabla_notas = Table(

        filas,

        repeatRows=1
    )

    tabla_notas.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor(
                    "#08142C"
                )
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
                (1, 0),
                (-1, -1),
                "CENTER"
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "PADDING",
                (0, 0),
                (-1, -1),
                7
            )
        ])
    )

    elementos.append(
        tabla_notas
    )

    elementos.append(
        Spacer(1, 20)
    )

    # ==========================================
    # RESUMEN
    # ==========================================

    promedio_texto = (

        str(promedio_general)

        if promedio_general is not None

        else "—"
    )

    if promedio_general is None:

        estado_general = "Pendiente"

    elif promedio_general >= 60:

        estado_general = "Aprobado"

    else:

        estado_general = "Reforzamiento"

    resumen = [

        [
            "Promedio general",
            promedio_texto
        ],

        [
            "Asignaturas",
            str(len(boletin))
        ],

        [
            "Estado académico",
            estado_general
        ]
    ]

    tabla_resumen = Table(

        resumen,

        colWidths=[
            180,
            150
        ]
    )

    tabla_resumen.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.HexColor(
                    "#EAF1FA"
                )
            ),

            (
                "FONTNAME",
                (0, 0),
                (0, -1),
                "Helvetica-Bold"
            ),

            (
                "ALIGN",
                (1, 0),
                (1, -1),
                "CENTER"
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "PADDING",
                (0, 0),
                (-1, -1),
                8
            )
        ])
    )

    elementos.append(
        tabla_resumen
    )

    elementos.append(
        Spacer(1, 30)
    )

    # ==========================================
    # FIRMAS
    # ==========================================

    firmas = Table(

        [

            [
                "________________________",
                "________________________"
            ],

            [
                "Docente / Tutor",
                "Dirección Académica"
            ]

        ],

        colWidths=[
            220,
            220
        ]
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

    elementos.append(
        firmas
    )

    # ==========================================
    # GENERAR PDF
    # ==========================================

    documento.build(
        elementos
    )

    buffer.seek(0)

    # ==========================================
    # DESCARGAR PDF
    # ==========================================

    nombre_estudiante = (

        estudiante.get(
            "nombre",
            "estudiante"
        )
        .replace(
            " ",
            "_"
        )
    )

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