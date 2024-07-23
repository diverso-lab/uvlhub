from flask import render_template
from app.modules.recaptcha import recaptcha_bp


@recaptcha_bp.route('/recaptcha', methods=['GET'])
def index():
    return render_template('recaptcha/index.html')
