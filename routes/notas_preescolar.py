"""
Evidencias de aprendizaje de PREESCOLAR (escala AA / AP).

Preescolar no usa EP1-EP10 ni notas sobre 100. Se evalúa con la hoja
"Evidencias de Aprendizaje": 5 dimensiones con indicadores marcados AA o AP.

Una sola hoja por estudiante y corte. Cada docente llena SOLO los
indicadores de su materia:

    Docente titular / guía (cualquier materia de preescolar que no sea
    de las especiales)                       -> indicadores "titular"
    Educación Física                          -> "ef"
    Educación Cristiana                       -> "ec"
    Inglés                                    -> "ingles"
    Informática Educativa                     -> "informatica"

Colección nueva:  evidencias_preescolar
    un documento por (estudiante_id, periodo, evaluacion)
    {
      valores: {"cog1": "AA", "soc2": "AP", ...},
      desarrollo_personal: "AA" | "AP" | "",
      promedio_general:    "AA" | "AP" | "",   # se recalcula en cada guardado
      actualizado_por: {indicador_id: docente_id}
    }

Uso en routes/docentes.py (ver PARCHE_docentes.md):
    from routes.notas_preescolar import vista_notas_preescolar, registrar_preescolar
"""

import os
import re
import unicodedata
import zipfile
from datetime import datetime
from io import BytesIO

