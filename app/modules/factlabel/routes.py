import os
import uuid
from datetime import datetime
from flask import current_app, jsonify, make_response, request, send_from_directory
from flask_login import current_user, login_required

from app import db
from app.modules.factlabel import factlabel_bp
from app.modules.hubfile.models import HubfileViewRecord
from app.modules.hubfile.services import HubfileDownloadRecordService, HubfileService
from app.modules.factlabel.services import FactlabelService

# @factlabel_bp.route('/factlabel', methods=['GET'])
# def index():
#     return render_template('factlabel/index.html')


@factlabel_bp.route('/factlabel/view/<int:file_id>', methods=['GET'])
def view_factlabel(file_id):
    print(f'view_factlabel...')
    file = HubfileService().get_or_404(file_id)
    filename = file.name

    directory_path = f"uploads/user_{file.feature_model.data_set.user_id}/dataset_{file.feature_model.data_set_id}/"
    parent_directory_path = os.path.dirname(current_app.root_path)
    file_path = os.path.join(parent_directory_path, directory_path, filename)

    try:
        if os.path.exists(file_path):
            content = FactlabelService().get_characterization(file)
            user_cookie = request.cookies.get('view_cookie')
            if not user_cookie:
                user_cookie = str(uuid.uuid4())

            # Check if the view record already exists for this cookie
            existing_record = HubfileViewRecord.query.filter_by(
                user_id=current_user.id if current_user.is_authenticated else None,
                file_id=file_id,
                view_cookie=user_cookie
            ).first()

            if not existing_record:
                # Register file view
                new_view_record = HubfileViewRecord(
                    user_id=current_user.id if current_user.is_authenticated else None,
                    file_id=file_id,
                    view_date=datetime.now(),
                    view_cookie=user_cookie
                )
                db.session.add(new_view_record)
                db.session.commit()

            # Prepare response
            response = jsonify({'success': True, 'content': content})
            if not request.cookies.get('view_cookie'):
                response = make_response(response)
                response.set_cookie('view_cookie', user_cookie, max_age=60*60*24*365*2)
            return response
        else:
            return jsonify({'success': False, 'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    


# @factlabel_bp.route("/factlabel/show/<int:file_id>", methods=["GET"])
# def show_factlabel(file_id):
#     hubfile = HubfileService().get_or_404(file_id)
#     user_owner = hubfile.get_owner_user()
#     filename = hubfile.name

#     directory_path = f"uploads/user_{user_owner.id}/dataset_{hubfile.feature_model.data_set_id}/"
#     parent_directory_path = os.path.dirname(current_app.root_path)
#     file_path = os.path.join(parent_directory_path, directory_path)

#     user_cookie = hubfile_download_record_service.create_cookie(hubfile=hubfile)

#     resp = make_response(
#         send_from_directory(directory=file_path, path=filename, as_attachment=True)
#     )
#     resp.set_cookie("file_download_cookie", user_cookie)

#     return resp