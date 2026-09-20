
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from bson import ObjectId
from datetime import datetime

from utils.database import db


# ==========================================================
# BLUEPRINT
# ==========================================================

mensajes_bp = Blueprint(
    "mensajes",
    __name__,
    url_prefix="/mensajes"
)


# ==========================================================
# COLECCIONES
# ==========================================================

usuarios = db.usuarios
docentes = db.docentes
estudiantes = db.estudiantes
conversaciones = db.conversaciones
mensajes = db.mensajes


# ==========================================================
# FUNCIONES AUXILIARES DE MENSAJERÍA
# ==========================================================


def obtener_estudiante():

    usuario = session.get("usuario")
    rol = session.get("rol")


    if not usuario:
        return None

    estudiante = None

    # ======================================================
    # MADRE / PADRE
    # ======================================================

    if rol == "padre":

        # --------------------------------------------------
        # PRIORIDAD 1: MADRE
        # --------------------------------------------------

        estudiante = estudiantes.find_one({
            "madre_usuario": usuario
        })

        if estudiante:

            pass

        # --------------------------------------------------
        # PRIORIDAD 2: TUTOR
        # --------------------------------------------------

        if not estudiante:

            estudiante = estudiantes.find_one({
                "tutor_usuario": usuario
            })

            if estudiante:

                pass

        # --------------------------------------------------
        # NO BUSCAR padre_usuario COMO PRIORIDAD
        # --------------------------------------------------
        #
        # La cuenta familiar principal de CIEM ONE
        # será la MADRE.
        #
        # --------------------------------------------------

    # ======================================================
    # ESTUDIANTE
    # ======================================================

    elif rol == "estudiante":

        estudiante = estudiantes.find_one({
            "usuario": usuario
        })

        if estudiante:

            pass

    # ======================================================
    # RESULTADO
    # ======================================================


    if estudiante:

        pass

    else:

        pass


    return estudiante


# ==========================================================
# OBTENER DOCENTE
# ==========================================================

def obtener_docente():

    usuario = session.get("usuario")


    if not usuario:


        return None

    # ======================================================
    # BUSCAR DOCENTE POR USUARIO
    # ======================================================

    docente = db.docentes.find_one({
        "usuario": usuario
    })

    # ======================================================
    # RESULTADO
    # ======================================================

    if docente:

        pass

    else:

        pass


    return docente


# ==========================================================
# CONVERTIR ID
# ==========================================================


def convertir_objectid(valor):

    """
    Convierte un valor a ObjectId cuando es posible.

    Si el valor ya es ObjectId:
        lo devuelve sin modificar.

    Si es un texto válido de ObjectId:
        lo convierte.

    Si es un código como:
        DOC012
        CIEM-KMBM
        USR004

    lo mantiene como texto.
    """

    # ------------------------------------------------------
    # YA ES OBJECTID
    # ------------------------------------------------------

    if isinstance(valor, ObjectId):

        return valor

    # ------------------------------------------------------
    # VALOR VACÍO
    # ------------------------------------------------------

    if valor is None:

        return None

    # ------------------------------------------------------
    # INTENTAR CONVERTIR
    # ------------------------------------------------------

    try:

        return ObjectId(str(valor))

    except Exception:

        return valor


# ==========================================================
# NORMALIZAR IDENTIFICADORES DE DOCENTE
# ==========================================================
#
# La colección "docentes" no es consistente: la mayoría de
# documentos tiene un _id tipo código ("DOC012"), pero algunos
# fueron insertados dejando que Mongo generara un ObjectId real
# como _id. Como "conversaciones", "notas", etc. guardan
# "docente_id" copiando ese _id tal cual, el mismo docente puede
# terminar identificado de formas distintas según cuándo se creó
# el registro que lo referencia.
#
# Estas dos funciones centralizan cómo se busca un docente y
# cómo se buscan sus conversaciones, para no repetir el mismo
# parche de "probar _id, código y usuario" en cada ruta.
# ==========================================================

