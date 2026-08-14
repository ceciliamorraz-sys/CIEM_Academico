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

    print("====================================")
    print("🔎 BUSCANDO ESTUDIANTE")
    print("ROL:", rol)
    print("USUARIO SESIÓN:", usuario)
    print("====================================")

    estudiante = None

    # ======================================================
    # ESTUDIANTE
    # ======================================================

    if rol == "estudiante":

        print("👨‍🎓 BUSCANDO ESTUDIANTE POR USUARIO")

        estudiante = db.estudiantes.find_one({
            "usuario": usuario,
            "estado": "activo"
        })

    # ======================================================
    # PADRE
    # ======================================================

    elif rol == "padre":

        print("👩‍👧 BUSCANDO HIJO DEL PADRE")
        print("USUARIO PADRE:", usuario)

        # --------------------------------------------------
        # PRIMERA OPCIÓN:
        # madre_usuario = alma
        # --------------------------------------------------

        estudiante = db.estudiantes.find_one({
            "madre_usuario": usuario,
            "estado": "activo"
        })

        print("------------------------------------")
        print("BÚSQUEDA POR madre_usuario")
        print("RESULTADO:", estudiante)

        # --------------------------------------------------
        # SEGUNDA OPCIÓN:
        # tutor_usuario
        # --------------------------------------------------

        if not estudiante:

            print("------------------------------------")
            print("⚠️ NO SE ENCONTRÓ POR madre_usuario")
            print("BUSCANDO POR tutor_usuario")

            estudiante = db.estudiantes.find_one({
                "tutor_usuario": usuario,
                "estado": "activo"
            })

            print("RESULTADO tutor_usuario:", estudiante)

        # --------------------------------------------------
        # TERCERA OPCIÓN:
        # buscar usuario y comparar nombre de madre/tutor
        # --------------------------------------------------

        if not estudiante:

            print("------------------------------------")
            print("⚠️ NO SE ENCONTRÓ POR tutor_usuario")
            print("BUSCANDO DATOS DEL USUARIO PADRE")

            usuario_padre = db.usuarios.find_one({
                "usuario": usuario,
                "rol": "padre",
                "activo": True
            })

            print("USUARIO PADRE EN DB:")
            print(usuario_padre)

            if usuario_padre:

                nombre_padre = (
                    usuario_padre.get("nombre")
                    or usuario_padre.get("nombre_completo")
                    or usuario_padre.get("nombre_usuario")
                )

                if nombre_padre:

                    print("------------------------------------")
                    print("NOMBRE PADRE:", nombre_padre)

                    estudiante = db.estudiantes.find_one({
                        "$or": [
                            {
                                "madre": nombre_padre,
                                "estado": "activo"
                            },
                            {
                                "tutor": nombre_padre,
                                "estado": "activo"
                            }
                        ]
                    })

                    print(
                        "RESULTADO BÚSQUEDA POR NOMBRE:",
                        estudiante
                    )

    # ======================================================
    # RESULTADO FINAL
    # ======================================================

    print("====================================")
    print("📊 RESULTADO FINAL")
    print("====================================")

    if estudiante:

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
            "MADRE USUARIO:",
            estudiante.get("madre_usuario")
        )

    else:

        print("❌ NO SE ENCONTRÓ ESTUDIANTE")

    print("====================================")

    return estudiante
# ==========================================================
# CONFIGURACIÓN
# ==========================================================