from bson import ObjectId
from flask import (
    current_app,
    flash,
    send_file,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from config.database import db


# ==========================================================
# CONFIGURACIÓN (editable por el colegio)
# ==========================================================

# Si más de esta fracción de los indicadores marcados son AA,
# el promedio general queda en AA; si no, en AP.
UMBRAL_AA_PROMEDIO = 0.5

DIMENSIONES = [
    ("cognitiva", "Dimensión cognitiva"),
    ("social", "Dimensión social"),
    ("fisica", "Dimensión física"),
    ("emocional", "Dimensión emocional"),
    ("espiritual", "Dimensión espiritual"),
]

# (id, texto, dueño). Mismas filas que la hoja: 5 / 4 / 4 / 4 / 5.
# Son una PROPUESTA: se pueden cambiar los textos sin tocar nada más,
# pero conviene no cambiar los ids una vez que haya notas guardadas.
INDICADORES = {
    "cognitiva": [
        ("cog1", "Reconoce y nombra colores, formas y tamaños", "titular"),
        ("cog2", "Cuenta y relaciona cantidades hasta el 10", "titular"),
        ("cog3", "Expresa ideas con oraciones claras", "titular"),
        ("cog4", "Reconoce vocabulario básico en inglés (saludos, colores, números)", "ingles"),
        ("cog5", "Usa con apoyo el mouse y el teclado en actividades sencillas", "informatica"),
    ],
    "social": [
        ("soc1", "Comparte materiales con sus compañeros", "titular"),
        ("soc2", "Respeta turnos y escucha cuando otros hablan", "titular"),
        ("soc3", "Sigue las normas del aula", "titular"),
        ("soc4", "Participa y colabora en trabajos de grupo", "titular"),
    ],
    "fisica": [
        ("fis1", "Corre, salta y lanza con coordinación", "ef"),
        ("fis2", "Mantiene el equilibrio en actividades motrices", "ef"),
        ("fis3", "Sigue instrucciones en juegos y rutinas", "ef"),
        ("fis4", "Participa con entusiasmo en las actividades físicas", "ef"),
    ],
    "emocional": [
        ("emo1", "Expresa sus emociones de forma adecuada", "titular"),
        ("emo2", "Maneja la frustración con apoyo del adulto", "titular"),
        ("emo3", "Muestra autonomía en sus actividades", "titular"),
        ("emo4", "Se muestra seguro y tranquilo en el aula", "titular"),
    ],
    "espiritual": [
        ("esp1", "Participa en los momentos de oración", "ec"),
        ("esp2", "Escucha con atención los relatos bíblicos", "ec"),
        ("esp3", "Muestra gratitud y respeto hacia los demás", "ec"),
        ("esp4", "Practica el amor y el compartir con sus compañeros", "ec"),
        ("esp5", "Reconoce a Dios como creador en su entorno", "ec"),
    ],
}

# Docentes titulares de preescolar. Se reconocen por su nombre en
# db.docentes (basta que el nombre CONTENGA todas las palabras de "claves",
# sin importar acentos ni mayúsculas) y solo para los niveles indicados.
# Si TITULARES_ESTRICTO es True, una clase de preescolar con materia general
# solo da acceso a la parte del titular a estas docentes; cualquier otro
# docente la ve en solo lectura. Poner False para que cualquier docente con
# materia general sea titular (comportamiento anterior).
TITULARES_ESTRICTO = True

TITULARES_PREESCOLAR = [
    {"claves": ["rosa", "mendoza"], "niveles": ["i nivel", "ii nivel"]},
    {"claves": ["tracy", "rosales"], "niveles": ["iii nivel"]},
]

NOMBRE_DUENO = {
    "ninguno": "Solo lectura",
    "titular": "Docente titular",
    "ef": "Educación Física",
    "ec": "Educación Cristiana",
    "ingles": "Inglés",
    "informatica": "Informática Educativa",
}

ESCALA = {
    "AA": "El estudiante alcanzó las competencias estándar del nivel de grado, "
          "demostrando una comprensión profunda de los conceptos y habilidades "
          "enseñados y superando el desempeño requerido.",
    "AP": "El estudiante muestra un progreso limitado hacia las competencias "
          "estándar del nivel de grado.",
}

MAPA_PREESCOLAR = {
    "i nivel": ["I Nivel", "1er Nivel de Preescolar", "Preescolar I Nivel"],
    "ii nivel": ["II Nivel", "2do Nivel de Preescolar", "Preescolar II Nivel"],
    "iii nivel": ["III Nivel", "3er Nivel de Preescolar", "Preescolar III Nivel"],
}

# periodo + evaluación -> corte (igual que guardar_notas)
CORTES = {
    ("I Semestre", "Primer Parcial"): "I Corte Evaluativo",
    ("I Semestre", "Segundo Parcial"): "II Corte Evaluativo",
    ("II Semestre", "Tercer Parcial"): "III Corte Evaluativo",
    ("II Semestre", "Cuarto Parcial"): "IV Corte Evaluativo",
}


# ==========================================================
# AUXILIARES
# ==========================================================

def _sin_acentos(texto):
    texto = unicodedata.normalize("NFD", str(texto or ""))
    return "".join(c for c in texto if unicodedata.category(c) != "Mn").lower()


def duenio_de_la_asignatura(asignatura_nombre, asignatura_codigo=""):
    """Qué indicadores le tocan a esta materia en preescolar."""

    nombre = _sin_acentos(asignatura_nombre)
    codigo = str(asignatura_codigo or "").strip().upper()

    if "fisica" in nombre:
        return "ef"
    if "cristian" in nombre or "biblia" in nombre or "biblic" in nombre:
        return "ec"
    if "ingles" in nombre or "english" in nombre:
        return "ingles"
    if "informatica" in nombre or codigo == "INF":
        return "informatica"

    return "titular"


def es_titular_registrado(docente, grado):
    nombre = _sin_acentos(docente.get("nombre", ""))
    grado = _sin_acentos(grado).strip()

    for t in TITULARES_PREESCOLAR:
        if all(c in nombre for c in t["claves"]) and grado in t["niveles"]:
            return True

    return False


def rol_del_docente(asignacion, docente):
    """'ef' | 'ec' | 'ingles' | 'informatica' | 'titular' | 'ninguno'"""

    rol = duenio_de_la_asignatura(
        asignacion.get("asignatura_nombre", ""),
        asignacion.get("asignatura_codigo", ""),
    )

    if (
        rol == "titular"
        and TITULARES_ESTRICTO
        and not es_titular_registrado(docente, asignacion.get("grado", ""))
    ):
        return "ninguno"

    return rol


def ids_de(dueno):
    return {
        ind[0]
        for lista in INDICADORES.values()
        for ind in lista
        if ind[2] == dueno
    }


def todos_los_ids():
    return {ind[0] for lista in INDICADORES.values() for ind in lista}


def estudiantes_de_asignacion(asignacion):
    grado = str(asignacion.get("grado", "")).strip()
    seccion = str(asignacion.get("seccion", "")).strip().upper()

    grados = MAPA_PREESCOLAR.get(grado.lower(), [grado])

    filtro = {"grado": {"$in": grados}, "estado": "activo"}

    if seccion:
        filtro["seccion"] = {"$regex": "^" + seccion + "$", "$options": "i"}

    return list(db.estudiantes.find(filtro).sort("nombre", 1))


def calcular_promedio_general(valores):
    marcados = [v for v in valores.values() if v in ("AA", "AP")]

    if not marcados:
        return ""

    aa = sum(1 for v in marcados if v == "AA")

    return "AA" if aa / len(marcados) > UMBRAL_AA_PROMEDIO else "AP"


def _periodo_evaluacion_validos(periodo, evaluacion):
    return (periodo, evaluacion) in CORTES


# ==========================================================
# HOJA IMPRIMIBLE (.docx) con docente y nivel ya puestos
# ==========================================================

RUTA_PLANTILLA = os.path.join("static", "plantillas", "hoja_evidencias_preescolar.docx")

_ROMANO = {"i nivel": "I", "ii nivel": "II", "iii nivel": "III"}

_PAT_DOCENTE = re.compile(
    r'(>Docente:</w:t></w:r><w:r>.*?<w:t xml:space="preserve">) (</w:t>)', re.S
)


def _escapar_xml(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def generar_hoja_docx(nombre_docente, grado):
    """Devuelve BytesIO con la hoja en blanco, con Nivel y Docente llenos."""

    ruta = os.path.join(current_app.root_path, RUTA_PLANTILLA)
    nivel = _ROMANO.get(_sin_acentos(grado).strip(), "")
    nombre = _escapar_xml(nombre_docente)

    salida = BytesIO()

    with zipfile.ZipFile(ruta) as zi, zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as zo:

        for item in zi.infolist():

            datos = zi.read(item.filename)

            if item.filename == "word/document.xml":

                xml = datos.decode("utf-8")
                xml = _PAT_DOCENTE.sub(lambda m: m.group(1) + " " + nombre + m.group(2), xml)

                if nivel:
                    xml = xml.replace(">I   <", ">" + nivel + "   <")

                datos = xml.encode("utf-8")

            zo.writestr(item, datos)

    salida.seek(0)
    return salida


# ==========================================================
# VISTA  (la llama notas() cuando el nivel es Preescolar)
# ==========================================================

def vista_notas_preescolar(asignacion, estudiantes, docente):

    periodo = request.args.get("periodo") or "I Semestre"
    evaluacion = request.args.get("evaluacion") or "Primer Parcial"

    if not _periodo_evaluacion_validos(periodo, evaluacion):
        periodo, evaluacion = "I Semestre", "Primer Parcial"

    dueno = rol_del_docente(asignacion, docente)

    editables = ids_de(dueno)

    registros = {
        str(r["estudiante_id"]): r
        for r in db.evidencias_preescolar.find({
            "periodo": periodo,
            "evaluacion": evaluacion,
            "estudiante_id": {"$in": [str(e["_id"]) for e in estudiantes]},
        })
    }

    filas = []

    for est in estudiantes:

        eid = str(est["_id"])
        reg = registros.get(eid, {})
        valores = reg.get("valores", {})

        propios = [i for i in editables]
        pendientes = sum(1 for i in propios if valores.get(i) not in ("AA", "AP"))

        filas.append({
            "id": eid,
            "nombre": est.get("nombre", ""),
            "valores": valores,
            "desarrollo_personal": reg.get("desarrollo_personal", ""),
            "promedio_general": reg.get("promedio_general", ""),
            "pendientes": pendientes,
        })

    return render_template(
        "docente/notas_preescolar.html",
        asignacion_id=str(asignacion["_id"]),
        asignatura_nombre=asignacion.get("asignatura_nombre", ""),
        grado=asignacion.get("grado", ""),
        seccion=asignacion.get("seccion", ""),
        docente=docente,
        periodo=periodo,
        evaluacion=evaluacion,
        corte=CORTES[(periodo, evaluacion)],
        cortes=CORTES,
        dimensiones=DIMENSIONES,
        indicadores=INDICADORES,
        nombre_dueno=NOMBRE_DUENO,
        dueno=dueno,
        es_titular=(dueno == "titular"),
        editables=editables,
        escala=ESCALA,
        filas=filas,
    )


# ==========================================================
# GUARDADO
# ==========================================================

def registrar_preescolar(docente_bp, role_required):
    """Registra POST /docente/notas/preescolar/guardar en el blueprint."""

    @docente_bp.route("/notas/preescolar/guardar", methods=["POST"])
    @role_required("docente")
    def guardar_notas_preescolar():

        asignatura_id = request.form.get("asignatura_id", "")
        periodo = request.form.get("periodo", "")
        evaluacion = request.form.get("evaluacion", "")

        usuario = session.get("usuario")
        docente = db.docentes.find_one({"usuario": usuario})

        if not docente:
            flash("Docente no encontrado.", "danger")
            return redirect(url_for("login"))

        codigo = str(docente.get("codigo", "")).strip().upper()
        docente_id = codigo if codigo.startswith("DOC") else "DOC" + codigo

        ids_busqueda = [asignatura_id]
        if ObjectId.is_valid(asignatura_id):
            ids_busqueda.append(ObjectId(asignatura_id))

        asignacion = db.asignaciones_clase.find_one({
            "_id": {"$in": ids_busqueda},
            "docente_id": docente_id,
            "activo": True,
        })

        if not asignacion or str(asignacion.get("nivel", "")).strip().lower() != "preescolar":
            flash("Asignación de preescolar no encontrada.", "danger")
            return redirect(url_for("docente.aulas"))

        if not _periodo_evaluacion_validos(periodo, evaluacion):
            flash("Período o evaluación inválidos.", "warning")
            return redirect(url_for("docente.notas", asignatura_id=asignatura_id))

        dueno = rol_del_docente(asignacion, docente)

        if dueno == "ninguno":
            flash(
                "Su usuario no está registrado como titular de este nivel "
                "de preescolar. Consulte con administración.",
                "warning",
            )
            return redirect(url_for("docente.notas", asignatura_id=asignatura_id))

        permitidos = ids_de(dueno)

        estudiantes = estudiantes_de_asignacion(asignacion)
        guardados = 0

        for est in estudiantes:

            eid = str(est["_id"])
            cambios = {}

            for ind_id in permitidos:

                valor = request.form.get(f"{ind_id}_{eid}", "").strip().upper()

                # Solo AA o AP; vacío = "sin evaluar" y no se escribe
                if valor in ("AA", "AP"):
                    cambios[f"valores.{ind_id}"] = valor
                    cambios[f"actualizado_por.{ind_id}"] = docente_id

            if dueno == "titular":

                dp = request.form.get(f"dp_{eid}", "").strip().upper()

                if dp in ("AA", "AP"):
                    cambios["desarrollo_personal"] = dp

            if not cambios:
                continue

            filtro = {
                "estudiante_id": eid,
                "periodo": periodo,
                "evaluacion": evaluacion,
            }

            cambios.update({
                "grado": asignacion.get("grado", ""),
                "seccion": asignacion.get("seccion", ""),
                "corte": CORTES[(periodo, evaluacion)],
                "fecha": datetime.now(),
            })

            db.evidencias_preescolar.update_one(
                filtro, {"$set": cambios}, upsert=True
            )

            # Recalcular el promedio general con TODO lo guardado
            reg = db.evidencias_preescolar.find_one(filtro)

            db.evidencias_preescolar.update_one(
                filtro,
                {"$set": {
                    "promedio_general": calcular_promedio_general(
                        reg.get("valores", {})
                    )
                }},
            )

            guardados += 1

        flash(
            f"Evidencias guardadas ({NOMBRE_DUENO[dueno]}). "
            f"Estudiantes actualizados: {guardados}",
            "success",
        )

        return redirect(url_for(
            "docente.notas",
            asignatura_id=asignatura_id,
            periodo=periodo,
            evaluacion=evaluacion,
        ))

    @docente_bp.route("/notas/preescolar/hoja/<asignatura_id>")
    @role_required("docente")
    def descargar_hoja_preescolar(asignatura_id):

        usuario = session.get("usuario")
        docente = db.docentes.find_one({"usuario": usuario})

        if not docente:
            return redirect(url_for("login"))

        codigo = str(docente.get("codigo", "")).strip().upper()
        docente_id = codigo if codigo.startswith("DOC") else "DOC" + codigo

        ids_busqueda = [asignatura_id]
        if ObjectId.is_valid(asignatura_id):
            ids_busqueda.append(ObjectId(asignatura_id))

        asignacion = db.asignaciones_clase.find_one({
            "_id": {"$in": ids_busqueda},
            "docente_id": docente_id,
            "activo": True,
        })

        if not asignacion or str(asignacion.get("nivel", "")).strip().lower() != "preescolar":
            flash("Asignación de preescolar no encontrada.", "danger")
            return redirect(url_for("docente.aulas"))

        archivo = generar_hoja_docx(
            docente.get("nombre", ""), asignacion.get("grado", "")
        )

        nivel = _ROMANO.get(_sin_acentos(asignacion.get("grado", "")).strip(), "preescolar")

        return send_file(
            archivo,
            as_attachment=True,
            download_name=f"Hoja_evidencias_{nivel}_Nivel.docx",
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    return guardar_notas_preescolar
