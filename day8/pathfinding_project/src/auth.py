from functools import wraps

from flask import flash, redirect, request, session, url_for


def is_editor_authenticated() -> bool:
    return session.get("editor_authenticated") is True


def editor_required(view_function):
    @wraps(view_function)
    def wrapped(*args, **kwargs):
        if not is_editor_authenticated():
            flash("Editor login required.", "error")
            return redirect(
                url_for("editor_login", next=request.path)
            )
        return view_function(*args, **kwargs)

    return wrapped
