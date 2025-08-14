from .extensions import login_manager, users_db, app
from .routes import bp


def create_app(config_class=None):
    if config_class:
        app.config.from_object(config_class)
    else:
        app.config.from_pyfile("config.py", silent=True)

    login_manager.init_app(app)

    users_db.load(app.config["ACCOUNTS_DB_DIRECTORY_PATH"])

    app.register_blueprint(bp)

    return app
