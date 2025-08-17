from flask import render_template, request
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import (
    SubmitField,
    TextAreaField,
    validators,
)
from .auth import auth_display_login_form
from .extensions import users_db
from .models.accounts import AppUser
from datetime import date
import calendar


class AppendTaskForm(FlaskForm):
    task = TextAreaField("Add new task", [validators.Optional(strip_whitespace=True)])
    submit = SubmitField("Submit")


def _sort_by_done(tasks):
    done = list()
    undone = list()
    for task in tasks:
        if task.is_completed:
            done.append(task)
        else:
            undone.append(task)

    return (done, undone)


def _sort_by_prio_and_date(tasks):
    def _sort_func(t):

        created = t.get_creation_date()

        return (
            "Z" if t.get_priority() is None else t.get_priority(),
            (-created.toordinal() if isinstance(created, date) else float("-inf")),
        )

    return sorted(tasks, key=_sort_func)


def _count_passed_due(tasks):
    n = 0
    for task in tasks:
        if not task.is_completed and task.get_due_date() is not None:
            if task.get_due_date() < date.today():
                n += 1

    return n


def _sort_by_completion_date(tasks):
    def _sort_funct(t):
        return (
            -t.get_completion_date().toordinal()
            if t.get_completion_date()
            else float("-inf")
        )

    return sorted(tasks, key=_sort_funct)


def main_get():
    if not current_user.is_authenticated:
        return auth_display_login_form()

    requested_user: AppUser | None = users_db.get(current_user.id)

    if requested_user is None:
        return render_template("error.html", message="User not found.")

    todos = requested_user.get_todos()

    done, undone = _sort_by_done(todos.get_tasks())

    undone = _sort_by_prio_and_date(undone)
    done = _sort_by_completion_date(done)

    n_task_done = requested_user.get_show_last_n_done_tasks()
    if n_task_done >= 0:
        done = done[:n_task_done]

    form = AppendTaskForm()
    form.task.default = requested_user.get_default_task_formated()
    form.task.data = requested_user.get_default_task_formated()

    return render_template(
        "main.html",
        tasks_done=done,
        tasks_undone=undone,
        form=form,
        current_date=date.today(),
        calendar=calendar.month(date.today().year, date.today().month),
        full_name=requested_user.full_name,
        due_tasks=_count_passed_due(undone)
    )
