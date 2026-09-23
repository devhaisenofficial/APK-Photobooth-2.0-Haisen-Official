import os
from flask import Blueprint, render_template, request, current_app, session as flask_session
from app.models.session_model import PhotoSession
from app.models.admin_model import AppSetting

mobile_bp = Blueprint('mobile', __name__, template_folder='../../templates')

@mobile_bp.route('/mobile')
def index():
    code = request.args.get('code', '').strip()
    is_expired = False
    not_found = False

    flask_session['mobile_access'] = True
    if code:
        flask_session[f'gallery_access_{code}'] = True
        flask_session['allowed_gallery_code'] = code
        session = PhotoSession.query.filter_by(unique_code=code).first()
        if not session:
            not_found = True
        elif session.status == 'completed':
            is_expired = True

    storage_base = current_app.config.get(
        'PRIVATE_STORAGE_PATH',
        os.path.join(current_app.root_path, '..', 'storage')
    )
    template_dir = os.path.join(storage_base, 'templates')
    custom_templates = []
    if os.path.exists(template_dir):
        custom_templates = [f for f in sorted(os.listdir(template_dir)) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]

    active_tpl_setting = AppSetting.query.filter_by(key='active_custom_template').first()
    active_template = active_tpl_setting.value if active_tpl_setting else 'default'

    return render_template('mobile/index.html',
                           code=code,
                           is_expired=is_expired,
                           not_found=not_found,
                           active_template=active_template,
                           custom_templates=custom_templates)