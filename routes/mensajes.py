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
# CREAR CONVERSACIÓN PADRE - DOCENTE
# ==========================================================

@mensajes_bp.route("/crear", methods=["POST"])
def crear():

    estudiante = obtener_estudiante()

    if not estudiante:

        flash(
            "Estudiante no encontrado",
            "danger"
        )

        return redirect("/")


    # ==========================
    # DATOS DEL FORMULARIO
    # ==========================

    docente_id = request.form.get("docente_id")
    texto = request.form.get("mensaje")

    if not docente_id:

        flash(
            "Debe seleccionar un docente",
            "warning"
        )

        return redirect(request.referrer)

    if not texto:

        flash(
            "Debe escribir un mensaje",
            "warning"
        )

        return redirect(request.referrer)


    # ==========================
    # BUSCAR DOCENTE
    # ==========================

    docente = docentes.find_one({

        "_id": docente_id

    })

    if not docente:

        flash(
            "Docente no encontrado",
            "danger"
        )

        return redirect(request.referrer)


    # ==========================
    # BUSCAR CONVERSACIÓN
    # ==========================

    conversacion = conversaciones.find_one({

        "estudiante_id": estudiante["_id"],

        "docente_id": docente["_id"]

    })


    if conversacion:

        conversacion_id = conversacion["_id"]

        conversaciones.update_one(

            {

                "_id": conversacion_id

            },

            {

                "$set": {

                    "ultimo_mensaje": texto,

                    "ultima_actualizacion": datetime.now(),

                    "no_leidos_docente": 1

                }

            }

        )

    else:

        resultado = conversaciones.insert_one({

            "estudiante_id": estudiante["_id"],

            "docente_id": docente["_id"],

            "estudiante": estudiante["nombre"],

            "docente": docente["nombre"],

            "ultimo_mensaje": texto,

            "fecha_creacion": datetime.now(),

            "ultima_actualizacion": datetime.now(),

            "no_leidos_docente": 1,

            "no_leidos_padre": 0

        })

        conversacion_id = resultado.inserted_id


    # ==========================
    # GUARDAR MENSAJE
    # ==========================

    mensajes.insert_one({

        "conversacion_id": conversacion_id,

        "emisor": "padre",

        "mensaje": texto,

        "fecha": datetime.now(),

        "leido": False

    })


    print("Conversación:", conversacion_id)


    return redirect(

        url_for(

            "mensajes.chat",

            conversacion_id=str(conversacion_id)

        )

    )
# ==========================================================
# CHAT PADRE / DOCENTE
# ==========================================================

@mensajes_bp.route("/chat/<conversacion_id>")
def chat(conversacion_id):
    print("ID RECIBIDO:", conversacion_id)

    conversacion = conversaciones.find_one({

        "_id": ObjectId(conversacion_id)

    })


    if not conversacion:

        flash(
            "Conversación no encontrada",
            "danger"
        )

        return redirect("/")



    lista_mensajes = list(

        mensajes.find({

            "conversacion_id": ObjectId(conversacion_id)

        }).sort(

            "fecha",
            1

        )

    )

    print("===================================")
    print("CONVERSACION COMPLETA:")
    print(conversacion)
    print("ID:", conversacion.get("_id"))
    print("===================================")
    return render_template(

        "chat/chat.html",

        conversacion=conversacion,

        mensajes=lista_mensajes

    )


# ==========================================================
# FUNCIONES AUXILIARES
# ==========================================================

def obtener_docente():

    usuario = session.get("usuario")

    if not usuario:
        print("⚠️ No existe usuario en sesión")
        return None

    docente = docentes.find_one({
        "usuario": usuario
    })

    print("====================================")
    print("BUSCANDO DOCENTE")
    print("USUARIO:", usuario)
    print("DOCENTE:", docente)
    print("====================================")

    return docente


def obtener_estudiante():

    usuario = session.get("usuario")

    if not usuario:
        print("⚠️ No existe usuario en sesión")
        return None

    estudiante = estudiantes.find_one({
        "usuario": usuario
    })

    print("====================================")
    print("BUSCANDO ESTUDIANTE DEL PADRE")
    print("USUARIO:", usuario)
    print("ESTUDIANTE:", estudiante)
    print("====================================")

    return estudiante


