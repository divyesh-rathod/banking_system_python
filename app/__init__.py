from flask import Flask
from .config import Config
from .database import init_db
from .routes import main
from .logging_config import setup_logging
from .tasks import init_scheduler

def create_app():
    # Set up logging
    setup_logging()
    
    # Initialize Flask app
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(Config)
    
    # Initialize database and register blueprints
    init_db(app)
    app.register_blueprint(main)
    
    # Initialize the scheduler
    init_scheduler(app)
    
    app.logger.info("Flask app initialized.")
    return app
