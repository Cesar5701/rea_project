from flask import Blueprint, render_template, session
from flask_login import login_required

# Create a Blueprint for main routes
main_bp = Blueprint('main', __name__, template_folder='../templates')

@main_bp.before_app_request
def make_session_permanent():
    """
    Make the session permanent.
    This means the session will last for the time specified in PERMANENT_SESSION_LIFETIME.
    """
    session.permanent = True

@main_bp.route('/')
def index():
    """
    Route for the home page.
    """
    return render_template('index.html')

@main_bp.route('/webrtc')
@login_required
def webrtc():
    """
    Route for the WebRTC video conferencing page.
    Requires the user to be logged in.
    """
    return render_template('webrtc.html')
