from flask import request, render_template, flash, redirect, url_for
from flask_login import login_required

from app.team import team_bp


@team_bp.route('/team', methods=['GET'])
def index():
    return render_template('team/index.html')
