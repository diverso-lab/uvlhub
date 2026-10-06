"""
Custom error handlers for SPLENT products.

You can override default framework error responses by defining
these functions. Each handler receives the Flask app and the error object.
The templates live in the theme, so the pages wear the product's skin; a
product that wants its own can shadow errors/404.html in its templates.
"""

from flask import render_template


def handle_404(app, e):
    app.logger.warning("Page Not Found: %s", str(e))
    return render_template("errors/404.html"), 404


def handle_500(app, e):
    app.logger.error("Internal Server Error: %s", str(e))
    return render_template("errors/500.html"), 500
