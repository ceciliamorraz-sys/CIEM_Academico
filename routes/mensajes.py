
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

    print("====================================")
    print("🔎 BUSCANDO ESTUDIANTE")
    print("ROL:", rol)
    print("USUARIO:", usuario)
    print("====================================")

    if not usuario:
        print("❌ No existe usuario en sesión")
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

            print("✅ ESTUDIANTE ENCONTRADO POR MADRE")
            print("MADRE USUARIO:", usuario)
            print("ESTUDIANTE:", estudiante.get("nombre"))

        # --------------------------------------------------
        # PRIORIDAD 2: TUTOR
        # --------------------------------------------------

        if not estudiante:

            estudiante = estudiantes.find_one({
                "tutor_usuario": usuario
            })

            if estudiante:

                print("✅ ESTUDIANTE ENCONTRADO POR TUTOR")
                print("TUTOR USUARIO:", usuario)
                print("ESTUDIANTE:", estudiante.get("nombre"))

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

            print("✅ ESTUDIANTE ENCONTRADO POR USUARIO")
            print("USUARIO:", usuario)
            print("ESTUDIANTE:", estudiante.get("nombre"))

    # ======================================================
    # RESULTADO
    # ======================================================

    print("====================================")
    print("📚 RESULTADO ESTUDIANTE")
    print("====================================")

    if estudiante:

        print("ID:", estudiante.get("_id"))
        print("NOMBRE:", estudiante.get("nombre"))
        print("MADRE:", estudiante.get("madre"))
        print("MADRE USUARIO:", estudiante.get("madre_usuario"))
        print("TUTOR:", estudiante.get("tutor"))

    else:

        print("❌ NO SE ENCONTRÓ ESTUDIANTE")

    print("====================================")

    return estudiante


# ==========================================================
# OBTENER DOCENTE
# ==========================================================

def obtener_docente():

    usuario = session.get("usuario")

    print("====================================")
    print("🔎 BUSCANDO DOCENTE")
    print("USUARIO:", usuario)
    print("====================================")

    if not usuario:

        print("❌ No existe usuario en sesión")

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

        print("✅ DOCENTE ENCONTRADO")
        print("ID:", docente.get("_id"))
        print("CÓDIGO:", docente.get("codigo"))
        print("NOMBRE:", docente.get("nombre"))
        print("USUARIO:", docente.get("usuario"))

    else:

        print("❌ DOCENTE NO ENCONTRADO")
        print("USUARIO BUSCADO:", usuario)

    print("====================================")

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
# CREAR CONVERSACIÓN
# PADRE / DOCENTE
# ==========================================================

