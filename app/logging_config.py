import logging

def setup_logging():
    # Configure the root logger
    logging.basicConfig(
        # Set the logging level to DEBUG (captures all levels of log messages)
        level=logging.DEBUG,
        
        # Define the format for log messages:
        # timestamp - log level - message
        format="%(asctime)s - %(levelname)s - %(message)s",
        
        # Specify handlers for log output:
        handlers=[
            # FileHandler: writes log messages to a file named "app.log"
            logging.FileHandler("app.log"),
            
            # StreamHandler: outputs log messages to the console
            logging.StreamHandler()
        ]
    )
    
    # Log a message indicating that the logging setup is complete
    # This message will be written to both the file and the console
    logging.getLogger().info("Logging is set up.")
