import os
import sqlite3
from datetime import timedelta
from flask import Flask, request, current_app
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import LoginManager, current_user

# Import the base configuration class from our new config file.
from config import Config

# Since other modules need access to extensions, we initialize them here
# globally but without an app instance. They will be bound to the app
# inside the factory function.
login_manager = LoginManager()
# We can set the login view here, which is the endpoint name for the login route.
socketio = SocketIO()

# --- Database Helper ---
def get_conn():
    """
    Connects to the database specified in the app's configuration.
    This function requires an active application context to access `current_app`.
    """
    conn = sqlite3.connect(current_app.config['DATABASE_URL'])
    conn.row_factory = sqlite3.Row
    return conn

def create_app(config_class=Config):
    """
    Creates and configures an instance of the Flask application.
    This function implements the 'Application Factory' pattern, which allows
    for creating multiple app instances with different configurations.
    """
    app = Flask(__name__)
    
    # Load configuration from the provided config class object.
    app.config.from_object(config_class)

    # --- Initialize Extensions ---
    # Bind the extension instances to the created app.
    login_manager.init_app(app)
    socketio.init_app(app)

    # --- User Loader for Flask-Login ---
    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        """
        Loads a user from the database given its ID.
        This function is used by Flask-Login to manage user sessions.
        """
        # We need an app context to connect to the database.
        with app.app_context():
            conn = get_conn()
            user_data = conn.execute("SELECT id, email, role FROM usuarios WHERE id = ?", (user_id,)).fetchone()
            conn.close()
            if user_data:
                return User(id=user_data['id'], email=user_data['email'], role=user_data['role'])
        return None
    
    # Set the login view, which is the endpoint name for the login route.
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
        """Handles a user joining a room."""
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
        
        # Send the list of existing peers to the new user.
        existing_peers = rooms[room]
        emit('existing_peers', existing_peers)
        
        # Add the new user to our room tracking and notify others.
        rooms[room][sid] = username
        # Notify other users in the room that a new peer has joined.
        emit('peer_joined', {'sid': sid, 'username': username}, to=room, include_self=False)

    @socketio.on('leave')
    def on_leave(data):
        """Handles a user leaving a room."""
        room = data.get('room')
        sid = request.sid
        leave_room(room)
        if room in rooms and sid in rooms[room]:
            username = rooms[room].pop(sid)
            # Notify other users in the room that a peer has left.
            emit('peer_left', {'sid': sid, 'username': username}, to=room, include_self=False)

    @socketio.on('signal')
    def on_signal(data):
        """Forwards a WebRTC signaling message to a specific user."""
        if not current_user.is_authenticated:
            return
            
        target_sid = data['target_sid']
        caller_sid = request.sid
        signal_data = data['signal']
        
        # Send the signal to the target user's room.
        emit('signal', {
            'caller_sid': caller_sid,
            'signal': signal_data,
            'caller_username': current_user.username
        }, room=target_sid)

    @socketio.on('disconnect')
    def on_disconnect():
        """Handles a user disconnecting from the server."""
        sid = request.sid
        # Find the room the user was in and notify others of their departure.
        for room, sids_with_users in list(rooms.items()):
            if sid in sids_with_users:
                username = sids_with_users.pop(sid)
                emit('peer_left', {'sid': sid, 'username': username}, to=room)
                break
                
    return app, socketio