def crear_conversacion(estudiante, docente):

    conversacion = conversaciones.find_one({
        "estudiante_id": estudiante["_id"],
        "docente_id": docente["_id"]
    })

    if conversacion:
        return conversacion

    nueva = {

        "estudiante_id": estudiante["_id"],

        "docente_id": docente["_id"],

        "estudiante": estudiante.get("nombre"),

        "docente": docente.get("nombre"),

        "fecha_creacion": datetime.now(),

        "ultima_actualizacion": datetime.now(),

        "ultimo_mensaje": "",

        "no_leidos_docente": 0,

        "no_leidos_padre": 0
    }

    resultado = conversaciones.insert_one(nueva)

    return conversaciones.find_one({
        "_id": resultado.inserted_id
    })
# ==========================================================
# BANDEJA DOCENTE
# ==========================================================

@mensajes_bp.route("/docente")
def bandeja_docente():

    docente = obtener_docente()

    if not docente:

        flash(
            "Docente no encontrado",
            "danger"
        )

        return redirect("/")

    # ======================================================
    # IDENTIFICADORES DEL DOCENTE
    # ======================================================

    docente_id = docente.get("_id")
    docente_codigo = docente.get("codigo")
    docente_usuario = docente.get("usuario")

    print("====================================")
    print("BANDEJA DOCENTE")
    print("DOCENTE:", docente.get("nombre"))
    print("ID:", docente_id)
    print("CODIGO:", docente_codigo)
    print("USUARIO:", docente_usuario)
    print("====================================")

    # ======================================================
    # BUSCAR CONVERSACIONES
    # ======================================================

    condiciones = []

    if docente_codigo:
        condiciones.append({
            "docente_id": docente_codigo
        })

    if docente_id:
        condiciones.append({
            "docente_id": docente_id
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
    # DEBUG
    # ======================================================

    print("====================================")
    print("TOTAL CONVERSACIONES:", len(lista))

    for c in lista:

        print("------------------------------------")
        print("ID:", c.get("_id"))
        print("ESTUDIANTE:", c.get("estudiante"))
        print("DOCENTE ID:", c.get("docente_id"))
        print("ULTIMO MENSAJE:", c.get("ultimo_mensaje"))
        print(
            "NO LEIDOS DOCENTE:",
            c.get("no_leidos_docente")
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
# RESPONDER MENSAJE
# ==========================================================

@mensajes_bp.route("/responder", methods=["POST"])
def responder():

    conversacion_id = request.form.get(
        "conversacion_id"
    )

    texto = request.form.get(
        "mensaje",
        ""
    ).strip()


    if not conversacion_id or not texto:

        flash(
            "Datos incompletos",
            "warning"
        )

        return redirect(
            request.referrer or "/"
        )


    try:

        conversacion_id_obj = ObjectId(
            conversacion_id
        )

    except Exception:

        flash(
            "ID de conversación inválido",
            "danger"
        )

        return redirect(
            request.referrer or "/"
        )


    conversacion = conversaciones.find_one({

        "_id": conversacion_id_obj

    })


    if not conversacion:

        flash(
            "Conversación no encontrada",
            "danger"
        )

        return redirect("/")


    rol = session.get("rol")


    # ======================================================
    # DOCENTE RESPONDE
    # ======================================================

    if rol == "docente":

        emisor = "docente"

        actualizar = {

            "ultimo_mensaje": texto,

            "ultima_actualizacion":
                datetime.now(),

            "no_leidos_padre": 1,

            "no_leidos_docente": 0

        }


    # ======================================================
    # PADRE RESPONDE
    # ======================================================

    elif rol == "padre":

        emisor = "padre"

        actualizar = {

            "ultimo_mensaje": texto,

            "ultima_actualizacion":
                datetime.now(),

            "no_leidos_docente": 1,

            "no_leidos_padre": 0

        }


    else:

        flash(
            "Usuario no autorizado",
            "danger"
        )

        return redirect("/")


    # ======================================================
    # GUARDAR MENSAJE
    # ======================================================

    mensajes.insert_one({

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

    conversaciones.update_one(

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
    print("MENSAJE ENVIADO")
    print("ROL:", rol)
    print("CONVERSACION:", conversacion_id)
    print("EMISOR:", emisor)
    print("MENSAJE:", texto)
    print("====================================")


    return redirect(

        url_for(

            "mensajes.chat",

            conversacion_id=
                conversacion_id

        )

    )


# ==========================================================
# BANDEJA DE MENSAJES DEL PADRE
# ==========================================================

@mensajes_bp.route("/padre")
def bandeja_padre():

    usuario = session.get("usuario")

    # ------------------------------------------
    # VERIFICAR SESIÓN
    # ------------------------------------------

    if not usuario:

        flash(
            "Debe iniciar sesión para ver sus mensajes.",
            "warning"
        )

        return redirect("/")


    # ------------------------------------------
    # BUSCAR ESTUDIANTE
    # ------------------------------------------

    estudiante = estudiantes.find_one({
        "usuario": usuario
    })


    print("====================================")
    print("BANDEJA PADRE")
    print("USUARIO:", usuario)
    print("ESTUDIANTE:", estudiante)
    print("====================================")


    # ------------------------------------------
    # VERIFICAR ESTUDIANTE
    # ------------------------------------------

    if not estudiante:

        flash(
            "No se encontró el estudiante asociado al padre.",
            "warning"
        )

        return redirect(
            url_for("estudiante.dashboard")
        )


    # ------------------------------------------
    # ID DEL ESTUDIANTE
    # ------------------------------------------

    estudiante_id = str(
        estudiante.get("_id")
    )


    # ------------------------------------------
    # OBTENER CONVERSACIONES
    # ------------------------------------------

    conversaciones_padre = list(

        conversaciones.find({

            "estudiante_id":
                estudiante_id

        }).sort(

            "ultima_actualizacion",
            -1

        )

    )


    # ------------------------------------------
    # DEBUG
    # ------------------------------------------

    print("====================================")
    print("ID ESTUDIANTE:", estudiante_id)
    print(
        "TOTAL CONVERSACIONES:",
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
            "ULTIMO MENSAJE:",
            conversacion.get("ultimo_mensaje")
        )

        print(
            "NO LEIDOS:",
            conversacion.get(
                "no_leidos_padre",
                0
            )
        )


    print("====================================")


    # ------------------------------------------
    # MOSTRAR BANDEJA DEL PADRE
    # ------------------------------------------

    return render_template(

        "mensaje/bandeja_padre.html",

        conversaciones=conversaciones_padre,

        estudiante=estudiante

    )# ==========================================================
# CONTADOR DE MENSAJES NO LEIDOS
# ==========================================================


@mensajes_bp.route("/contador")
def contador():



    rol = session.get(

        "rol"

    )


    usuario = session.get(

        "usuario"

    )



    total = 0




    if rol == "docente":


        docente = docentes.find_one({

            "usuario":

                usuario

        })



        if docente:


            total = conversaciones.count_documents({

                "docente_id":

                    docente["_id"],


                "no_leidos_docente":

                    {

                        "$gt":0

                    }

            })





    else:


        estudiante = obtener_estudiante()



        if estudiante:


            total = conversaciones.count_documents({

                "estudiante_id":

                    estudiante["_id"],


                "no_leidos_padre":

                    {

                        "$gt":0

                    }

            })




    return {

        "total":

            total

    }

 # ------------------------------------------
    # VOLVER AL DASHBOARD
    # ------------------------------------------

    return redirect("/estudiante/")


# ==========================================================
# MARCAR CONVERSACION LEIDA
# ==========================================================


@mensajes_bp.route(
    "/leer/<id>"
)
def marcar_leido(id):


    mensajes.update_many(

        {

            "conversacion_id":

                ObjectId(id)

        },


        {

            "$set":

            {

                "leido":

                    True

            }

        }

    )



    conversaciones.update_one(

        {

            "_id":

                ObjectId(id)

        },


        {

            "$set":

            {

                "no_leidos_docente":

                    0,


                "no_leidos_padre":

                    0

            }

        }

    )


    return redirect(

        request.referrer

    )



# ==========================================================
# ELIMINAR CONVERSACION
# ==========================================================


@mensajes_bp.route("/eliminar/<id>")
def eliminar(id):


    conversaciones.delete_one({

        "_id":

            ObjectId(id)

    })



    mensajes.delete_many({

        "conversacion_id":

            ObjectId(id)

    })


    flash(

        "Conversación eliminada",

        "success"

    )


    return redirect(

        request.referrer

    )