def resolver_docente(valor):
    """
    Recibe un valor de docente_id (puede ser _id como string,
    ObjectId, o código tipo "DOC012") y devuelve el documento
    del docente, probando en orden: _id tal cual, código, y
    _id como ObjectId.
    """

    if not valor:
        return None

    docente = docentes.find_one({
        "_id": valor
    })

    if docente:
        return docente

    docente = docentes.find_one({
        "codigo": valor
    })

    if docente:
        return docente

    try:
        docente = docentes.find_one({
            "_id": ObjectId(str(valor))
        })
    except Exception:
        docente = None

    return docente


def condiciones_docente_id(docente):
    """
    Devuelve la lista de condiciones ($or) para encontrar
    conversaciones de un docente, cubriendo los distintos
    formatos con los que "docente_id" pudo haber quedado
    guardado (_id, código, usuario).
    """

    condiciones = []

    for campo in ("_id", "codigo", "usuario"):

        valor = docente.get(campo)

        if valor:
            condiciones.append({
                "docente_id": valor
            })

    return condiciones


# ==========================================================
# CREAR CONVERSACIÓN
# PADRE / DOCENTE
# ==========================================================

@mensajes_bp.route("/crear", methods=["POST"])
def crear():


    # ======================================================
    # OBTENER ESTUDIANTE
    # ======================================================

    estudiante = obtener_estudiante()

    if not estudiante:

        flash(
            "No se encontró el estudiante asociado a su cuenta.",
            "danger"
        )

        return redirect(
            request.referrer or
            url_for("estudiante.dashboard")
        )

    # ======================================================
    # DATOS DEL FORMULARIO
    # ======================================================

    docente_id = request.form.get(
        "docente_id",
        ""
    ).strip()

    texto = request.form.get(
        "mensaje",
        ""
    ).strip()


    # ======================================================
    # VALIDAR DOCENTE
    # ======================================================

    if not docente_id:

        flash(
            "Debe seleccionar un docente.",
            "warning"
        )

        return redirect(
            request.referrer or
            url_for("estudiante.dashboard")
        )

    # ======================================================
    # VALIDAR MENSAJE
    # ======================================================

    if not texto:

        flash(
            "Debe escribir un mensaje.",
            "warning"
        )

        return redirect(
            request.referrer or
            url_for("estudiante.dashboard")
        )

    # ======================================================
    # BUSCAR DOCENTE
    # ======================================================

    docente = resolver_docente(docente_id)

    # ======================================================
    # VALIDAR DOCENTE
    # ======================================================

    if not docente:


        flash(
            "No se encontró el docente seleccionado.",
            "danger"
        )

        return redirect(
            request.referrer or
            url_for("estudiante.dashboard")
        )

    # ======================================================
    # IDENTIFICADORES
    # ======================================================

    estudiante_id = estudiante.get("_id")
    docente_real_id = docente.get("_id")


    # ======================================================
    # BUSCAR CONVERSACIÓN EXISTENTE
    # ======================================================

    conversacion = conversaciones.find_one({

        "estudiante_id": estudiante_id,

        "docente_id": docente_real_id

    })

    # ======================================================
    # CONVERSACIÓN EXISTENTE
    # ======================================================

    if conversacion:

        conversacion_id = conversacion["_id"]

        conversaciones.update_one(

            {
                "_id": conversacion_id
            },

            {
                "$set": {

                    "ultimo_mensaje": texto,

                    "ultima_actualizacion":
                        datetime.now(),

                    "no_leidos_docente": 1,

                    "no_leidos_padre": 0

                }
            }
        )


    # ======================================================
    # NUEVA CONVERSACIÓN
    # ======================================================

    else:

        resultado = conversaciones.insert_one({

            "estudiante_id":
                estudiante_id,

            "docente_id":
                docente_real_id,

            "estudiante":
                estudiante.get("nombre", ""),

            "docente":
                docente.get("nombre", ""),

            "ultimo_mensaje":
                texto,

            "fecha_creacion":
                datetime.now(),

            "ultima_actualizacion":
                datetime.now(),

            "no_leidos_docente":
                1,

            "no_leidos_padre":
                0

        })

        conversacion_id = resultado.inserted_id


    # ======================================================
    # GUARDAR MENSAJE
    # ======================================================

    mensajes.insert_one({

        "conversacion_id":
            conversacion_id,

        "emisor":
            "padre",

        "mensaje":
            texto,

        "fecha":
            datetime.now(),

        "leido":
            False

    })


    return redirect(

        url_for(
            "mensajes.chat",
            conversacion_id=str(
                conversacion_id
            )
        )

    )


