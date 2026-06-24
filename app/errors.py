"""Product-level error handlers, discovered by splent_framework's ErrorHandlerManager.

Each ``handle_<code>(app, e)`` overrides the framework default for that status.
Only 404 is customised here: API paths get a JSON body instead of the HTML page
(the rest fall back to the framework's render_template defaults).
"""
from flask import jsonify, render_template, request


def handle_404(app, e):
    app.logger.warning("Page Not Found: %s", str(e))
    if request.path.startswith("/api/"):
        return jsonify({"error": "Not found"}), 404
    return render_template("404.html"), 404
