from flask import current_app, redirect, render_template, session, url_for
from flask_login import login_user
import app
from app.modules.auth.models import User
from app.modules.orcid import orcid_bp
from app.modules.orcid.services import OrcidService
from app.modules.profile.models import UserProfile
from app import db

@orcid_bp.before_app_request
def before_request():
    current_app.orcid_service = OrcidService()

@orcid_bp.route('/orcid/login')
def login():
    redirect_uri = url_for('orcid.authorize', _external=True, _scheme='https')
    return current_app.orcid_service.orcid_client.authorize_redirect(redirect_uri)

@orcid_bp.route('/orcid/authorize')
def authorize():
    token = current_app.orcid_service.orcid_client.authorize_access_token()
    resp = current_app.orcid_service.orcid_client.get('https://orcid.org/oauth/userinfo', token=token)
    user_info = resp.json()
    
    orcid_id = user_info['sub']
    user = User.query.join(UserProfile).filter(UserProfile.orcid == orcid_id).first()
    
    if not user:
        # Crear un nuevo usuario y perfil
        user = User(email=user_info.get('email'))
        db.session.add(user)
        db.session.commit()
        
        profile = UserProfile(
            user_id=user.id,
            orcid=orcid_id,
            name=user_info.get('name', ''),
            surname=user_info.get('surname', ''),
            affiliation=user_info.get('affiliation', '')
        )
        profile.save()
    
    login_user(user)
    return redirect('/')
