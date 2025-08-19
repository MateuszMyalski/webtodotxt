from flask import request, render_template, redirect, url_for, jsonify
from flask_login import login_required
from functools import wraps
from werkzeug import Response
from .extensions import bp, users_db, login_manager, app, csrf
from .auth import auth_authenticate_post, auth_logout
from .account import account_post, account_get
from .main import main_get
from .token import verify_user_token
from .crud import crud_form_post, crud_delete, crud_get, crud_put, crud_api_post
from .search import search_post, search_get

def handle_uncaught_exceptions(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            if app.debug:
                import traceback

                traceback.print_exc()

            return render_template("error.html", message=str(e))

    return wrapper


def api_key_required(view_function):
    @wraps(view_function)
    def wrapper(*args, **kwargs):
        x_api_key = request.headers.get("X-API-Key")
        user = users_db.get(kwargs["username"])

        if user is None:
            return jsonify({"status": "Unauthorized"}), 401

        if x_api_key is None:
            return jsonify({"status": "Unauthorized"}), 401

        if verify_user_token(x_api_key) is None:
            return jsonify({"status": "Unauthorized"}), 401

        return view_function(*args, **kwargs)

    return wrapper


@login_manager.unauthorized_handler
def handle_needs_login():
    return redirect(url_for("main.index"))


@bp.route("/", methods=("GET", "POST"))
@handle_uncaught_exceptions
def index() -> str | Response:
    if request.method == "GET":
        return main_get()

    if request.method == "POST":
        return auth_authenticate_post()

    return redirect(url_for("main.index"))


@bp.route("/task/", defaults={"line_number": None}, methods=("POST",))
@bp.route("/task/<int:line_number>", methods=("POST", "DELETE", "GET", "PUT"))
@handle_uncaught_exceptions
@login_required
def internal_crud(line_number):
    if request.method == "POST":
        return crud_form_post()
    if request.method == "PUT":
        return crud_put(line_number)
    if request.method == "DELETE":
        return crud_delete(line_number)
    if request.method == "GET":
        return crud_get(line_number)

    return redirect(url_for("main.index"))

@bp.route("/api/v1/<username>/task", methods=("POST",))
@api_key_required
@csrf.exempt
def todo_append_api(username):
    return crud_api_post(username)


@bp.route("/logout", methods=("GET", "POST"))
@handle_uncaught_exceptions
@login_required
def logout():
    return auth_logout()


@bp.route("/account/view", methods=("GET", "POST"))
@handle_uncaught_exceptions
@login_required
def account():
    if request.method == "POST":
        return account_post()

    if request.method == "GET":
        return account_get()

    return render_template("404.html")

@bp.route("/search", methods=("GET", "POST"))
@handle_uncaught_exceptions
@login_required
def search():
    if request.method == "POST":
        return search_post()

    if request.method == "GET":
        return search_get()

    return render_template("404.html")