@estudiante_bp.route("/configuracion")
@role_required("estudiante", "padre")
def configuracion():

    rol = session.get("rol")
    usuario = session.get("usuario")

    print("====================================")
    print("⚙️ CONFIGURACIÓN")
    print("====================================")
    print("ROL:", rol)
    print("USUARIO:", usuario)

    estudiante = obtener_estudiante_sesion()

    print("ESTUDIANTE:", estudiante)
    print("====================================")

    return render_template(
        "estudiante/configuracion_estudiante.html",
        estudiante=estudiante,
        rol=rol,
        usuario=usuario
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

    print("====================================")
    print("📧 CAMBIANDO CORREO")
    print("====================================")
    print("USUARIO:", usuario)
    print("NUEVO CORREO:", nuevo_correo)
    print("====================================")

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

    print("USUARIO ENCONTRADO:")
    print(usuario_db)

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

    print("====================================")
    print("📊 RESULTADO ACTUALIZACIÓN")
    print("====================================")
    print("MATCHED:", resultado.matched_count)
    print("MODIFIED:", resultado.modified_count)
    print("====================================")

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

    print("====================================")
    print("🔐 CAMBIO DE CONTRASEÑA")
    print("====================================")
    print("USUARIO:", usuario)
    print("====================================")

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

    print("====================================")
    print("🔐 RESULTADO CAMBIO CONTRASEÑA")
    print("====================================")
    print("MATCHED:", resultado.matched_count)
    print("MODIFIED:", resultado.modified_count)
    print("====================================")

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

    print("====================================")
    print("🏠 DASHBOARD ESTUDIANTE / PADRE")
    print("ROL:", rol)
    print("USUARIO:", usuario)
    print("====================================")

    estudiante = obtener_estudiante_sesion()

    notas = []
    docentes = []
    mensajes = []
    conversaciones_padre = []
    avisos = []

    # ======================================================
    # CARGAR DOCENTES
    # ======================================================

    print("====================================")
    print("👨‍🏫 BUSCANDO DOCENTES")
    print("====================================")

    try:

        docentes = list(
            db.docentes.find()
        )

        print(
            "TOTAL DOCENTES:",
            len(docentes)
        )

        for docente in docentes:

            print("------------------------------------")
            print("DOCENTE ID:", docente.get("_id"))
            print("NOMBRE:", docente.get("nombre"))
            print("USUARIO:", docente.get("usuario"))
            print("ESTADO:", docente.get("estado"))

    except Exception as e:

        print(
            "❌ ERROR AL CARGAR DOCENTES:",
            e
        )

        docentes = []

    print("====================================")

    # ======================================================
    # SI SE ENCONTRÓ ESTUDIANTE
    # ======================================================

    if estudiante:

        estudiante_id = str(
            estudiante.get("_id")
        )

        print("====================================")
        print("📚 CARGANDO INFORMACIÓN ACADÉMICA")
        print("ID ESTUDIANTE:", estudiante_id)
        print("====================================")

        # ==================================================
        # OBTENER NOTAS
        # ==================================================

        notas = list(
            db.notas.find({
                "estudiante_id": estudiante_id
            })
        )

        print(
            "TOTAL NOTAS:",
            len(notas)
        )

        # ==================================================
        # CONVERSACIONES DEL PADRE
        # ==================================================

        if rol == "padre":

            conversaciones_padre = list(
                db.conversaciones.find({
                    "estudiante_id": estudiante_id
                }).sort(
                    "ultima_actualizacion",
                    -1
                )
            )

            print(
                "TOTAL CONVERSACIONES:",
                len(conversaciones_padre)
            )

    else:

        print(
            "❌ NO SE ENCONTRÓ ESTUDIANTE PARA LA SESIÓN"
        )

    # ======================================================
    # AVISOS INSTITUCIONALES
    # ======================================================

    usuario_actual = session.get("usuario")

    print("====================================")
    print("🔎 PRUEBA COLECCIÓN avisos_padres")
    print("USUARIO ACTUAL:", usuario_actual)
    print("====================================")

    todos_avisos_padres = list(
        db.avisos_padres.find()
    )

    print(
        "TOTAL AVISOS EN avisos_padres:",
        len(todos_avisos_padres)
    )

    for aviso in todos_avisos_padres:

        print("------------------------------------")

        print(
            "ID:",
            aviso.get("_id")
        )

        print(
            "USUARIO PADRE:",
            aviso.get("usuario_padre")
        )

        print(
            "NOMBRE PADRE:",
            aviso.get("nombre_padre")
        )

        print(
            "TÍTULO:",
            aviso.get("titulo")
        )

        print(
            "MENSAJE:",
            aviso.get("mensaje")
        )

        print(
            "ESTADO:",
            aviso.get("estado")
        )

        print(
            "FECHA:",
            aviso.get("fecha")
        )

    print("====================================")


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

    print("====================================")
    print("📢 AVISOS INSTITUCIONALES")
    print("USUARIO PADRE:", usuario_actual)
    print("TOTAL AVISOS:", len(avisos))
    print("------------------------------------")

    for aviso in avisos:

        print(
            "ID:",
            aviso.get("_id")
        )

        print(
            "TÍTULO:",
            aviso.get("titulo")
        )

        print(
            "CONTENIDO:",
            aviso.get("contenido")
        )

        print(
            "FECHA:",
            aviso.get("fecha")
        )

        print(
            "ESTADO:",
            aviso.get("estado")
        )

        print("------------------------------------")

    print("====================================")

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

@estudiante_bp.route("/boletin/pdf")
@role_required("estudiante", "padre")
def boletin_pdf():

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
    # CREAR PDF
    # ======================================================

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

    elementos = []

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
            "CIEM ONE",
            subtitulo
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

    # ======================================================
    # DATOS DEL ESTUDIANTE
    # ======================================================

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
        colWidths=[120, 350]
    )

    tabla_datos.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.HexColor("#08142C")
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

    # ======================================================
    # TABLA DE NOTAS
    # ======================================================

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
                colors.HexColor("#08142C")
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

    # ======================================================
    # RESUMEN
    # ======================================================

    promedio_texto = (

        str(promedio_general)

        if promedio_general is not None

        else "—"
    )

    resumen = [

        [
            "Promedio general",
            promedio_texto
        ],

        [
            "Asignaturas",
            str(len(boletin))
        ]
    ]

    tabla_resumen = Table(
        resumen,
        colWidths=[180, 100]
    )

    tabla_resumen.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.HexColor("#EAF1FA")
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

    # ======================================================
    # FIRMAS
    # ======================================================

    firmas = Table([

        [
            "________________________",
            "________________________"
        ],

        [
            "Docente / Tutor",
            "Dirección Académica"
        ]

    ], colWidths=[220, 220])

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

    # ======================================================
    # GENERAR PDF
    # ======================================================

    documento.build(
        elementos
    )

    buffer.seek(0)

    # ======================================================
    # NOMBRE DEL ARCHIVO
    # ======================================================

    nombre_estudiante = (

        estudiante.get(
            "nombre",
            "estudiante"
        )
        .replace(" ", "_")
    )

    return send_file(

        buffer,

        as_attachment=True,

        download_name=(
            f"Boletin_{nombre_estudiante}_2026.pdf"
        ),

        mimetype="application/pdf"
    )
