"""
Custom logging configuration for this SPLENT product.

This function allows the product to override the default logging setup
provided by the framework. It will be called automatically by the
LoggingManager during application initialization if present.
"""

import logging


def configure_logging(app):
    """
    Configure the logging behavior for this product.

    This function is detected and invoked by the SPLENT LoggingManager.
    You can modify log levels, handlers, and formats as needed.
    """
    # Set the global log level
    app.logger.setLevel(logging.DEBUG)

    # Create a stream handler (logs to console)
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)

    # Define the log format
    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)

    # Attach the handler to the app's logger
    app.logger.addHandler(handler)
