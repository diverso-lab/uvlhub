import logging
from logging.handlers import RotatingFileHandler


class LoggingManager:
    def __init__(self, app):
        self.app = app

    def setup_logging(self):
        # Configure log format
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        # Configure the log file with file rotation
        file_handler = RotatingFileHandler("app.log", maxBytes=10240, backupCount=10)
        file_handler.setLevel(logging.ERROR)
        file_handler.setFormatter(formatter)

        # Add handler to app logger
        self.app.logger.addHandler(file_handler)

        # Configure console log if necessary
        if self.app.debug:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            stream_handler.setFormatter(formatter)
            self.app.logger.addHandler(stream_handler)

        # Set the overall log level
        self.app.logger.setLevel(logging.INFO)
