from datetime import datetime
from flask import render_template, flash, get_flashed_messages, request
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    IntegerField,
    FieldList,
    FormField,
)
from wtforms import validators
from .models.accounts import AppUser
from .models.flash import FlashType, flash_collect
from .models.file import DbFile
from .extensions import users_db
from .token import generate_user_token


class FilterForm(FlaskForm):
    name = StringField("Name")
    value = StringField("Value")


class QuickFiltersForm(FlaskForm):
    filters = FieldList(FormField(FilterForm), min_entries=5, max_entries=5)
    submit = SubmitField("Save")

    def populate_default_filters(self, quick_filters: dict):
        for idx, (filter_name, filter_val) in enumerate(quick_filters.items()):
            if idx >= len(self.filters):
                break

            self.filters[idx].form.name.data = filter_name
            self.filters[idx].form.name.default = filter_name
            self.filters[idx].form.value.data = filter_val
            self.filters[idx].form.value.default = filter_val


class UserDetailsForm(FlaskForm):
    full_name = StringField("Full name", validators=[validators.DataRequired()])

    submit = SubmitField("Update details")

    def populate_default_full_name(self, full_name):
        self.full_name.data = full_name
        self.full_name.default = full_name


class XApiKeyGenerateForm(FlaskForm):
    token = StringField(
        "X-Api-Key Token",
        validators=[validators.ReadOnly()],
        default="First generate...",
    )
    submit = SubmitField("Generate x-api-key")


class ChangePasswordForm(FlaskForm):
    current_passw = PasswordField(
        "Current password", validators=[validators.DataRequired()]
    )
    new_passw = PasswordField("New password", validators=[validators.DataRequired()])
    confirm = PasswordField(
        "Confirm new password",
        validators=[
            validators.DataRequired(),
            validators.EqualTo("new_passw", message="Passwords must match"),
        ],
    )
    submit = SubmitField("Change password")


class AppSettingsForm(FlaskForm):
    default_task = StringField(
        "Default task",
    )
    show_n_last_done_tasks = IntegerField(
        "Show last N done tasks",
        description="Value '-1' means show all complete tasks",
        validators=[validators.NumberRange(min=-1)],
    )
    submit = SubmitField("Submit")

    def populate_default_default_task(self, line):
        self.default_task.data = line
        self.default_task.default = line

    def populate_default_show_n_last_done_tasks(self, number_of_tasks):
        self.show_n_last_done_tasks.data = number_of_tasks
        self.show_n_last_done_tasks.default = number_of_tasks


class ArchiveForm(FlaskForm):
    submit = SubmitField("Archive todo.txt")


def flash_collect():
    infos = [("info", msg) for msg in get_flashed_messages(False, FlashType.INFO.name)]

    errors = [
        ("error", msg) for msg in get_flashed_messages(False, FlashType.ERROR.name)
    ]

    return [*infos, *errors]


def _handle_details_change(user: AppUser, form: UserDetailsForm) -> None:
    if not form.validate_on_submit():
        flash("Request could not be validated.", FlashType.ERROR.name)

    user.set_full_name(form.full_name.data)

    flash("Details changed.", FlashType.INFO.name)


def _handle_token_generation(user: AppUser, form: XApiKeyGenerateForm) -> None:
    if not form.validate_on_submit():
        flash("Request could not be validated.", FlashType.ERROR.name)

    token = user.set_token()
    user_token = generate_user_token(token)

    form.token.default = user_token
    form.token.data = user_token

    flash("Token generated.", FlashType.INFO.name)


def _handle_password_change(user: AppUser, form: ChangePasswordForm) -> None:
    if not form.validate_on_submit():
        flash("Request could not be validated.", FlashType.ERROR.name)

    success = user.change_password(
        current=form.current_passw.data, new=form.new_passw.data
    )

    if success:
        flash("Password changed.", FlashType.INFO.name)
    else:
        flash("Invalid password.", FlashType.ERROR.name)