@mensajes_bp.route("/chat/<conversacion_id>")
def chat(conversacion_id):


    try:

        conversacion_id_obj = ObjectId(
            conversacion_id
        )

    except Exception:

        flash(
            "ID de conversación inválido.",
            "danger"
        )

        return redirect("/")

    # ======================================================
    # BUSCAR CONVERSACIÓN
    # ======================================================

    conversacion = conversaciones.find_one({

        "_id":
            conversacion_id_obj

    })


    if not conversacion:

        flash(
            "Conversación no encontrada.",
            "danger"
        )

        return redirect("/")

    # ======================================================
    # BUSCAR MENSAJES
    # ======================================================

    lista_mensajes = list(

        mensajes.find({

            "conversacion_id":
                conversacion_id_obj

        }).sort(

            "fecha",
            1

        )

    )


    for mensaje in lista_mensajes:

        pass


    
    # ======================================================
    # MARCAR COMO LEÍDOS
    # ======================================================

    rol = session.get("rol")

    if rol == "docente":

        conversaciones.update_one(

            {
                "_id":
                    conversacion_id_obj
            },

            {
                "$set": {
                    "no_leidos_docente": 0
                }
            }

        )

    elif rol == "padre":

        conversaciones.update_one(

            {
                "_id":
                    conversacion_id_obj
            },

            {
                "$set": {
                    "no_leidos_padre": 0
                }
            }

        )


    return render_template(

        "chat/chat.html",

        conversacion=conversacion,

        mensajes=lista_mensajes

    )


# ==========================================================
# BANDEJA DOCENTE
# ==========================================================

@mensajes_bp.route("/docente")
def bandeja_docente():

    docente = obtener_docente()

    if not docente:

        flash(
            "Docente no encontrado.",
            "danger"
        )

        return redirect("/")

    # ======================================================
    # DATOS DEL DOCENTE
    # ======================================================

    docente_id = docente.get("_id")
    docente_codigo = docente.get("codigo")
    docente_usuario = docente.get("usuario")

    # ======================================================
    # BUSCAR CONVERSACIONES
    # ======================================================

    condiciones = condiciones_docente_id(docente)

    lista = []

    if condiciones:

        lista = list(

            conversaciones.find({
                "$or": condiciones
            }).sort(
                "ultima_actualizacion",
                -1
            )

        )

    # ======================================================
    # COMPLETAR NOMBRE DE LA MADRE
    # ======================================================

    for conversacion in lista:

        estudiante_id = conversacion.get(
            "estudiante_id"
        )

        estudiante = None

        # ----------------------------------------------
        # BUSCAR ESTUDIANTE
        # ----------------------------------------------

        if estudiante_id:

            estudiante = estudiantes.find_one({
                "_id": estudiante_id
            })

        # ----------------------------------------------
        # SI NO LO ENCUENTRA, BUSCAR POR NOMBRE
        # ----------------------------------------------

        if not estudiante:

            nombre_estudiante = conversacion.get(
                "estudiante"
            )

            if nombre_estudiante:

                estudiante = estudiantes.find_one({
                    "nombre": {
                        "$regex": "^" + nombre_estudiante,
                        "$options": "i"
                    }
                })

        # ----------------------------------------------
        # OBTENER DATOS DE LA MADRE
        # ----------------------------------------------
        #
        # Algunos registros (por datos antiguos, ej. atorrez)
        # tienen "madre_nombre" o el "madre" ya guardado en la
        # conversación como el objeto completo de la madre en
        # vez de solo el texto del nombre. Esto normaliza ambos
        # casos para no mostrar el diccionario crudo en la bandeja.

        def _texto_madre(valor, campo="nombre"):

            if isinstance(valor, dict):

                return (
                    valor.get(campo)
                    or valor.get("nombre")
                    or valor.get("usuario")
                )

            return valor

        if estudiante:

            madre_nombre = _texto_madre(
                estudiante.get("madre_nombre")
            )

            madre_usuario = _texto_madre(
                estudiante.get("madre_usuario"),
                campo="usuario"
            )

            # ------------------------------------------
            # GUARDAR EN LA CONVERSACIÓN
            # ------------------------------------------

            if madre_nombre:
                conversacion["madre"] = madre_nombre

            if madre_usuario:
                conversacion["madre_usuario"] = madre_usuario

        # ----------------------------------------------
        # SI YA EXISTE EL DATO EN LA CONVERSACIÓN
        # (puede venir mal guardado desde antes, ej. como
        # el objeto completo de la madre)
        # ----------------------------------------------

        conversacion["madre"] = (
            _texto_madre(conversacion.get("madre"))
            or "Padre/Madre de familia"
        )

    # ======================================================
    # DEBUG
    # ======================================================


    for conversacion in lista:

        pass


    # ======================================================
    # MOSTRAR BANDEJA
    # ======================================================

    return render_template(

        "docente/mensajes.html",

        conversaciones=lista,

        docente=docente

    )
