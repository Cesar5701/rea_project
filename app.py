import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from ipfs_client import upload_to_ipfs
from nlp_utils import generar_embedding, clasificar_texto, embedding_to_blob, blob_to_embedding

load_dotenv()
DB = "rea.db"
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "devsecret")
app.debug = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
socketio = SocketIO(app)

# Configuración de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    conn = get_conn()
    user_data = conn.execute("SELECT id, username, role FROM usuarios WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if user_data:
        return User(id=user_data['id'], username=user_data['username'], role=user_data['role'])
    return None

def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

# --- Rutas Principales y de Autenticación ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_conn()
        user_exists = conn.execute("SELECT id FROM usuarios WHERE username = ?", (username,)).fetchone()
        if user_exists:
            flash('El nombre de usuario ya existe.', 'error')
            conn.close()
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password)
        conn.execute("INSERT INTO usuarios (username, password_hash) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        conn.close()
        flash('¡Registro exitoso! Por favor, inicia sesión.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_conn()
        user_data = conn.execute("SELECT id, username, password_hash, role FROM usuarios WHERE username = ?", (username,)).fetchone()
        conn.close()
        if user_data and check_password_hash(user_data['password_hash'], password):
            user = User(id=user_data['id'], username=user_data['username'], role=user_data['role'])
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos.', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# --- Rutas de la Aplicación ---

@app.route('/webrtc')
@login_required
def webrtc():
    return render_template('webrtc.html')

@app.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        enlace_manual = request.form.get('enlace', '').strip()
        categoria_manual = request.form.get('categoria', '').strip() or None
        cid = None
        gateway_url = enlace_manual or None
        filename = None
        file = request.files.get('archivo')
        if file and file.filename:
            content = file.read()
            filename = file.filename
            try:
                cid, gateway_url = upload_to_ipfs(content, filename)
            except Exception as e:
                flash(f"Error subiendo a IPFS: {e}", "error")
                return redirect(request.url)
        texto_para_clasificar = f"{titulo} {descripcion}"
        categoria_detectada = categoria_manual or clasificar_texto(texto_para_clasificar)
        emb_vec = generar_embedding(texto_para_clasificar)
        emb_blob = embedding_to_blob(emb_vec)
        conn = get_conn()
        conn.execute("""
            INSERT INTO recursos (titulo, descripcion, categoria, enlace, cid, filename, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (titulo, descripcion, categoria_detectada, gateway_url, cid, filename, emb_blob))
        conn.commit()
        conn.close()
        flash("Recurso guardado y clasificado: " + categoria_detectada, "success")
        return redirect(url_for('recursos'))
    return render_template('nuevo.html')

@app.route('/recursos')
@login_required
def recursos():
    conn = get_conn()
    recursos = conn.execute("SELECT * FROM recursos ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("recursos.html", recursos=recursos)

@app.route('/buscar_semantico', methods=['GET', 'POST'])
@login_required
def buscar_semantico():
    if request.method == 'POST':
        q = request.form.get('q', '').strip()
        top_k = int(request.form.get('k', 5))
        q_emb = generar_embedding(q)
        conn = get_conn()
        rows = conn.execute("SELECT id, titulo, descripcion, categoria, enlace, cid, embedding FROM recursos").fetchall()
        conn.close()
        import numpy as np
        results = []
        for r in rows:
            if not r["embedding"]: continue
            try:
                emb_stored = blob_to_embedding(r["embedding"])
                cos = float(np.dot(q_emb, emb_stored) / (np.linalg.norm(q_emb) * np.linalg.norm(emb_stored) + 1e-9))
                results.append({**dict(r), "score": cos})
            except:
                continue
        results_sorted = sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]
        return render_template("resultados_busqueda.html", resultados=results_sorted, query=q)
    return render_template('buscar_semantico.html')

# --- Manejadores de Socket.IO para WebRTC ---

rooms_state = {}

@socketio.on('join')
def on_join(data):
    room = data['room']
    sid = request.sid
    join_room(room)
    
    emit('system', {'msg': 'Un nuevo peer se ha unido a la sala.'}, to=room, include_self=False)

    if room not in rooms_state:
        rooms_state[room] = []
    
    existing_peers = rooms_state[room]
    if existing_peers:
        # Es el segundo peer. Le dice al primero que inicie la conexión.
        first_peer_sid = existing_peers[0]
        emit('start_peer_connection', {'initiator': True}, room=first_peer_sid)
    
    rooms_state[room].append(sid)

@socketio.on('leave')
def on_leave(data):
    room = data['room']
    sid = request.sid
    leave_room(room)
    
    if room in rooms_state and sid in rooms_state[room]:
        rooms_state[room].remove(sid)
        if not rooms_state[room]:
            del rooms_state[room]
            
    # Notifica a los usuarios restantes que alguien se fue
    emit('peer_left', to=room, include_self=False)
    emit('system', {'msg': 'Un peer ha abandonado la sala.'}, to=room, include_self=False)

@socketio.on('signal')
def on_signal(data):
    room = data['room']
    sender_sid = request.sid
    
    if room in rooms_state:
        # Encuentra al otro peer en la sala y envíale la señal directamente
        other_peers = [peer_sid for peer_sid in rooms_state[room] if peer_sid != sender_sid]
        if other_peers:
            recipient_sid = other_peers[0] # Asume solo 2 peers por sala
            emit('signal', {'data': data['data']}, room=recipient_sid)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)