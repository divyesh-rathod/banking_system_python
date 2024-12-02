from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.sql import text
from .database import db  # Use the initialized db instance

scheduler = BackgroundScheduler()

def check_database_health(app, logger):
    """Function to check database health."""
    try:
        # Push the application context for database access
        with app.app_context():
            with db.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                logger.info("Database is healthy.")
    except Exception as e:
        logger.error(f"Database health check failed: {e}")

def init_scheduler(app):
    """Initialize the scheduler and add jobs."""
    scheduler.add_job(lambda: check_database_health(app, app.logger), 'interval', seconds=30)
    scheduler.start()
    app.logger.info("Background scheduler started.")