# ==========================================================
# BANDEJA DE MENSAJES DEL ESTUDIANTE
# ==========================================================

@mensajes_bp.route("/estudiante")
def bandeja_estudiante():

    usuario = session.get("usuario")
    rol = session.get("rol")

    # ======================================================
    # VERIFICAR SESIÓN
    # ======================================================

    if not usuario or rol not in ("estudiante", "padre"):

        flash(
            "Debe iniciar sesión para ver sus mensajes.",
            "warning"
        )

        return redirect(
            url_for("login")
        )

    # ======================================================
    # BUSCAR ESTUDIANTE SEGÚN EL ROL
    # ======================================================

    if rol == "estudiante":

        estudiante = estudiantes.find_one({
            "usuario": usuario,
            "estado": "activo"
        })

    else:

        estudiante = estudiantes.find_one({
            "madre_usuario": usuario,
            "estado": "activo"
        })

    if not estudiante:

        flash(
            "No se encontró la información del estudiante.",
            "warning"
        )

        return redirect(
            url_for("estudiante.dashboard")
        )

    # ======================================================
    # OBTENER DOCENTES
    # ======================================================

    lista_docentes = list(
        docentes.find({
            "activo": {
                "$ne": False
            }
        }).sort(
            "nombre",
            1
        )
    )

    # ======================================================
    # BUSCAR CONVERSACIONES DEL ESTUDIANTE
    # ======================================================

    estudiante_id = estudiante.get("_id")

    conversaciones_estudiante = list(
        conversaciones.find({
            "estudiante_id": estudiante_id
        }).sort(
            "ultima_actualizacion",
            -1
        )
    )

    # ======================================================
    # MOSTRAR BANDEJA
    # ======================================================

    return render_template(

        "mensaje/bandeja_padre.html",

        conversaciones=conversaciones_estudiante,

        estudiante=estudiante,

        docentes=lista_docentes

    )

# ==========================================================
# BANDEJA DE MENSAJES DE LA MADRE
# ==========================================================

