from functools import wraps
from flask import session, redirect, url_for, flash

def role_required(*roles):

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):

            if "rol" not in session:
                flash("Debe iniciar sesión", "danger")
                return redirect(url_for("login"))

            if session.get("rol") not in roles:
                flash("Acceso no permitido", "danger")
                return redirect(url_for("login"))

            return func(*args, **kwargs)

        return wrapper

    return decorator