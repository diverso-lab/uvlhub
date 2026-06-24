import logging
import uuid

from flask import jsonify, make_response, request

from app.features.factlabel import factlabel_bp
from app.features.factlabel.services import FactlabelNotReady, FactlabelService, InvalidFactlabel
from app.features.hubfile.services import HubfileService

logger = logging.getLogger(__name__)

VIEW_COOKIE = "view_cookie"
VIEW_COOKIE_MAX_AGE = 60 * 60 * 24 * 365 * 2  # two years

factlabel_service = FactlabelService()


@factlabel_bp.route("/factlabel/view/<int:file_id>", methods=["GET"])
def view_factlabel(file_id):
    hubfile = HubfileService().get_or_404(file_id)

    try:
        content = factlabel_service.parse_factlabel(hubfile)
    except FactlabelNotReady as exc:
        return jsonify({"success": False, "error": str(exc)}), 404
    except InvalidFactlabel as exc:
        return jsonify({"success": False, "error": str(exc)}), 500

    incoming_cookie = request.cookies.get(VIEW_COOKIE)
    user_cookie = incoming_cookie or str(uuid.uuid4())
    factlabel_service.record_view(hubfile, user_cookie)

    response = jsonify({"success": True, "content": content})
    if not incoming_cookie:
        response = make_response(response)
        response.set_cookie(VIEW_COOKIE, user_cookie, max_age=VIEW_COOKIE_MAX_AGE)
    return response
