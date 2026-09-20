from flask import Blueprint, render_template, request, current_app
from flask import send_file
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import mm
from reportlab.lib import colors
import io
import os

from services.ciem_ai import (
    generar_rubrica,
    generar_lista_cotejo,
    generar_practica,
    generar_examen,
    generar_plan
)



# ======================================
# BLUEPRINT CIEM ASISTE IA
# ======================================

ciem_ai_bp = Blueprint(
    "ciem_ai",
    __name__,
    url_prefix="/ciem-ai"
)



# ======================================
# PÁGINA PRINCIPAL
# ======================================

@ciem_ai_bp.route("/")
def inicio():

    tipo_preseleccionado = request.args.get(
        "tipo",
        ""
    )

    return render_template(
        "docente/ciem_ai.html",
        tipo_preseleccionado=tipo_preseleccionado
    )



# ======================================
# GENERADOR DE RECURSOS PEDAGÓGICOS
# ======================================

@ciem_ai_bp.route("/generar", methods=["POST"])
def generar():



    tipo = request.form.get("tipo")


    asignatura = request.form.get(
        "asignatura",
        "No especificada"
    )


    tema = request.form.get(
        "tema",
        "No especificado"
    )


    grado = request.form.get(
        "grado",
        "No especificado"
    )



    # ===============================
    # SELECCIÓN DEL RECURSO
    # ===============================


    if tipo == "rubrica":


        resultado = generar_rubrica(
            asignatura,
            tema,
            grado
        )


        titulo = "Rúbrica de Evaluación"



    elif tipo == "lista":


        resultado = generar_lista_cotejo(
            asignatura,
            tema,
            grado
        )


        titulo = "Lista de Cotejo"



    elif tipo == "practica":


        resultado = generar_practica(
            asignatura,
            tema,
            grado
        )


        titulo = "Guía Práctica"



    elif tipo == "examen":


        resultado = generar_examen(
            asignatura,
            tema,
            grado
        )


        titulo = "Examen"



    elif tipo == "plan":


        resultado = generar_plan(
            asignatura,
            tema,
            grado
        )


        titulo = "Plan de Clase"



    else:


        resultado = """

        <div class="alert alert-warning">

        Debe seleccionar un recurso pedagógico.

        </div>

        """


        titulo = "CIEM Asiste IA"




    return render_template(

        "docente/ciem_ai.html",

        resultado=resultado,

        titulo=titulo,

        asignatura=asignatura,

        tema=tema,

        grado=grado

    )
# ======================================
# GENERAR PDF CIEM ASISTE IA
# ======================================

@ciem_ai_bp.route("/pdf", methods=["POST"])
def generar_pdf():

    contenido = request.form.get("contenido")

    titulo = request.form.get(
        "titulo",
        "CIEM Asiste IA"
    )

    buffer = io.BytesIO()

    documento = SimpleDocTemplate(
        buffer,
        pagesize=(595, 842),
        topMargin=32,
        bottomMargin=32,
        leftMargin=42,
        rightMargin=42
    )

    estilos = getSampleStyleSheet()

    azul_institucional = colors.HexColor("#08142C")
    dorado_institucional = colors.HexColor("#D89F00")
    texto_suave = colors.HexColor("#667085")
    texto_cuerpo = colors.HexColor("#172033")

    estilo_colegio = ParagraphStyle(
        "TituloColegio",
        parent=estilos["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        textColor=azul_institucional,
        alignment=TA_CENTER,
        spaceAfter=2
    )

    estilo_subtitulo = ParagraphStyle(
        "Subtitulo",
        parent=estilos["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=texto_suave,
        alignment=TA_CENTER,
        spaceAfter=16
    )

    estilo_titulo_recurso = ParagraphStyle(
        "TituloRecurso",
        parent=estilos["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        textColor=azul_institucional,
        alignment=TA_CENTER,
        spaceBefore=2,
        spaceAfter=16
    )

    estilo_cuerpo = ParagraphStyle(
        "Cuerpo",
        parent=estilos["Normal"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=15,
        textColor=texto_cuerpo
    )

    elementos = []

    # ==================================
    # ENCABEZADO CON LOGO INSTITUCIONAL
    # ==================================

    logo_path = os.path.join(
        current_app.static_folder,
        "img",
        "logo.jpg"
    )

    if os.path.exists(logo_path):

        logo = Image(
            logo_path,
            width=22 * mm,
            height=22 * mm
        )

        logo.hAlign = "CENTER"

        elementos.append(logo)
        elementos.append(Spacer(1, 8))

    elementos.append(
        Paragraph(
            "COLEGIO INTEGRAL EMANUEL",
            estilo_colegio
        )
    )

    elementos.append(
        Paragraph(
            "Sistema de Gestión Académica · CIEM Asiste IA",
            estilo_subtitulo
        )
    )

    elementos.append(
        HRFlowable(
            width="100%",
            thickness=1.4,
            color=dorado_institucional,
            spaceAfter=16
        )
    )

    elementos.append(
        Paragraph(
            titulo,
            estilo_titulo_recurso
        )
    )

    # ==================================
    # CONTENIDO
    # ==================================

    texto = contenido.replace(
        "<br>",
        "\n"
    ) if contenido else ""

    for linea in texto.split("\n"):

        if linea.strip():

            elementos.append(
                Paragraph(
                    linea,
                    estilo_cuerpo
                )
            )

            elementos.append(
                Spacer(1, 8)
            )

        else:

            elementos.append(
                Spacer(1, 4)
            )

    documento.build(elementos)

    buffer.seek(0)

    nombre_archivo = "CIEM_" + titulo.replace(" ", "_") + ".pdf"

    return send_file(
        buffer,
        as_attachment=True,
        download_name=nombre_archivo,
        mimetype="application/pdf"
    )