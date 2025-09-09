import os
import sqlite3
from datetime import timedelta
from flask import Flask, request
from dotenv import load_dotenv
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import LoginManager, current_user

# Since the models, routes, and other modules need access to extensions like 
# socketio and login_manager, we initialize them here but without an app instance.
login_manager = LoginManager()
# We can set the login view here, which is the endpoint name for the login route.
socketio = SocketIO()

# --- Database Helper ---
def get_conn():
    # The database file is now relative to the instance folder, which is outside the app package.
    conn = sqlite3.connect(os.getenv("DATABASE_URL", "rea.db"))
    conn.row_factory = sqlite3.Row
    return conn

def create_app(debug=False):
    """Create an application."""
    load_dotenv()
    app = Flask(__name__)
    app.config['DEBUG'] = debug
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "devsecret")
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=6)

    # --- Initialize Extensions ---
    login_manager.init_app(app)
    socketio.init_app(app)

    # --- User Loader for Flask-Login ---
    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        conn = get_conn()
        user_data = conn.execute("SELECT id, email, role FROM usuarios WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        if user_data:
            return User(id=user_data['id'], email=user_data['email'], role=user_data['role'])
        return None
    
    login_manager.login_view = 'auth.login'

    # --- Register Blueprints ---
    from .routes import auth, main, resources
    app.register_blueprint(auth.auth_bp)
    app.register_blueprint(main.main_bp)
    app.register_blueprint(resources.resources_bp)

    # --- Socket.IO Handlers ---
    rooms = {} 

    @socketio.on('join')
    def on_join(data):
        room = data['room']
        sid = request.sid
        # It's possible current_user is not available if the connection happens
        # before the session is fully established.
        if not current_user.is_authenticated:
            return
        username = current_user.username
        join_room(room)
        if room not in rooms:
            rooms[room] = {}
        existing_peers = rooms[room]
        emit('existing_peers', existing_peers)
        rooms[room][sid] = username
        emit('peer_joined', {'sid': sid, 'username': username}, to=room, include_self=False)

    @socketio.on('leave')
    def on_leave(data):
        room = data.get('room')
        sid = request.sid
        leave_room(room)
        if room in rooms and sid in rooms[room]:
            username = rooms[room].pop(sid)
            emit('peer_left', {'sid': sid, 'username': username}, to=room, include_self=False)

    @socketio.on('signal')
    def on_signal(data):
        if not current_user.is_authenticated:
            return
        target_sid = data['target_sid']
        caller_sid = request.sid
        signal_data = data['signal']
        emit('signal', {
            'caller_sid': caller_sid,
            'signal': signal_data,
            'caller_username': current_user.username
        }, room=target_sid)

    @socketio.on('disconnect')
    def on_disconnect():
        sid = request.sid
        for room, sids_with_users in list(rooms.items()):
            if sid in sids_with_users:
                username = sids_with_users.pop(sid)
                emit('peer_left', {'sid': sid, 'username': username}, to=room)
                break
                
    return app, socketio
