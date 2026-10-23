"""
Custom error handlers for SPLENT products.

You can override default framework error responses by defining
these functions. Each handler receives the Flask app and the error object.
uvlhub answers with its own pages (404.html, 500.html, beside 400.html and
401.html): the card uvlhub.io shows, in the product's skin. They have names
of their own, so theme's errors/404.html and errors/500.html, which other
products draw, are not shadowed. theme replaces the 404 handler as it
starts, so create_app registers handle_404 again once the features have
(_answer_not_found).
"""

from flask import render_template


def handle_404(app, e):
    app.logger.warning("Page Not Found: %s", str(e))
    return render_template("404.html"), 404


def handle_500(app, e):
    app.logger.error("Internal Server Error: %s", str(e))
    return render_template("500.html"), 500
