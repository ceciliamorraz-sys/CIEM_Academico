from flask import Blueprint, render_template, request
from flask import send_file
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io

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

    return render_template(
        "docente/ciem_ai.html"
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

    buffer = io.BytesIO()


    documento = SimpleDocTemplate(
        buffer,
        pagesize=(595,842)
    )


    estilos = getSampleStyleSheet()


    elementos = []


    texto = contenido.replace(
        "<br>",
        "\n"
    )


    for linea in texto.split("\n"):

        elementos.append(
            Paragraph(
                linea,
                estilos["Normal"]
            )
        )

        elementos.append(
            Spacer(1,12)
        )


    documento.build(elementos)


    buffer.seek(0)


    return send_file(
        buffer,
        as_attachment=True,
        download_name="CIEM_Asiste_IA.pdf",
        mimetype="application/pdf"
    )