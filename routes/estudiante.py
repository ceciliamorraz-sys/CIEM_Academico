from flask import (
    Blueprint,
    render_template,
    session,
    request,
    flash,
    redirect,
    url_for
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
    # ROL ESTUDIANTE
    # ======================================================

    if rol == "estudiante":

        estudiante = db.estudiantes.find_one({
            "usuario": usuario,
            "estado": "activo"
        })

        print("====================================")
        print("🎓 BÚSQUEDA ESTUDIANTE")
        print("USUARIO:", usuario)
        print("RESULTADO:", estudiante)
        print("====================================")

    # ======================================================
    # ROL PADRE
    # ======================================================

    elif rol == "padre":

        print("====================================")
        print("👨‍👩‍👧 BUSCANDO HIJO DEL PADRE")
        print("USUARIO:", usuario)
        print("====================================")

        print("🔥🔥🔥 CÓDIGO NUEVO EJECUTÁNDOSE 🔥🔥🔥")

        estudiante = db.estudiantes.find_one({
            "madre_usuario": usuario
        })

        print("====================================")
        print("🔍 PRUEBA SIN ESTADO")
        print("MADRE_USUARIO:", usuario)
        print("RESULTADO SIN ESTADO:", estudiante)
        print("====================================")
        print("====================================")
        print("📋 DATOS DE ESTUDIANTES EN FLASK")

        todos_estudiantes = list(
            db.estudiantes.find(
                {},
                {
                    "_id": 1,
                    "nombre": 1,
                    "madre_usuario": 1,
                    "padre_usuario": 1,
                    "estado": 1
                }
            )
        )

        print("TOTAL:", len(todos_estudiantes))

        for est in todos_estudiantes:
            print(est)

        print("====================================")

    # ======================================================
    # RESULTADO FINAL
    # ======================================================

    print("====================================")
    print("📌 RESULTADO FINAL ESTUDIANTE")
    print("RESULTADO:", estudiante)
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
    print("ROL:", rol)
    print("USUARIO:", usuario)
    print("====================================")

    estudiante = obtener_estudiante_sesion()

    return render_template(
        "estudiante/configuracion.html",
        estudiante=estudiante,
        rol=rol,
        usuario=usuario
    )

# ==========================================================
# CAMBIAR CORREO
# ==========================================================

@estudiante_bp.route("/cambiar-correo", methods=["POST"])
@role_required("estudiante", "padre")
def cambiar_correo():

    nuevo_correo = request.form.get(
        "nuevo_correo",
        ""
    ).strip().lower()

    usuario = session.get("usuario")

    print("====================================")
    print("CAMBIO DE CORREO")
    print("USUARIO:", usuario)
    print("NUEVO CORREO:", nuevo_correo)

    # Validar correo
    if not nuevo_correo:

        flash(
            "Debe ingresar un correo electrónico.",
            "danger"
        )

        return redirect(
            url_for("estudiante.configuracion")
        )

    # Buscar usuario
    user = db.usuarios.find_one({
        "usuario": usuario
    })

    print("USUARIO ENCONTRADO:", user)

    if not user:

        flash(
            "No se encontró el usuario.",
            "danger"
        )

        return redirect(
            url_for("estudiante.configuracion")
        )

    # Actualizar correo
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

    print(
        "DOCUMENTOS MODIFICADOS:",
        resultado.modified_count
    )

    print("CORREO ACTUALIZADO CORRECTAMENTE")
    print("====================================")

    flash(
        "Correo actualizado correctamente.",
        "success"
    )

    return redirect(
        url_for("estudiante.configuracion")
    )
# ======================================================
# RESULTADO FINAL
# ======================================================

    print("====================================")
    print("RESULTADO FINAL")

    if estudiante:

        print("✅ ESTUDIANTE ENCONTRADO")
        print("ID:", estudiante.get("_id"))
        print("NOMBRE:", estudiante.get("nombre"))
        print("PADRE:", estudiante.get("padre"))
        print("GRADO:", estudiante.get("grado"))
        print("SECCIÓN:", estudiante.get("seccion"))
        print("USUARIO:", estudiante.get("usuario"))
        print("ESTADO:", estudiante.get("estado"))

    else:

        print("❌ NO SE ENCONTRÓ ESTUDIANTE")
        print("USUARIO BUSCADO:", usuario)

    print("====================================")

    return estudiante


# ==========================================================
# DASHBOARD ESTUDIANTE / PADRE
# ==========================================================

@estudiante_bp.route("/")
@role_required("estudiante", "padre")
def dashboard():

    rol = session.get("rol")
    usuario = session.get("usuario")

    print("\n====================================")
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
    # ESTUDIANTE ENCONTRADO
    # ======================================================

    if estudiante:

        estudiante_id = str(
            estudiante.get("_id")
        )

        print("====================================")
        print("✅ ESTUDIANTE ENCONTRADO")
        print("ID:", estudiante_id)
        print("NOMBRE:", estudiante.get("nombre"))
        print("GRADO:", estudiante.get("grado"))
        print("SECCIÓN:", estudiante.get("seccion"))
        print("PADRE:", estudiante.get("padre"))
        print("====================================")

        # ==================================================
        # COMPARACIÓN DE ID
        # ==================================================

        print("====================================")
        print("🔎 COMPARACIÓN DE ID")
        print("ID DEL ESTUDIANTE:", estudiante_id)

        nota_prueba = db.notas.find_one({
            "estudiante_id": estudiante_id
        })

        print(
            "NOTA ENCONTRADA CON ESTE ID:",
            nota_prueba
        )

        nota_real = db.notas.find_one({
            "estudiante_id": "6a4688082ff5b2fcc47d8ccb"
        })

        print(
            "NOTA CON ID REAL:",
            nota_real
        )

        print("====================================")

        # ==================================================
        # OBTENER NOTAS
        # ==================================================

        notas = list(
            db.notas.find({
                "estudiante_id": estudiante_id
            })
        )

        print("====================================")
        print("📊 NOTAS DEL ESTUDIANTE")
        print("TOTAL NOTAS:", len(notas))

        for nota in notas:

            print(
                "ASIGNATURA:",
                nota.get("asignatura_nombre"),
                "| PERIODO:",
                nota.get("periodo"),
                "| EVALUACIÓN:",
                nota.get("evaluacion"),
                "| EP1:",
                nota.get("ep1"),
                "| EP2:",
                nota.get("ep2"),
                "| EP3:",
                nota.get("ep3"),
                "| EP4:",
                nota.get("ep4"),
                "| EP5:",
                nota.get("ep5"),
                "| EP6:",
                nota.get("ep6"),
                "| EP7:",
                nota.get("ep7"),
                "| EP8:",
                nota.get("ep8"),
                "| EP9:",
                nota.get("ep9"),
                "| EP10:",
                nota.get("ep10"),
                "| ACUM:",
                nota.get("acumulado"),
                "| PROM:",
                nota.get("promedio")
            )

        print("====================================")

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
                "💬 CONVERSACIONES:",
                len(conversaciones_padre)
            )

    # ==================================================
    # AVISOS
    # ==================================================

    avisos = list(
        db.avisos.find({
            "activo": True
        }).sort(
            "fecha",
            -1
        ).limit(10)
    )

    # ==================================================
    # MOSTRAR DASHBOARD
    # ==================================================

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

    rol = session.get("rol")
    usuario = session.get("usuario")

    # ======================================================
    # BUSCAR ESTUDIANTE
    # ======================================================

    estudiante = None

    if rol == "estudiante":

        estudiante = db.estudiantes.find_one({
            "usuario": usuario
        })

    elif rol == "padre":

        estudiante = db.estudiantes.find_one({
            "usuario": usuario
        })

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
        estudiante["_id"]
    )

    # ======================================================
    # OBTENER NOTAS REALES
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
            asignatura["_id"]
        )

        mapa_asignaturas[asignatura_id] = asignatura

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
            or "Asignatura"
        )

        # ----------------------------------------------
        # CREAR ASIGNATURA
        # ----------------------------------------------

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

            except (ValueError, TypeError):

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

                valores.append(
                    float(valor)
                )

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
    # ESTADÍSTICAS
    # ======================================================

    promedios = [

        item["promedio"]

        for item in rendimiento

        if item["promedio"] is not None

    ]

    promedio_general = None

    if promedios:

        promedio_general = round(
            sum(promedios)
            / len(promedios),
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

    if rendimiento:

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
    # DEBUG
    # ======================================================

    print("====================================")
    print("RENDIMIENTO ACADÉMICO")
    print("ESTUDIANTE:", estudiante.get("nombre"))
    print("ID:", estudiante_id)
    print("NOTAS:", len(notas))
    print("ASIGNATURAS:", len(rendimiento))
    print("PROMEDIO GENERAL:", promedio_general)
    print("APROBADAS:", aprobadas)
    print("REFORZAMIENTO:", reforzamiento)

    if mejor_asignatura:

        print(
            "MEJOR ASIGNATURA:",
            mejor_asignatura["asignatura"],
            mejor_asignatura["promedio"]
        )

    print("====================================")

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

    rol = session.get("rol")
    usuario = session.get("usuario")

    estudiante = None

    # ------------------------------------------
    # BUSCAR ESTUDIANTE
    # ------------------------------------------

    if rol == "estudiante":

        estudiante = db.estudiantes.find_one({
            "usuario": usuario
        })

    elif rol == "padre":

        estudiante = db.estudiantes.find_one({
            "usuario": usuario
        })

    # ------------------------------------------
    # VERIFICAR ESTUDIANTE
    # ------------------------------------------

    if not estudiante:

        flash(
            "No se encontró la información del estudiante.",
            "warning"
        )

        return redirect(
            url_for("estudiante.dashboard")
        )

    # ------------------------------------------
    # BUSCAR INFORMACIÓN DE LA CUENTA
    # ------------------------------------------

    usuario_db = db.usuarios.find_one({
        "usuario": usuario
    })

    # ------------------------------------------
    # MOSTRAR PERFIL
    # ------------------------------------------

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

    rol = session.get("rol")
    usuario = session.get("usuario")

    # ======================================================
    # BUSCAR ESTUDIANTE
    # ======================================================

    estudiante = db.estudiantes.find_one({
        "usuario": usuario
    })

    if not estudiante:

        flash(
            "No se encontró el estudiante asociado.",
            "danger"
        )

        return redirect(
            url_for("estudiante.dashboard")
        )

    estudiante_id = str(
        estudiante["_id"]
    )

    # ======================================================
    # OBTENER NOTAS REALES
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
            str(asignatura["_id"])
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

        if corte:

            boletin[asignatura_id][corte] = nota.get(
                "nota",
                nota.get("promedio", 0)
            )

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

    normal = estilos["Normal"]

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
    # GENERAR
    # ======================================================

    documento.build(
        elementos
    )

    buffer.seek(0)

    # ======================================================
    # DESCARGAR PDF
    # ======================================================

    from flask import send_file

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