def _handle_app_settings_change(user: AppUser, form: AppSettingsForm) -> None:
    if not form.validate_on_submit():
        flash("Request could not be validated.", FlashType.ERROR.name)

    user.set_show_last_n_done_tasks(form.show_n_last_done_tasks.data)
    user.set_default_task(form.default_task.data)

    flash("App settings changed.", FlashType.INFO.name)


def _handle_archive_handle(user: AppUser, form: ArchiveForm) -> None:
    if not form.validate_on_submit():
        flash("Request could not be validated.", FlashType.ERROR.name)

    db_file = user.get_todo_file()

    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        db_file_archive = DbFile(db_file.get_path() + f".{timestamp}.archive")
        db_file_archive.create()
        db_file.copy_to(db_file_archive.get_path())
    except:
        flash("Cannot create archive!.", FlashType.ERROR.name)

    db_file.erase()

    flash("Archived.", FlashType.INFO.name)


def _handle_quick_filters_handle(user: AppUser, form: QuickFiltersForm):
    if not form.validate_on_submit():
        flash("Request could not be validated.", FlashType.ERROR.name)
        return

    quick_filters = {}
    for filter_form in form.filters:
        name = filter_form.form.name.data.strip()
        value = filter_form.form.value.data.strip()
        if name and value:
            quick_filters[name] = value

    user.set_quick_filters(quick_filters)
    flash("Quick filters updated.", FlashType.INFO.name)


def account_post():
    requested_user: AppUser | None = users_db.get(current_user.id)

    if requested_user is None:
        return render_template("error.html", message="User not found.")

    form_details = UserDetailsForm(prefix="details")
    form_change_password = ChangePasswordForm(prefix="password")
    form_api_token = XApiKeyGenerateForm(prefix="token")
    form_app_settings = AppSettingsForm(prefix="app")
    form_archive = ArchiveForm(prefix="archive")
    form_quick_filters = QuickFiltersForm(prefix="filters")

    if form_details.submit.data:
        _handle_details_change(requested_user, form_details)

    if form_change_password.submit.data:
        _handle_password_change(requested_user, form_change_password)

    if form_api_token.submit.data:
        _handle_token_generation(requested_user, form_api_token)

    if form_app_settings.submit.data:
        _handle_app_settings_change(requested_user, form_app_settings)

    if form_archive.submit.data:
        _handle_archive_handle(requested_user, form_archive)

    if form_quick_filters.submit.data:
        _handle_quick_filters_handle(requested_user, form_quick_filters)

    form_details.populate_default_full_name(requested_user.full_name)

    return render_template(
        "account_view.html",
        form_details=form_details,
        form_change_password=form_change_password,
        username=requested_user.username,
        form_api_token=form_api_token,
        host_url=request.host_url,
        form_app_settings=form_app_settings,
        form_archive=form_archive,
        form_quick_filters=form_quick_filters,
        infos=flash_collect(),
    )


def account_get():
    requested_user: AppUser | None = users_db.get(current_user.id)

    if requested_user is None:
        return render_template("error.html", message="User not found.")

    form_details = UserDetailsForm(prefix="details")
    form_details.populate_default_full_name(requested_user.full_name)

    form_change_password = ChangePasswordForm(prefix="password")

    form_api_token = XApiKeyGenerateForm(prefix="token")

    form_app_settings = AppSettingsForm(prefix="app")
    form_app_settings.populate_default_default_task(requested_user.get_default_task())
    form_app_settings.populate_default_show_n_last_done_tasks(
        requested_user.get_show_last_n_done_tasks()
    )

    form_archive = ArchiveForm(prefix="archive")

    form_quick_filters = QuickFiltersForm(prefix="filters")
    form_quick_filters.populate_default_filters(requested_user.get_quick_filters())

    return render_template(
        "account_view.html",
        form_details=form_details,
        form_change_password=form_change_password,
        username=requested_user.username,
        form_api_token=form_api_token,
        host_url=request.host_url,
        form_app_settings=form_app_settings,
        form_archive=form_archive,
        form_quick_filters=form_quick_filters,
        infos=flash_collect(),
    )