@mensajes_bp.route("/padre")
def bandeja_padre():

    usuario = session.get("usuario")
    rol = session.get("rol")


    # ======================================================
    # VERIFICAR SESIÓN
    # ======================================================

    if not usuario:

        flash(
            "Debe iniciar sesión para ver sus mensajes.",
            "warning"
        )

        return redirect(
            url_for("login")
        )

    # ======================================================
    # BUSCAR ESTUDIANTE DE LA MADRE
    # ======================================================

    estudiante = estudiantes.find_one({
        "madre_usuario": usuario
    })


    if not estudiante:

        flash(
            "No se encontró el estudiante asociado a esta madre.",
            "warning"
        )

        return redirect(
            url_for("estudiante.dashboard")
        )
    # ======================================================
    # CORREGIR CONVERSACIONES ANTIGUAS DE LA MADRE
    # ======================================================

    estudiante_id_actual = estudiante.get("_id")

    # ======================================================
    # OBTENER DOCENTES
    # ======================================================

    lista_docentes = list(
        docentes.find({
            "activo": {
                "$ne": False
            }
        }).sort(
            "nombre",
            1
        )
    )


    for docente in lista_docentes:

        pass


    # ======================================================
    # BUSCAR CONVERSACIONES
    # ======================================================

    estudiante_id = estudiante.get("_id")

    conversaciones_padre = list(
        conversaciones.find({
            "estudiante_id": estudiante_id
        }).sort(
            "ultima_actualizacion",
            -1
        )
    )

    # ======================================================
    # DEBUG
    # ======================================================


    for conversacion in conversaciones_padre:

        pass


    # ======================================================
    # MOSTRAR BANDEJA
    # ======================================================

    return render_template(

        "mensaje/bandeja_padre.html",

        conversaciones=conversaciones_padre,

        estudiante=estudiante,

        docentes=lista_docentes

    )

# ==========================================================
# RESPONDER MENSAJE
# ==========================================================

@mensajes_bp.route("/responder", methods=["POST"])
def responder():

    conversacion_id = request.form.get(
        "conversacion_id",
        ""
    ).strip()

    texto = request.form.get(
        "mensaje",
        ""
    ).strip()

    # ======================================================
    # VALIDAR DATOS
    # ======================================================

    if not conversacion_id or not texto:

        flash(
            "Debe escribir un mensaje.",
            "warning"
        )

        return redirect(
            request.referrer or "/"
        )

    # ======================================================
    # CONVERTIR ID
    # ======================================================

    try:

        conversacion_id_obj = ObjectId(
            conversacion_id
        )

    except Exception:

        flash(
            "ID de conversación inválido.",
            "danger"
        )

        return redirect(
            request.referrer or "/"
        )

    # ======================================================
    # BUSCAR CONVERSACIÓN
    # ======================================================

    conversacion = conversaciones.find_one(
        {
            "_id": conversacion_id_obj
        }
    )

    if not conversacion:


        flash(
            "Conversación no encontrada.",
            "danger"
        )

        return redirect(
            request.referrer or "/"
        )

    # ======================================================
    # MOSTRAR INFORMACIÓN
    # ======================================================


    # ======================================================
    # OBTENER ROL
    # ======================================================

    rol = session.get("rol")

    # ======================================================
    # DOCENTE RESPONDE
    # ======================================================

    if rol == "docente":

        emisor = "docente"

        actualizar = {

            "ultimo_mensaje": texto,

            "ultima_actualizacion": datetime.now(),

            # La madre tiene un mensaje nuevo
            "no_leidos_padre": 1,

            # El docente ya respondió
            "no_leidos_docente": 0

        }

    # ======================================================
    # PADRE RESPONDE
    # ======================================================

    elif rol == "padre":

        emisor = "padre"

        actualizar = {

            "ultimo_mensaje": texto,

            "ultima_actualizacion": datetime.now(),

            # El docente tiene un mensaje nuevo
            "no_leidos_docente": 1,

            # La madre ya respondió
            "no_leidos_padre": 0

        }

    # ======================================================
    # ROL NO AUTORIZADO
    # ======================================================

    else:

        flash(
            "Usuario no autorizado.",
            "danger"
        )

        return redirect(
            request.referrer or "/"
        )

    # ======================================================
    # GUARDAR MENSAJE
    # ======================================================

    resultado_mensaje = mensajes.insert_one({

        "conversacion_id":
            conversacion_id_obj,

        "emisor":
            emisor,

        "mensaje":
            texto,

        "fecha":
            datetime.now(),

        "leido":
            False

    })


    # ======================================================
    # ACTUALIZAR CONVERSACIÓN
    # ======================================================

    resultado_actualizacion = conversaciones.update_one(

        {
            "_id":
                conversacion_id_obj
        },

        {
            "$set":
                actualizar
        }

    )


    # ======================================================
    # MOSTRAR DESTINATARIO
    # ======================================================

    if rol == "docente":

        pass


    elif rol == "padre":

        pass


    # ======================================================
    # COMPROBAR CONVERSACIÓN
    # ======================================================

    conversacion_comprobada = conversaciones.find_one(
        {
            "_id":
                conversacion_id_obj
        }
    )


    if conversacion_comprobada:

        pass


    # ======================================================
    # VOLVER AL CHAT
    # ======================================================

    return redirect(
        url_for(
            "mensajes.chat",
            conversacion_id=conversacion_id
        )
    )