@mensajes_bp.route("/crear", methods=["POST"])
def crear():

    print("====================================")
    print("📨 CREANDO MENSAJE")
    print("====================================")

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

    print("DOCENTE ID:", docente_id)
    print("MENSAJE:", texto)

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

    docente = docentes.find_one({
        "_id": docente_id
    })

    # Si no lo encuentra, intentar por código
    if not docente:

        docente = docentes.find_one({
            "codigo": docente_id
        })

    # Si todavía no existe, intentar ObjectId
    if not docente:

        try:

            docente = docentes.find_one({
                "_id": ObjectId(docente_id)
            })

        except Exception:

            pass

    # ======================================================
    # VALIDAR DOCENTE
    # ======================================================

    if not docente:

        print("❌ DOCENTE NO ENCONTRADO")

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

    print("====================================")
    print("✅ DOCENTE ENCONTRADO")
    print("DOCENTE ID:", docente_real_id)
    print("DOCENTE:", docente.get("nombre"))
    print("ESTUDIANTE ID:", estudiante_id)
    print("ESTUDIANTE:", estudiante.get("nombre"))
    print("====================================")

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

        print("♻️ CONVERSACIÓN ACTUALIZADA")

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

        print("🆕 NUEVA CONVERSACIÓN")

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

    print("====================================")
    print("✅ MENSAJE GUARDADO")
    print("CONVERSACIÓN:", conversacion_id)
    print("====================================")

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

    print("====================================")
    print("💬 ABRIENDO CHAT")
    print("ID:", conversacion_id)
    print("====================================")

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

    print("====================================")
    print("🔎 CONVERSACIÓN ENCONTRADA:")
    print(conversacion)
    print("====================================")

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

    print("====================================")
    print("📨 MENSAJES ENCONTRADOS")
    print("TOTAL:", len(lista_mensajes))

    for mensaje in lista_mensajes:

        print("------------------------------------")
        print("ID MENSAJE:", mensaje.get("_id"))
        print("CONVERSACIÓN:", mensaje.get("conversacion_id"))
        print("EMISOR:", mensaje.get("emisor"))
        print("MENSAJE:", mensaje.get("mensaje"))
        print("FECHA:", mensaje.get("fecha"))
        print("LEÍDO:", mensaje.get("leido"))

    print("====================================")

    
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

    print("TOTAL MENSAJES:", len(lista_mensajes))

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
    print("====================================")
    print("🔎 IDENTIFICADORES DEL DOCENTE")
    print("NOMBRE:", docente.get("nombre"))
    print("_id:", docente.get("_id"))
    print("codigo:", docente.get("codigo"))
    print("usuario:", docente.get("usuario"))
    print("====================================")

    print("🔎 BUSCANDO CONVERSACIONES POR CADA IDENTIFICADOR")

    if docente.get("_id") is not None:
        prueba_id = list(
            conversaciones.find({
                "docente_id": docente.get("_id")
            })
        )
        print("POR _id:", len(prueba_id))

    if docente.get("codigo"):
        prueba_codigo = list(
            conversaciones.find({
                "docente_id": docente.get("codigo")
            })
        )
        print("POR codigo:", len(prueba_codigo))

    if docente.get("usuario"):
        prueba_usuario = list(
            conversaciones.find({
                "docente_id": docente.get("usuario")
            })
        )
        print("POR usuario:", len(prueba_usuario))

    print("====================================")
    print("📨 BANDEJA DOCENTE")
    print("DOCENTE:", docente.get("nombre"))
    print("ID:", docente_id)
    print("CODIGO:", docente_codigo)
    print("USUARIO:", docente_usuario)
    print("====================================")

    # ======================================================
    # BUSCAR CONVERSACIONES
    # ======================================================

    condiciones = []

    if docente_id:

        condiciones.append({
            "docente_id": docente_id
        })

    if docente_codigo:

        condiciones.append({
            "docente_id": docente_codigo
        })

    if docente_usuario:

        condiciones.append({
            "docente_id": docente_usuario
        })

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

        if estudiante:

            madre_nombre = estudiante.get(
                "madre_nombre"
            )

            madre_usuario = estudiante.get(
                "madre_usuario"
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
        # ----------------------------------------------

        if not conversacion.get("madre"):

            conversacion["madre"] = "Madre"

    # ======================================================
    # DEBUG
    # ======================================================

    print("====================================")
    print("📬 TOTAL CONVERSACIONES:", len(lista))
    print("====================================")

    for conversacion in lista:

        print("------------------------------------")

        print(
            "ID:",
            conversacion.get("_id")
        )

        print(
            "MADRE:",
            conversacion.get(
                "madre",
                "Madre"
            )
        )

        print(
            "MADRE USUARIO:",
            conversacion.get(
                "madre_usuario",
                ""
            )
        )

        print(
            "ESTUDIANTE:",
            conversacion.get(
                "estudiante",
                ""
            )
        )

        print(
            "DOCENTE ID:",
            conversacion.get(
                "docente_id"
            )
        )

        print(
            "ÚLTIMO MENSAJE:",
            conversacion.get(
                "ultimo_mensaje",
                ""
            )
        )

        print(
            "NO LEÍDOS DOCENTE:",
            conversacion.get(
                "no_leidos_docente",
                0
            )
        )

    print("====================================")

    # ======================================================
    # MOSTRAR BANDEJA
    # ======================================================

    return render_template(

        "docente/mensajes.html",

        conversaciones=lista,

        docente=docente

    )
# ==========================================================
# BANDEJA DE MENSAJES DE LA MADRE
# ==========================================================

@mensajes_bp.route("/padre")
def bandeja_padre():

    usuario = session.get("usuario")
    rol = session.get("rol")

    print("====================================")
    print("💬 BANDEJA DE MENSAJES")
    print("ROL:", rol)
    print("USUARIO:", usuario)
    print("====================================")

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

    print("====================================")
    print("🔎 BUSCANDO HIJO DE LA MADRE")
    print("MADRE:", usuario)
    print("ESTUDIANTE:", estudiante)
    print("====================================")

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

    print("====================================")
    print("🔧 REVISANDO CONVERSACIONES")
    print("ESTUDIANTE ID ACTUAL:", estudiante_id_actual)
    print("ESTUDIANTE:", estudiante.get("nombre"))
    print("MADRE:", estudiante.get("madre_nombre"))
    print("MADRE USUARIO:", estudiante.get("madre_usuario"))
    print("====================================")

    # Buscar conversaciones que pertenecen a esta estudiante
    # pero que todavía tienen el ID antiguo

    conversaciones_antiguas = list(
        conversaciones.find({
            "estudiante": {
                "$regex": "^Kayla Marcela",
                "$options": "i"
            }
        })
    )

    print(
        "CONVERSACIONES ENCONTRADAS:",
        len(conversaciones_antiguas)
    )

    for conversacion in conversaciones_antiguas:

        print("------------------------------------")
        print(
            "ID CONVERSACIÓN:",
            conversacion.get("_id")
        )

        print(
            "ID ANTIGUO:",
            conversacion.get("estudiante_id")
        )

        print(
            "DOCENTE:",
            conversacion.get("docente")
        )

        print(
            "DOCENTE ID:",
            conversacion.get("docente_id")
        )

    # ======================================================
    # ACTUALIZAR LAS CONVERSACIONES
    # ======================================================

    for conversacion in conversaciones_antiguas:

        conversaciones.update_one(

            {
                "_id":
                    conversacion.get("_id")
            },

            {
                "$set": {

                    "estudiante_id":
                        estudiante_id_actual,

                    "estudiante":
                        estudiante.get("nombre"),

                    "madre":
                        estudiante.get(
                            "madre_nombre",
                            "Alma Nubia Morráz Tórrez"
                        ),

                    "madre_usuario":
                        estudiante.get(
                            "madre_usuario",
                            usuario
                        )

                }
            }

        )

    print("====================================")
    print("✅ CONVERSACIONES ACTUALIZADAS")
    print("NUEVO ID:", estudiante_id_actual)
    print("MADRE USUARIO:", usuario)
    print("====================================")

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

    print("====================================")
    print("👨‍🏫 DOCENTES DISPONIBLES")
    print("TOTAL:", len(lista_docentes))

    for docente in lista_docentes:

        print(
            "DOCENTE:",
            docente.get("nombre"),
            "| ID:",
            docente.get("_id"),
            "| USUARIO:",
            docente.get("usuario")
        )

    print("====================================")

    # ======================================================
    # BUSCAR CONVERSACIONES
    # ======================================================

    estudiante_id = estudiante.get("_id")
    print("====================================")
    print("🔎 BUSCANDO CONVERSACIONES DE KAYLA")
    print("ID ACTUAL:", estudiante_id)
    print("MADRE:", estudiante.get("madre_nombre"))
    print("MADRE USUARIO:", estudiante.get("madre_usuario"))
    print("====================================")

    prueba_nombre = list(
        conversaciones.find({
            "estudiante": {
                "$regex": "^Kayla Marcela",
                "$options": "i"
            }
        })
    )

    print(
        "CONVERSACIONES ENCONTRADAS POR NOMBRE:",
        len(prueba_nombre)
    )

    for c in prueba_nombre:

        print("------------------------------------")
        print("ID CONVERSACIÓN:", c.get("_id"))
        print("ESTUDIANTE ID:", c.get("estudiante_id"))
        print("ESTUDIANTE:", c.get("estudiante"))
        print("DOCENTE ID:", c.get("docente_id"))
        print("DOCENTE:", c.get("docente"))
        print("ÚLTIMO MENSAJE:", c.get("ultimo_mensaje"))
        print(
            "NO LEÍDOS MADRE:",
            c.get("no_leidos_padre", 0)
        )

    print("====================================")

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

    print("====================================")
    print("📬 CONVERSACIONES DE LA MADRE")
    print("ESTUDIANTE ID:", estudiante_id)
    print(
        "TOTAL:",
        len(conversaciones_padre)
    )

    for conversacion in conversaciones_padre:

        print("------------------------------------")

        print(
            "ID:",
            conversacion.get("_id")
        )

        print(
            "DOCENTE:",
            conversacion.get("docente")
        )

        print(
            "DOCENTE ID:",
            conversacion.get("docente_id")
        )

        print(
            "ÚLTIMO MENSAJE:",
            conversacion.get("ultimo_mensaje")
        )

        print(
            "NO LEÍDOS:",
            conversacion.get(
                "no_leidos_padre",
                0
            )
        )

    print("====================================")

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

        print("❌ CONVERSACIÓN NO ENCONTRADA")
        print(
            "ID:",
            conversacion_id_obj
        )

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

    print("====================================")
    print("🔎 CONVERSACIÓN PARA RESPONDER")
    print("ID:", conversacion_id_obj)
    print(
        "ESTUDIANTE ID:",
        conversacion.get("estudiante_id")
    )
    print(
        "ESTUDIANTE:",
        conversacion.get("estudiante")
    )
    print(
        "DOCENTE ID:",
        conversacion.get("docente_id")
    )
    print(
        "DOCENTE:",
        conversacion.get("docente")
    )
    print(
        "MADRE:",
        conversacion.get("madre")
    )
    print("====================================")

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

    print("====================================")
    print("✅ MENSAJE GUARDADO")
    print(
        "ID MENSAJE:",
        resultado_mensaje.inserted_id
    )
    print(
        "EMISOR:",
        emisor
    )
    print(
        "MENSAJE:",
        texto
    )
    print("====================================")

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

    print("====================================")
    print("📬 ACTUALIZACIÓN DE CONVERSACIÓN")
    print("====================================")

    print(
        "ROL:",
        rol
    )

    print(
        "EMISOR:",
        emisor
    )

    print(
        "CONVERSACIÓN:",
        conversacion_id
    )

    print(
        "MENSAJE:",
        texto
    )

    print(
        "DOCUMENTOS ENCONTRADOS:",
        resultado_actualizacion.matched_count
    )

    print(
        "DOCUMENTOS MODIFICADOS:",
        resultado_actualizacion.modified_count
    )

    # ======================================================
    # MOSTRAR DESTINATARIO
    # ======================================================

    if rol == "docente":

        print(
            "➡️ DESTINATARIO: MADRE"
        )

        print(
            "NO LEÍDOS MADRE:",
            actualizar.get(
                "no_leidos_padre"
            )
        )

    elif rol == "padre":

        print(
            "➡️ DESTINATARIO: DOCENTE"
        )

        print(
            "NO LEÍDOS DOCENTE:",
            actualizar.get(
                "no_leidos_docente"
            )
        )

    print("====================================")

    # ======================================================
    # COMPROBAR CONVERSACIÓN
    # ======================================================

    conversacion_comprobada = conversaciones.find_one(
        {
            "_id":
                conversacion_id_obj
        }
    )

    print("====================================")
    print("🔎 CONVERSACIÓN DESPUÉS DE ACTUALIZAR")
    print("====================================")

    if conversacion_comprobada:

        print(
            "ESTUDIANTE ID:",
            conversacion_comprobada.get(
                "estudiante_id"
            )
        )

        print(
            "ESTUDIANTE:",
            conversacion_comprobada.get(
                "estudiante"
            )
        )

        print(
            "DOCENTE ID:",
            conversacion_comprobada.get(
                "docente_id"
            )
        )

        print(
            "DOCENTE:",
            conversacion_comprobada.get(
                "docente"
            )
        )

        print(
            "MADRE:",
            conversacion_comprobada.get(
                "madre"
            )
        )

        print(
            "ÚLTIMO MENSAJE:",
            conversacion_comprobada.get(
                "ultimo_mensaje"
            )
        )

        print(
            "NO LEÍDOS MADRE:",
            conversacion_comprobada.get(
                "no_leidos_padre",
                0
            )
        )

        print(
            "NO LEÍDOS DOCENTE:",
            conversacion_comprobada.get(
                "no_leidos_docente",
                0
            )
        )

    print("====================================")

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

            docente_id = docente.get("_id")

            total = conversaciones.count_documents({

                "docente_id":
                    docente_id,

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

