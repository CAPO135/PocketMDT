import logging
import os
from datetime import datetime

def setup_logger(name="POCKET_MDT"):
    logger=logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Create logs directory if it doesn't exist
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # Create a unique log file name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"{logs_dir}/pocket_mdt_{timestamp}.log"

    # Console handler
    ch=logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # File handler for tracing
    fh=logging.FileHandler(log_filename)
    fh.setLevel(logging.DEBUG)

    formatter=logging.Formatter("[%(asctime)s] [%(levelname)s] --- [%(message)s]")
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    if not logger.hasHandlers():
        logger.addHandler(ch)
        logger.addHandler(fh)

    return logger



logger=setup_logger()