# ==========================================================
# CONTADOR DE MENSAJES NO LEÍDOS
# ==========================================================

@mensajes_bp.route("/contador")
def contador():

    rol = session.get("rol")
    usuario = session.get("usuario")

    total = 0

    # ======================================================
    # DOCENTE
    # ======================================================

    if rol == "docente":

        docente = docentes.find_one({

            "usuario":
                usuario

        })

        if docente:

            condiciones = condiciones_docente_id(docente)

            if condiciones:

                total = conversaciones.count_documents({

                    "$or": condiciones,

                    "no_leidos_docente": {
                        "$gt": 0
                    }

                })

    # ======================================================
    # PADRE
    # ======================================================

    elif rol == "padre":

        estudiante = obtener_estudiante()

        if estudiante:

            estudiante_id = estudiante.get("_id")

            total = conversaciones.count_documents({

                "estudiante_id":
                    estudiante_id,

                "no_leidos_padre": {
                    "$gt": 0
                }

            })

    return {
        "total": total
    }


# ==========================================================
# MARCAR CONVERSACIÓN COMO LEÍDA
# ==========================================================

@mensajes_bp.route("/leer/<id>")
def marcar_leido(id):

    try:

        conversacion_id = ObjectId(id)

    except Exception:

        flash(
            "ID de conversación inválido.",
            "danger"
        )

        return redirect(
            request.referrer or "/"
        )

    rol = session.get("rol")

    # ======================================================
    # MARCAR MENSAJES
    # ======================================================

    mensajes.update_many(

        {
            "conversacion_id":
                conversacion_id
        },

        {
            "$set": {
                "leido": True
            }
        }

    )

    # ======================================================
    # MARCAR SEGÚN ROL
    # ======================================================

    if rol == "docente":

        conversaciones.update_one(

            {
                "_id":
                    conversacion_id
            },

            {
                "$set": {
                    "no_leidos_docente": 0
                }
            }

        )

    elif rol == "padre":

        conversaciones.update_one(

            {
                "_id":
                    conversacion_id
            },

            {
                "$set": {
                    "no_leidos_padre": 0
                }
            }

        )

    return redirect(
        request.referrer or "/"
    )


# ==========================================================
# ELIMINAR CONVERSACIÓN
# ==========================================================

@mensajes_bp.route("/eliminar/<id>")
def eliminar(id):

    try:

        conversacion_id = ObjectId(id)

    except Exception:

        flash(
            "ID de conversación inválido.",
            "danger"
        )

        return redirect(
            request.referrer or "/"
        )

    # ======================================================
    # ELIMINAR CONVERSACIÓN
    # ======================================================

    conversaciones.delete_one({

        "_id":
            conversacion_id

    })

    # ======================================================
    # ELIMINAR MENSAJES
    # ======================================================

    mensajes.delete_many({

        "conversacion_id":
            conversacion_id

    })

    flash(
        "Conversación eliminada correctamente.",
        "success"
    )

    return redirect(
        request.referrer or "/"
    )

