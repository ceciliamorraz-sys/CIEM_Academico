from flask import (
    Blueprint,
    render_template,
    session,
    request,
    flash,
    redirect,
    url_for,
    send_file
)

from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER

from config.database import db
from utils.decorators import role_required


# ==================================================
# DOCENTE ACTUAL DE UNA NOTA (no el histórico)
# ==================================================
#
# nota.docente / nota.docente_nombre reflejan quién
# registró esa nota en su momento. Si la materia se
# reasignó a otro docente después, eso queda viejo.
# Esta función busca quién da la materia ACTUALMENTE
# (asignación activa) para mostrar el nombre correcto
# en el dashboard del estudiante.

def _docente_actual_para_nota(nota):

    asignacion_actual = db.asignaciones_clase.find_one({
        "asignatura_nombre": nota.get("asignatura_nombre"),
        "grado": nota.get("grado"),
        "seccion": nota.get("seccion"),
        "activo": True
    })

    if not asignacion_actual:
        return (
            nota.get("docente_nombre")
            or nota.get("docente")
            or "No registrado"
        )

    docente_id = asignacion_actual.get("docente_id", "")

    codigo_limpio = docente_id.replace("DOC", "").strip()

    posibles_codigos = list(dict.fromkeys([
        docente_id,
        codigo_limpio,
        "DOC" + codigo_limpio
    ]))

    docente = db.docentes.find_one({
        "codigo": {"$in": posibles_codigos}
    })

    if docente and docente.get("nombre"):
        return docente["nombre"]

    return (
        nota.get("docente_nombre")
        or nota.get("docente")
        or "No registrado"
    )


# ==========================================================
# BLUEPRINT
# ==========================================================


estudiante_bp = Blueprint(
    "estudiante",
    __name__,
    url_prefix="/estudiante"
)


# ==========================================================
# BUSCAR ESTUDIANTE ASOCIADO A LA SESIÓN
# ==========================================================

def obtener_estudiante_sesion():

    rol = session.get("rol")
    usuario = session.get("usuario")


    estudiante = None

    # ======================================================
    # ESTUDIANTE
    # ======================================================

    if rol == "estudiante":


        estudiante = db.estudiantes.find_one({
            "usuario": usuario,
            "estado": "activo"
        })

    # ======================================================
    # PADRE
    # ======================================================

    elif rol == "padre":


        # --------------------------------------------------
        # BUSCAR ESTUDIANTE POR USUARIO DE LA MADRE
        # --------------------------------------------------

        estudiante = db.estudiantes.find_one({
            "madre_usuario": usuario,
            "estado": "activo"
        })

    # ======================================================
    # RESULTADO
    #
    # El return va fuera del if/elif para que aplique tanto
    # al caso "estudiante" como al caso "padre". Antes solo
    # estaba dentro del elif, así que cuando rol == "estudiante"
    # la función siempre devolvía None aunque sí encontrara
    # el documento en Mongo.
    # ======================================================

    return estudiante
# ==========================================================
# CONFIGURACIÓN
# ==========================================================

@estudiante_bp.route("/configuracion")
@role_required("estudiante", "padre")
def configuracion():

    rol = session.get("rol")
    usuario = session.get("usuario")

    estudiante = obtener_estudiante_sesion()

    usuario_db = db.usuarios.find_one({
        "usuario": usuario
    })

    return render_template(
        "estudiante/configuracion_estudiante.html",
        estudiante=estudiante,
        rol=rol,
        usuario=usuario_db
    )


# ==========================================================
# CAMBIAR CORREO
# ==========================================================

