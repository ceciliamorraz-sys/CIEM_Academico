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



    # ======================================================
    # CASO 2: RESPONDER CONVERSACIÓN EXISTENTE
    # ======================================================


    if rol == "docente":

        emisor = "docente"


        actualizar = {

            "no_leidos_estudiante": 1,

            "ultima_actualizacion": datetime.now(),

            "ultimo_mensaje": mensaje

        }



    else:

        emisor = "estudiante"


        actualizar = {

            "no_leidos_docente": 1,

            "ultima_actualizacion": datetime.now(),

            "ultimo_mensaje": mensaje

        }




    mensajes.insert_one({

        "conversacion_id": ObjectId(conversacion_id),

        "emisor": emisor,

        "mensaje": mensaje,

        "fecha": datetime.now(),

        "leido": False

    })




    conversaciones.update_one(

        {

            "_id": ObjectId(conversacion_id)

        },

        {

            "$set": actualizar

        }

    )



    return redirect(

        url_for(

            "mensajes.chat",

            conversacion_id=conversacion_id

        )

    )
# ==========================================================
# RESPONDER MENSAJE
# ==========================================================

@mensajes_bp.route("/responder", methods=["POST"])
def responder():

    conversacion_id = request.form.get("conversacion_id")
    texto = request.form.get("mensaje")

    if not conversacion_id or not texto:

        flash("Datos incompletos", "warning")
        return redirect(request.referrer)

    rol = session.get("rol")

    if rol == "docente":

        emisor = "docente"

        actualizar = {
            "ultimo_mensaje": texto,
            "ultima_actualizacion": datetime.now(),
            "no_leidos_padre": 1,
            "no_leidos_docente": 0
        }

    else:

        emisor = "padre"

        actualizar = {
            "ultimo_mensaje": texto,
            "ultima_actualizacion": datetime.now(),
            "no_leidos_docente": 1,
            "no_leidos_padre": 0
        }

    mensajes.insert_one({

        "conversacion_id": ObjectId(conversacion_id),
        "emisor": emisor,
        "mensaje": texto,
        "fecha": datetime.now(),
        "leido": False

    })

    conversaciones.update_one(

        {"_id": ObjectId(conversacion_id)},

        {"$set": actualizar}

    )

    return redirect(
        url_for(
            "mensajes.chat",
            conversacion_id=conversacion_id
        )
    )
# ==========================================================
# FUNCIONES AUXILIARES
# ==========================================================


def obtener_docente():

    usuario = session.get("usuario")


    if not usuario:

        return None



    docente = docentes.find_one({

        "usuario": usuario

    })


    return docente





def obtener_estudiante():

    usuario = session.get("usuario")


    if not usuario:

        return None



    estudiante = estudiantes.find_one({

        "padre": {

            "$regex": usuario,

            "$options": "i"

        }

    })


    return estudiante





def crear_conversacion(estudiante, docente):


    conversacion = conversaciones.find_one({

        "estudiante_id": estudiante["_id"],

        "docente_id": docente["_id"]

    })


    if conversacion:

        return conversacion



    nueva = {


        "estudiante_id":

            estudiante["_id"],



        "docente_id":

            docente["_id"],



        "estudiante":

            estudiante.get("nombre"),



        "docente":

            docente.get("nombre"),



        "fecha_creacion":

            datetime.now(),



        "ultima_actualizacion":

            datetime.now(),



        "ultimo_mensaje":

            "",



        "no_leidos_docente":

            0,



        "no_leidos_padre":

            0

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




    lista = list(

    conversaciones.find({

        "docente_id": docente["codigo"]

    }).sort(

        "ultima_actualizacion",

        -1

    )

)



    return render_template(

        "docente/mensajes.html",

        conversaciones=lista,

        docente=docente

    )





# ==========================================================
# BANDEJA PADRE
# ==========================================================


@mensajes_bp.route("/padre")
def bandeja_padre():

    estudiante = obtener_estudiante()

    if not estudiante:

        flash(
            "No se encontró estudiante",
            "danger"
        )

        return redirect("/")


    lista = list(

        conversaciones.find({

            "estudiante_id": estudiante["_id"]

        }).sort(

            "ultima_actualizacion",
            -1

        )

    )


    return render_template(
        "estudiante/mensajes.html",
        conversaciones=lista,
        estudiante=estudiante
    )

# ==========================================================
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


@mensajes_bp.route(
    "/eliminar/<id>"
)
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
