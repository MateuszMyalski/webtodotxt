import os
import secrets
from .file import DbFile
from .user import Config, User
from .todos import Todos
from datetime import date


class WebTodoTxtConfig(Config):
    def __init__(self, directory) -> None:
        super().__init__(directory)

        if self._data.get("webtodotxt", None) is None:
            self._data["webtodotxt"] = {
                "api_token": "",
                "show_last_n_done_tasks": -1,
                "default_task": "",
                "quick_filters": {},
            }
            self._save()

        self._app_config = self._data["webtodotxt"]

    def set_token(self):
        self._app_config["api_token"] = secrets.token_urlsafe(32)
        self._save()
        return self.get_token()

    def get_token(self):
        return self._app_config.get("api_token", None)

    def set_default_task(self, string):
        self._app_config["default_task"] = string
        self._save()

    def get_default_task(self):
        return self._app_config.get("default_task", "")

    def set_show_last_n_done_tasks(self, n_tasks):
        self._app_config["show_last_n_done_tasks"] = n_tasks
        self._save()

    def get_show_last_n_done_tasks(self):
        return self._app_config.get("show_last_n_done_tasks", -1)

    def get_quick_filters(self):
        return self._app_config.get("quick_filters", {})

    def set_quick_filters(self, new_quick_filters: dict):
        quick_filters = self._app_config.get("quick_filters", None)
        if quick_filters is None:
            self._app_config.update({"quick_filters": {}})

        self._app_config["quick_filters"] = new_quick_filters
        self._save()


class AppUser(User):
    TODO_FILE_NAME = "todo.txt"
    APP_DIRECTORY = "webtodotxt"

    def __init__(self, id, user_directory):
        super().__init__(id, WebTodoTxtConfig(user_directory))

        self._app_path = os.path.join(user_directory, self.APP_DIRECTORY)

    def set_token(self):
        return self._config.set_token()

    def get_token(self):
        return self._config.get_token()

    def set_default_task(self, string):
        self._config.set_default_task(string)

    def get_default_task_constants(self):
        return {
            "date": date.today(),
            "user": self._config.get_username(),
            "name": self.full_name,
        }

    def get_default_task(self):
        return self._config.get_default_task()

    def get_default_task_formated(self):
        return self._config.get_default_task().format(
            **self.get_default_task_constants()
        )

    def set_show_last_n_done_tasks(self, n_tasks):
        self._config.set_show_last_n_done_tasks(n_tasks)

    def get_show_last_n_done_tasks(self):
        return self._config.get_show_last_n_done_tasks()

    def get_todo_file(self) -> DbFile:
        db_file = DbFile(os.path.join(self._app_path, self.TODO_FILE_NAME))
        if not db_file.exists():
            db_file.create()
        return db_file

    def get_todos(self) -> Todos:
        db_file = self.get_todo_file()

        return Todos(db_file)

    def get_quick_filters(self):
        return self._config.get_quick_filters()

    def set_quick_filters(self, quick_filters):
        self._config.set_quick_filters(quick_filters)


class Users:
    def __init__(self):
        self._users_db = {}

    def load(self, db_path: str) -> None:
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database path {db_path} does not exist.")

        with os.scandir(db_path) as entries:
            for entry in entries:
                user_directory = os.path.join(db_path, entry.name)
                if not Config.config_file_exists(user_directory):
                    continue

                user = AppUser(id=entry.name, user_directory=user_directory)

                self._users_db[user.id] = user

    def get(self, username) -> AppUser | None:
        return self._users_db.get(username, None)