@estudiante_bp.route(
    "/cambiar-correo",
    methods=["POST"]
)
@role_required("estudiante", "padre")
def cambiar_correo():

    usuario = session.get("usuario")

    nuevo_correo = request.form.get(
        "correo",
        ""
    ).strip().lower()


    # ======================================================
    # VALIDAR CORREO
    # ======================================================

    if not nuevo_correo:

        flash(
            "Debe ingresar un correo electrónico.",
            "danger"
        )

        return redirect(
            url_for("estudiante.configuracion")
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
            url_for("estudiante.configuracion")
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


    # ======================================================
    # MENSAJE
    # ======================================================

    if resultado.modified_count > 0:

        flash(
            "Correo actualizado correctamente.",
            "success"
        )

    else:

        flash(
            "El correo ya tenía ese mismo valor.",
            "info"
        )

    return redirect(
        url_for("estudiante.configuracion")
    )

# ==========================================================
# CAMBIAR CONTRASEÑA
# ==========================================================

@estudiante_bp.route(
    "/cambiar-password",
    methods=["POST"]
)
@role_required("estudiante", "padre")
def cambiar_password():

    usuario = session.get("usuario")


    if not usuario:

        flash(
            "No se pudo identificar el usuario.",
            "danger"
        )

        return redirect(
            url_for("estudiante.configuracion")
        )

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

    if not password_actual:

        flash(
            "Debe ingresar su contraseña actual.",
            "danger"
        )

        return redirect(
            url_for("estudiante.configuracion")
        )

    if not password_nueva:

        flash(
            "Debe ingresar una nueva contraseña.",
            "danger"
        )

        return redirect(
            url_for("estudiante.configuracion")
        )

    if not password_confirmar:

        flash(
            "Debe confirmar la nueva contraseña.",
            "danger"
        )

        return redirect(
            url_for("estudiante.configuracion")
        )

    if password_nueva != password_confirmar:

        flash(
            "Las nuevas contraseñas no coinciden.",
            "danger"
        )

        return redirect(
            url_for("estudiante.configuracion")
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
            url_for("estudiante.configuracion")
        )

    # ======================================================
    # VERIFICAR CONTRASEÑA ACTUAL
    # ======================================================

    password_bd = str(
        usuario_db.get("password", "")
    ).strip()

    if password_bd != password_actual:

        flash(
            "La contraseña actual es incorrecta.",
            "danger"
        )

        return redirect(
            url_for("estudiante.configuracion")
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


    if resultado.modified_count > 0:

        flash(
            "Contraseña actualizada correctamente.",
            "success"
        )

    else:

        flash(
            "La contraseña ya tenía ese mismo valor.",
            "info"
        )

    return redirect(
        url_for("estudiante.configuracion")
    )

# ==========================================================
# DASHBOARD ESTUDIANTE / PADRE
# ==========================================================

@estudiante_bp.route("/")
@role_required("estudiante", "padre")
def dashboard():

    rol = session.get("rol")
    usuario = session.get("usuario")


    estudiante = obtener_estudiante_sesion()

    notas = []
    docentes = []
    mensajes = []
    conversaciones_padre = []
    avisos = []

    # ======================================================
    # CARGAR DOCENTES
    # ======================================================


    try:

        docentes = list(
            db.docentes.find()
        )


        for docente in docentes:

            pass

    except Exception as e:


        docentes = []


    # ======================================================
    # SI SE ENCONTRÓ ESTUDIANTE
    # ======================================================

    if estudiante:

        estudiante_id = str(
            estudiante.get("_id")
        )


        # ==================================================
        # OBTENER NOTAS
        # ==================================================

        notas = list(
            db.notas.find({
                "estudiante_id": estudiante_id
            })
        )

        for nota in notas:
            nota["docente_actual_nombre"] = (
                _docente_actual_para_nota(nota)
            )


        # ==================================================
        # CONVERSACIONES (PADRE O ESTUDIANTE)
        # ==================================================

        if rol in ("padre", "estudiante"):

            conversaciones_padre = list(
                db.conversaciones.find({
                    "estudiante_id": estudiante_id
                }).sort(
                    "ultima_actualizacion",
                    -1
                )
            )

            # ----------------------------------------------
            # CONTADOR DE MENSAJES SIN LEER
            # ----------------------------------------------

            mensajes = [
                c for c in conversaciones_padre
                if c.get("no_leidos_padre", 0) > 0
            ]

    else:

        pass

    # ======================================================
    # AVISOS INSTITUCIONALES
    # ======================================================

    usuario_actual = session.get("usuario")


    todos_avisos_padres = list(
        db.avisos_padres.find()
    )


    for aviso in todos_avisos_padres:

        pass


   # ======================================================
    # BUSCAR AVISOS INSTITUCIONALES
    # ======================================================

    avisos = list(
        db.comunicaciones.find({
            "estado": "publicado"
        }).sort(
            "fecha_creacion",
            -1
        ).limit(10)
    )

    # ======================================================
    # ADAPTAR AVISOS PARA EL DASHBOARD
    # ======================================================

    for aviso in avisos:

        aviso["contenido"] = aviso.get(
            "mensaje",
            ""
        )
    # ======================================================
    # DEBUG AVISOS
    # ======================================================


    for aviso in avisos:

        pass


    # ======================================================
    # MOSTRAR DASHBOARD
    # ======================================================

    return render_template(
        "estudiante/estudiante_dashboard.html",
        estudiante=estudiante,
        notas=notas,
        docentes=docentes,
        mensajes=mensajes,
        conversaciones=conversaciones_padre,
        avisos=avisos
    )

    # ==========================================================
# RENDIMIENTO ACADÉMICO
# ==========================================================

@estudiante_bp.route("/rendimiento")
@role_required("estudiante", "padre")
def rendimiento():

    estudiante = obtener_estudiante_sesion()

    # ======================================================
    # VERIFICAR ESTUDIANTE
    # ======================================================

    if not estudiante:

        flash(
            "No se encontró el estudiante asociado.",
            "danger"
        )

        return redirect(
            url_for("estudiante.dashboard")
        )

    # ======================================================
    # ID DEL ESTUDIANTE
    # ======================================================

    estudiante_id = str(
        estudiante.get("_id")
    )

    # ======================================================
    # OBTENER NOTAS
    # ======================================================

    notas = list(
        db.notas.find({
            "estudiante_id": estudiante_id
        })
    )

    # ======================================================
    # OBTENER ASIGNATURAS
    # ======================================================

    asignaturas = list(
        db.asignaturas.find()
    )

    # ======================================================
    # MAPA DE ASIGNATURAS
    # ======================================================

    mapa_asignaturas = {}

    for asignatura in asignaturas:

        asignatura_id = str(
            asignatura.get("_id")
        )

        mapa_asignaturas[
            asignatura_id
        ] = asignatura

    # ======================================================
    # ESTRUCTURA DEL RENDIMIENTO
    # ======================================================

    rendimiento = {}

    for nota in notas:

        asignatura_id = str(
            nota.get("asignatura_id")
        )

        asignatura = mapa_asignaturas.get(
            asignatura_id,
            {}
        )

        nombre_asignatura = (
            asignatura.get("nombre")
            or asignatura.get("asignatura")
            or nota.get("asignatura_nombre")
            or "Asignatura"
        )

        if asignatura_id not in rendimiento:

            rendimiento[asignatura_id] = {

                "asignatura_id": asignatura_id,

                "asignatura": nombre_asignatura,

                "corte1": None,

                "corte2": None,

                "corte3": None,

                "corte4": None,

                "promedio": None
            }

        # ==================================================
        # DETERMINAR CORTE
        # ==================================================

        periodo = nota.get("periodo")
        evaluacion = nota.get("evaluacion")

        corte = None

        if (
            periodo == "I Semestre"
            and evaluacion == "Primer Parcial"
        ):

            corte = "corte1"

        elif (
            periodo == "I Semestre"
            and evaluacion == "Segundo Parcial"
        ):

            corte = "corte2"

        elif (
            periodo == "II Semestre"
            and evaluacion == "Tercer Parcial"
        ):

            corte = "corte3"

        elif (
            periodo == "II Semestre"
            and evaluacion == "Cuarto Parcial"
        ):

            corte = "corte4"

        # ==================================================
        # GUARDAR NOTA
        # ==================================================

        if corte:

            valor = nota.get(
                "nota",
                nota.get("promedio")
            )

            try:

                valor = float(valor)

            except (
                ValueError,
                TypeError
            ):

                valor = None

            rendimiento[
                asignatura_id
            ][corte] = valor

    # ======================================================
    # CALCULAR PROMEDIOS
    # ======================================================

    for datos in rendimiento.values():

        valores = []

        for campo in [
            "corte1",
            "corte2",
            "corte3",
            "corte4"
        ]:

            valor = datos.get(campo)

            if valor is not None:

                try:

                    valores.append(
                        float(valor)
                    )

                except (
                    ValueError,
                    TypeError
                ):

                    pass

        if valores:

            datos["promedio"] = round(
                sum(valores) / len(valores),
                2
            )

    # ======================================================
    # CONVERTIR A LISTA
    # ======================================================

    rendimiento = list(
        rendimiento.values()
    )

    # ======================================================
    # PROMEDIO GENERAL
    # ======================================================

    promedios = [

        item["promedio"]

        for item in rendimiento

        if item["promedio"] is not None
    ]

    promedio_general = None

    if promedios:

        promedio_general = round(
            sum(promedios) / len(promedios),
            2
        )

    # ======================================================
    # APROBADAS
    # ======================================================

    aprobadas = 0

    for item in rendimiento:

        if (
            item["promedio"] is not None
            and item["promedio"] >= 60
        ):

            aprobadas += 1

    # ======================================================
    # REFORZAMIENTO
    # ======================================================

    reforzamiento = 0

    for item in rendimiento:

        if (
            item["promedio"] is not None
            and item["promedio"] < 60
        ):

            reforzamiento += 1

    # ======================================================
    # MEJOR ASIGNATURA
    # ======================================================

    mejor_asignatura = None

    evaluadas = [

        item

        for item in rendimiento

        if item["promedio"] is not None
    ]

    if evaluadas:

        mejor_asignatura = max(
            evaluadas,
            key=lambda x: x["promedio"]
        )

    # ======================================================
    # MOSTRAR RENDIMIENTO
    # ======================================================

    return render_template(
        "estudiante/rendimiento.html",
        estudiante=estudiante,
        rendimiento=rendimiento,
        promedio_general=promedio_general,
        aprobadas=aprobadas,
        reforzamiento=reforzamiento,
        mejor_asignatura=mejor_asignatura
    )


# ==========================================================
# PERFIL DEL ESTUDIANTE
# ==========================================================

@estudiante_bp.route("/perfil")
@role_required("estudiante", "padre")
def perfil():

    estudiante = obtener_estudiante_sesion()

    # ======================================================
    # VERIFICAR
    # ======================================================

    if not estudiante:

        flash(
            "No se encontró la información del estudiante.",
            "warning"
        )

        return redirect(
            url_for("estudiante.dashboard")
        )

    # ======================================================
    # USUARIO DE LA CUENTA
    # ======================================================

    usuario = session.get("usuario")

    usuario_db = db.usuarios.find_one({
        "usuario": usuario
    })

    # ======================================================
    # MOSTRAR PERFIL
    # ======================================================

    return render_template(
        "estudiante/perfil.html",
        estudiante=estudiante,
        usuario=usuario_db
    )


# ==========================================================
# GENERAR BOLETÍN PDF
# ==========================================================

def _construir_datos_boletin(estudiante):

    # ======================================================
    # ID ESTUDIANTE
    # ======================================================

    estudiante_id = str(
        estudiante.get("_id")
    )

    # ======================================================
    # OBTENER NOTAS
    # ======================================================

    notas = list(
        db.notas.find({
            "estudiante_id": estudiante_id
        })
    )

    # ======================================================
    # OBTENER ASIGNATURAS
    # ======================================================

    asignaturas = list(
        db.asignaturas.find()
    )

    mapa_asignaturas = {}

    for asignatura in asignaturas:

        mapa_asignaturas[
            str(asignatura.get("_id"))
        ] = asignatura

    # ======================================================
    # CONSTRUIR BOLETÍN
    # ======================================================

    boletin = {}

    for nota in notas:

        asignatura_id = str(
            nota.get("asignatura_id")
        )

        if asignatura_id not in boletin:

            asignatura = mapa_asignaturas.get(
                asignatura_id,
                {}
            )

            nombre = (
                asignatura.get("nombre")
                or asignatura.get("asignatura")
                or nota.get("asignatura_nombre")
                or "Asignatura"
            )

            boletin[asignatura_id] = {

                "asignatura": nombre,

                "corte1": None,

                "corte2": None,

                "corte3": None,

                "corte4": None,

                "promedio": None
            }

        # ==================================================
        # DETERMINAR CORTE
        # ==================================================

        periodo = nota.get("periodo")
        evaluacion = nota.get("evaluacion")

        corte = None

        if (
            periodo == "I Semestre"
            and evaluacion == "Primer Parcial"
        ):

            corte = "corte1"

        elif (
            periodo == "I Semestre"
            and evaluacion == "Segundo Parcial"
        ):

            corte = "corte2"

        elif (
            periodo == "II Semestre"
            and evaluacion == "Tercer Parcial"
        ):

            corte = "corte3"

        elif (
            periodo == "II Semestre"
            and evaluacion == "Cuarto Parcial"
        ):

            corte = "corte4"

        # ==================================================
        # GUARDAR NOTA
        # ==================================================

        if corte:

            valor = nota.get(
                "nota",
                nota.get("promedio")
            )

            try:

                valor = float(valor)

            except (
                ValueError,
                TypeError
            ):

                valor = None

            boletin[
                asignatura_id
            ][corte] = valor

    # ======================================================
    # CALCULAR PROMEDIOS
    # ======================================================

    for datos in boletin.values():

        valores = []

        for campo in [
            "corte1",
            "corte2",
            "corte3",
            "corte4"
        ]:

            valor = datos.get(campo)

            if valor is not None:

                try:

                    valores.append(
                        float(valor)
                    )

                except (
                    ValueError,
                    TypeError
                ):

                    pass

        if valores:

            datos["promedio"] = round(
                sum(valores) / len(valores),
                2
            )

    # ======================================================
    # CONVERTIR A LISTA
    # ======================================================

    boletin = list(
        boletin.values()
    )

    # ======================================================
    # PROMEDIO GENERAL
    # ======================================================

    promedios = [

        item["promedio"]

        for item in boletin

        if item["promedio"] is not None
    ]

    promedio_general = None

    if promedios:

        promedio_general = round(
            sum(promedios) / len(promedios),
            2
        )

    # ======================================================
    # OBSERVACIÓN
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

    return notas, boletin, promedio_general, observacion


# ==========================================================
# VISTA PREVIA DEL BOLETÍN (EN NAVEGADOR, SIN DESCARGAR)
# ==========================================================

@estudiante_bp.route("/boletin")
@role_required("estudiante", "padre")
def boletin_preview():

    estudiante = obtener_estudiante_sesion()

    if not estudiante:

        flash(
            "No se encontró el estudiante asociado.",
            "danger"
        )

        return redirect(
            url_for("estudiante.dashboard")
        )

    notas, boletin, promedio_general, observacion = (
        _construir_datos_boletin(estudiante)
    )

    return render_template(

        "boletin.html",

        estudiante=estudiante,

        notas=notas,

        boletin=boletin,

        promedio_general=promedio_general,

        observacion=observacion,

        fecha_emision=datetime.now().strftime("%d/%m/%Y"),

        modo_preview=True
    )


@estudiante_bp.route("/boletin/pdf")
@role_required("estudiante", "padre")
def boletin_pdf():

    # ======================================================
    # OBTENER ESTUDIANTE
    # ======================================================

    estudiante = obtener_estudiante_sesion()

    if not estudiante:

        flash(
            "No se encontró el estudiante asociado.",
            "danger"
        )

        return redirect(
            url_for("estudiante.dashboard")
        )

    notas, boletin, promedio_general, observacion = (
        _construir_datos_boletin(estudiante)
    )

    # ======================================================
    # GENERAR HTML
    # ======================================================

    html_boletin = render_template(

        "boletin.html",

        estudiante=estudiante,

        notas=notas,

        boletin=boletin,

        promedio_general=promedio_general,

        observacion=observacion,

        fecha_emision=datetime.now().strftime("%d/%m/%Y"),

        modo_preview=False
    )

    # ======================================================
    # WEASYPRINT
    # ======================================================

    from weasyprint import HTML

    pdf_bytes = HTML(

        string=html_boletin,

        base_url=request.url_root

    ).write_pdf()

    # ======================================================
    # BUFFER
    # ======================================================

    buffer = BytesIO(
        pdf_bytes
    )

    # ======================================================
    # NOMBRE DEL ARCHIVO
    # ======================================================

    nombre_estudiante = str(

        estudiante.get(
            "nombre",
            "estudiante"
        )
    )

    nombre_estudiante = (

        nombre_estudiante

        .replace(
            " ",
            "_"
        )

        .replace(
            "/",
            "_"
        )

        .replace(
            "\\",
            "_"
        )
    )

    # ======================================================
    # DESCARGAR
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