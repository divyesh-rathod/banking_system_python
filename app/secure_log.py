import hashlib

# Global variable to store the hash of the last log entry
last_log_hash = None

def tamper_proof_log(logger, level, message):
    """
    Log a message with tamper-proofing by chaining log hashes.

    Args:
        logger (logging.Logger): The logger instance to use.
        level (str): The logging level ('info', 'warning', 'exception', etc.).
        message (str): The log message to log.
    """
    global last_log_hash

    # Combine the message with the previous hash
    if last_log_hash:
        combined_message = f"{last_log_hash} - {message}"
    else:
        combined_message = message

    # Compute the current hash
    current_hash = hashlib.sha256(combined_message.encode('utf-8')).hexdigest()

    # Log the message along with the current hash
    log_entry = f"{combined_message} - HASH: {current_hash}"
    if level == 'info':
        logger.info(log_entry)
    elif level == 'warning':
        logger.warning(log_entry)
    elif level == 'exception':
        logger.exception(log_entry)
    else:
        logger.debug(log_entry)  # Fallback to debug for unspecified levels

    # Update the last log hash
    last_log_hash = current_hash
