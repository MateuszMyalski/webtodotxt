import os
import flask_login
import secrets
import tomllib
import tomli_w
from .file import DbFile
from werkzeug.security import check_password_hash, generate_password_hash
from .todos import Todos
from datetime import date


class Config:
    CONFIG_FILE_NAME = "config.toml"

    def __init__(self, db_file: DbFile) -> None:
        self._db_file = db_file
        self._data = self._load()

    def _load(self) -> dict:
        if not self._db_file.exists():
            raise FileNotFoundError(f"Missing config: {self._db_file.get_path()}")
        with open(self._db_file.get_path(), "rb") as f:
            return tomllib.load(f)

    def _save(self) -> None:
        with open(self._db_file.get_path(), "wb") as f:
            tomli_w.dump(self._data, f)

    def get_username(self) -> str:
        return self._data["user"]["username"]

    def get_full_name(self) -> str:
        return self._data["user"].get("full_name", "")

    def set_full_name(self, full_name: str) -> None:
        self._data["user"]["full_name"] = full_name
        self._save()

    def get_password_hash(self) -> str:
        return self._data["user"]["password_hash"]

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.get_password_hash(), password)

    def change_password(self, current_password: str, new_password: str) -> bool:
        if not self.check_password(current_password):
            return False

        self._data["user"]["password_hash"] = generate_password_hash(new_password)
        self._save()

        return True


class WebTodoTxtConfig(Config):
    def __init__(self, db_file: DbFile) -> None:
        super().__init__(db_file)
        if self._data.get("webtodotxt", None) is None:
            self._data["webtodotxt"] = {
                "api_token": "",
                "show_last_n_done_tasks": -1,
                "default_task": "",
            }
            self._save()

    def set_token(self):
        self._data["webtodotxt"]["api_token"] = secrets.token_urlsafe(32)
        self._save()
        return self.get_token()

    def get_token(self):
        return self._data["webtodotxt"].get("api_token", None)

    def set_default_task(self, string):
        self._data["webtodotxt"]["default_task"] = string
        self._save()

    def get_default_task(self):
        return self._data["webtodotxt"].get("default_task", "")

    def set_show_last_n_done_tasks(self, n_tasks):
        self._data["webtodotxt"]["show_last_n_done_tasks"] = n_tasks
        self._save()

    def get_show_last_n_done_tasks(self):
        return self._data["webtodotxt"].get("show_last_n_done_tasks", -1)


class ConfigCreator(Config):
    def __init__(self, db_file: DbFile):
        if not os.path.exists(db_file._dir):
            raise FileNotFoundError(f"Provided dir does not exist: {db_file._dir}")

        self._data = {
            "user": {
                "username": "",
                "full_name": "",
                "active": True,
                "password_hash": "",
            },
            "webtodotxt": {
                "api_token": "",
                "show_last_n_done_tasks": "",
                "default_task": "",
            },
        }

        # Do not overwrite config that already exists
        if not db_file.exists():
            with open(db_file.get_path(), "wb") as f:
                tomli_w.dump(self._data, f)

        super().__init__(db_file)

    def set_username(self, username: str):
        self._data["user"]["username"] = username
        self._save()

    def set_password(self, password: str):
        self._data["user"]["password_hash"] = generate_password_hash(password)
        self._save()

    def generate_api_token(self) -> str:
        token = secrets.token_urlsafe(32)
        self._data["webtodotxt"]["api_token"] = token
        self._save()
        return token


class User(flask_login.UserMixin):
    TODO_FILE_NAME = "todo.txt"
    APP_DIRECTORY = "webtodotxt"

    def __init__(self, id, config: WebTodoTxtConfig):
        self.id = id
        self._config = config
        self._user_directory = ""
        self._app_path = ""

    def set_user_directory(self, directory):
        self._user_directory = directory
        self._app_path = os.path.join(self._user_directory, self.APP_DIRECTORY)

    @property
    def username(self):
        return self._config.get_username()

    @property
    def full_name(self):
        return self._config.get_full_name()

    def check_password(self, password: str) -> bool:
        return self._config.check_password(password)

    def set_password(self, current: str, new: str) -> bool:
        return self._config.change_password(current, new)

    def set_full_name(self, name: str):
        self._config.set_full_name(name)

    def get_id(self):
        return self.id

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


class Users:
    def __init__(self):
        self._users_db = {}

    def load(self, db_path: str) -> None:
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database path {db_path} does not exist.")

        with os.scandir(db_path) as entries:
            for entry in entries:
                user_cfg_file = DbFile(
                    os.path.join(db_path, entry.name, Config.CONFIG_FILE_NAME)
                )

                user = self._load_user(user_cfg_file)
                if user is None:
                    continue

                self._users_db[user.id] = user
                user.set_user_directory(os.path.join(db_path, entry.name))

    def _load_user(self, db_file: DbFile) -> User | None:
        if not db_file.exists():
            return None

        config = WebTodoTxtConfig(db_file)
        user = User(id=config.get_username(), config=config)

        return user

    def get(self, username) -> User | None:
        return self._users_db.get(username, None)
