import json
import logging
import uuid
from datetime import datetime

from flask import jsonify, make_response, request
from flask_login import current_user

from app import db
from app.modules.factlabel import factlabel_bp
from app.modules.hubfile.models import HubfileViewRecord
from app.modules.hubfile.services import HubfileService

logger = logging.getLogger(__name__)


@factlabel_bp.route("/factlabel/view/<int:file_id>", methods=["GET"])
def view_factlabel(file_id):
    file = HubfileService().get_or_404(file_id)

    try:
        if not file.factlabel_json:
            return jsonify({"success": False, "error": "FactLabel not ready yet"}), 404

        # 🔹 Convertir de string a dict
        try:
            content = json.loads(file.factlabel_json)
        except Exception:
            return (
                jsonify({"success": False, "error": "Invalid FactLabel JSON in DB"}),
                500,
            )

        # --- Registro de la vista ---
        user_cookie = request.cookies.get("view_cookie")
        if not user_cookie:
            user_cookie = str(uuid.uuid4())

        existing_record = HubfileViewRecord.query.filter_by(
            user_id=current_user.id if current_user.is_authenticated else None,
            file_id=file_id,
            view_cookie=user_cookie,
        ).first()

        if not existing_record:
            new_view_record = HubfileViewRecord(
                user_id=current_user.id if current_user.is_authenticated else None,
                file_id=file_id,
                view_date=datetime.now(),
                view_cookie=user_cookie,
            )
            db.session.add(new_view_record)
            db.session.commit()

        # --- Preparar respuesta ---
        response = jsonify({"success": True, "content": content})
        if not request.cookies.get("view_cookie"):
            response = make_response(response)
            response.set_cookie("view_cookie", user_cookie, max_age=60 * 60 * 24 * 365 * 2)
        return response

    except Exception as e:
        return (
            jsonify({"success": False, "error": f"Internal server error: {str(e)}"}),
            500,
        )
