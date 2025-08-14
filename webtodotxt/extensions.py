from flask import Flask
from flask_wtf import CSRFProtect
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import Blueprint
from .models.accounts import Users

app = Flask(__name__, instance_relative_config=True)

login_manager = LoginManager()

bp = Blueprint("main", __name__)

csrf = CSRFProtect(app)

users_db = Users()

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["50 per minute"],
    storage_uri="memory://",
    strategy="fixed-window"
)
