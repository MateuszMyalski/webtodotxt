from flask import render_template, jsonify, request, redirect, url_for
from flask_login import current_user
from .auth import auth_display_login_form
from .extensions import users_db
from .main import AppendTaskForm
from pytodotxt import Task
from functools import wraps
import json


def with_todo_manager(json_errors=True):
    """Decorator to inject TodoManager into a route after auth check."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return auth_display_login_form()
            user = users_db.get(current_user.id)

            if not user:
                err = {"status": "NOK", "message": "Cannot load user"}
                return (
                    (jsonify(err), 400)
                    if json_errors
                    else render_template("error.html", message=err["message"])
                )

            todos = user.get_todos()
            return fn(todos, *args, **kwargs)

        return wrapper

    return decorator


@with_todo_manager(json_errors=False)
def crud_form_post(todos):
    form = AppendTaskForm()

    if not form.validate_on_submit():
        return render_template("error.html", message="Validation error.")

    try:
        task = Task(form.task.data)
        if not task.description:
            return redirect(url_for("main.index"))
    except:
        return render_template("error.html", message="Task parsing error.")

    todos.append_task(task)
    todos.save()

    return redirect(url_for("main.index"))


def crud_api_post(username):
    if request.headers.get("Content-type", "") != "application/json":
        return jsonify({"status": "Content-type nor supported."}), 400

    requested_user = users_db.get(username)

    if requested_user is None:
        return {"status": "NOK", "message": "Cannot load user"}

    try:
        user_request_data = json.loads(request.data.decode())
        task_line = user_request_data.get("task")

        task = Task(task_line)
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "Could not parse request.",
                    "received_content": f"{request.data.decode()}",
                    "exception:": f"{e}",
                }
            ),
            400,
        )

    todos = requested_user.get_todos()
    todos.append_task(task)
    todos.save()

    return jsonify({"status": "Ok"}), 200


@with_todo_manager()
def crud_put(todos, line_number):
    if request.headers.get("Content-type", "") != "application/json":
        return jsonify({"status": "NOK", "message": "Content-type not supported."}), 400

    try:
        line_number = int(line_number)
    except:
        return jsonify({"status": "NOK", "message": "Cannot parse line number."})

    task = todos.get_task(line_number)
    if task is None:
        return jsonify({"status": "NOK", "message": "Line number not found"})

    try:
        data = json.loads(request.data.decode())

        action = data["action"]

        if action == "toggle":
            if data["key"] == "done":
                new_task = task.toggle_done()
                if new_task is not None:
                    todos.append_task(new_task)

        elif action == "edit":
            if data["key"] == "line":
                task.parse(data["value"])

        todos.save()

    except:
        return jsonify({"status": "NOK", "message": "Cannot parse response"}), 400

    return jsonify({"status": "OK"}), 200


@with_todo_manager()
def crud_delete(todos, line_number):
    try:
        line_number = int(line_number)
    except:
        return jsonify({"status": "NOK", "message": "Cannot parse line number"}), 500

    try:
        todos.delete_task(line_number)
    except:
        jsonify({"status": "NOK"}), 500
        raise

    return jsonify({"status": "OK"}), 200


@with_todo_manager()
def crud_get(todos, line_number):
    try:
        line_number = int(line_number)
    except:
        return jsonify({"status": "NOK", "message": "Cannot parse line number."})

    task_line = todos.get_line(line_number)
    if task_line is None:
        return jsonify({"status": "NOK", "message": "Line number not found"})

    return jsonify({"status": "OK", "task": f"{task_line}"})
