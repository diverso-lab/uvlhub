from flask import render_template
from app.modules.hubfile import hubfile_bp


@hubfile_bp.route('/hubfile', methods=['GET'])
def index():
    return render_template('hubfile/index.html')
