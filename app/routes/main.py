from flask import Blueprint, render_template, session
from flask_login import login_required

main_bp = Blueprint('main', __name__, template_folder='../templates')

@main_bp.before_app_request
def make_session_permanent():
    session.permanent = True

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/webrtc')
@login_required
def webrtc():
    return render_template('webrtc.html')
