from flask import render_template
from app.modules.prueba import prueba_bp


@prueba_bp.route('/prueba', methods=['GET'])
def index():
    return render_template('prueba/index.html')
