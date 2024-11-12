from flask import Flask
from .config import Config
from .database import init_db
from .routes import main
from .logging_config import setup_logging  # Import the logging setup function

def create_app():
    # Set up logging
    setup_logging()
    
    # Initialize Flask app
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(Config)
    
    # Initialize database and register blueprints
    init_db(app)
    app.register_blueprint(main)

    app.logger.info("Flask app initialized.")  # Example log entry

    return app