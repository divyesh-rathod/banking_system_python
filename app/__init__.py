from flask import Flask
from .config import Config
from .database import init_db
from .routes import main


def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(Config)
    init_db(app)
    app.register_blueprint(main)
    return app
