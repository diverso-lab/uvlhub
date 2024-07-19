from flask import current_app, redirect, render_template, session, url_for
from flask_login import login_user
import app
from app.modules.auth.models import User
from app.modules.orcid import orcid_bp
from app.modules.orcid.models import Orcid
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

    # Obtener información disponible del perfil público de ORCID
    given_name = user_info.get('given_name', '')
    family_name = user_info.get('family_name', '')

    # Verificar si el ORCID iD ya está registrado en la tabla Orcid
    orcid_record = Orcid.query.filter_by(orcid_id=orcid_id).first()
    
    if orcid_record:
        # Si el registro existe, obtener el perfil del usuario asociado
        profile = UserProfile.query.filter_by(id=orcid_record.profile_id).first()
        if profile:
            user = User.query.get(profile.user_id)
            login_user(user)
            return redirect('/')
    else:
        # Registrar el ORCID iD en la tabla Orcid y crear usuario y perfil
        user = User()
        user.set_password(orcid_id)  # Usar el ORCID como contraseña
        db.session.add(user)
        db.session.commit()

        profile = UserProfile(
            user_id=user.id,
            name=given_name,
            surname=family_name
        )
        db.session.add(profile)
        db.session.commit()

        orcid_record = Orcid(
            orcid_id=orcid_id,
            profile_id=profile.id
        )
        db.session.add(orcid_record)
        db.session.commit()

        login_user(user)
        return redirect('/')
    