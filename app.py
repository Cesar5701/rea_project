import os
import sqlite3
# 1. Se importa la herramienta para manejar duraciones de tiempo
from datetime import timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session
from dotenv import load_dotenv
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from ipfs_client import upload_to_ipfs
from nlp_utils import generar_embedding, clasificar_texto, embedding_to_blob, blob_to_embedding
import passwordmeter

# --- IMPORTACIONES PARA LA BÚSQUEDA SEMÁNTICA MEJORADA ---
from vector_db import add_embedding as add_embedding_to_chroma
from vector_db import query_similar

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "devsecret")

# 2. CONFIGURACIÓN DE EXPIRACIÓN DE SESIÓN EN EL BACKEND
# Se establece la duración máxima de inactividad de una sesión en 10 minutos.
app.permanent_session_lifetime = timedelta(minutes=6)

socketio = SocketIO(app)

# Configuración de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, email, role):
        self.id = id
        self.email = email
        self.role = role
        self.username = email.split('@')[0]

@login_manager.user_loader
def load_user(user_id):
    conn = get_conn()
    user_data = conn.execute("SELECT id, email, role FROM usuarios WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if user_data:
        return User(id=user_data['id'], email=user_data['email'], role=user_data['role'])
    return None

# 3. FUNCIÓN PARA REINICIAR EL CONTADOR DE INACTIVIDAD
# Esta función se ejecuta con cada petición del usuario (cada vez que carga una página o envía un formulario).
# Marca la sesión como permanente, lo que activa el contador de 10 minutos.
@app.before_request
def make_session_permanent():
    session.permanent = True

def get_conn():
    conn = sqlite3.connect(os.getenv("DATABASE_URL", "rea.db"))
    conn.row_factory = sqlite3.Row
    return conn

# --- Rutas Principales y de Autenticación ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if not email.endswith('@alumno.buap.mx'):
            flash('Solo se permiten registros con el correo institucional "@alumno.buap.mx".', 'error')
            return redirect(url_for('register'))
        
        strength, _ = passwordmeter.test(password)
        if strength < 0.5:
            flash('La contraseña es muy débil. Por favor, elige una más segura.', 'error')
            return redirect(url_for('register'))
        
        conn = get_conn()
        user_exists = conn.execute("SELECT id FROM usuarios WHERE email = ?", (email,)).fetchone()
        if user_exists:
            flash('Ese correo electrónico ya está registrado.', 'error')
            conn.close()
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (email, password_hash) VALUES (?, ?)", (email, hashed_password))
        conn.commit()
        conn.close()
        flash('¡Registro exitoso! Por favor, inicia sesión con tu correo.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_conn()
        user_data = conn.execute("SELECT id, email, password_hash, role FROM usuarios WHERE email = ?", (email,)).fetchone()
        conn.close()
        if user_data and check_password_hash(user_data['password_hash'], password):
            user = User(id=user_data['id'], email=user_data['email'], role=user_data['role'])
            login_user(user)
            # Marcar la sesión como permanente desde el inicio de sesión
            session.permanent = True
            return redirect(url_for('index'))
        else:
            flash('Correo o contraseña incorrectos.', 'error')
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
        if not titulo:
            flash("El título es un campo obligatorio.", "error")
            return redirect(request.url)
        
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
        
        emb_vec = None
        try:
            texto_para_clasificar = f"{titulo} {descripcion}"
            categoria_detectada = categoria_manual or clasificar_texto(texto_para_clasificar)
            emb_vec = generar_embedding(texto_para_clasificar)
            emb_blob = embedding_to_blob(emb_vec)
            flash_message = "Recurso guardado y clasificado: " + categoria_detectada
            flash_category = "success"
        except Exception as e:
            print(f"ERROR en NLP: {e}")
            categoria_detectada = categoria_manual or "Sin clasificar"
            emb_blob = None
            flash_message = "Recurso guardado, pero ocurrió un error al clasificarlo automáticamente."
            flash_category = "warning"

        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO recursos (titulo, descripcion, categoria, enlace, cid, filename, embedding, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (titulo, descripcion, categoria_detectada, gateway_url, cid, filename, emb_blob, current_user.id))
        conn.commit()
        # --- MEJORA: Añadir a ChromaDB ---
        if emb_vec is not None:
            resource_id = cursor.lastrowid
            metadata = {"titulo": titulo, "categoria": categoria_detectada}
            add_embedding_to_chroma(resource_id, emb_vec, metadata)
        # ---------------------------------
        conn.close()
        flash(flash_message, flash_category)
        return redirect(url_for('recursos'))
    return render_template('nuevo.html')

@app.route('/recursos')
@login_required
def recursos():
    conn = get_conn()
    recursos_data = conn.execute("SELECT * FROM recursos ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("recursos.html", recursos=recursos_data)

@app.route('/buscar_semantico', methods=['GET', 'POST'])
@login_required
def buscar_semantico():
    if request.method == 'POST':
        q = request.form.get('q', '').strip()
        top_k = int(request.form.get('k', 5))
        if not q:
            flash("Por favor, introduce una consulta para buscar.", "error")
            return render_template('buscar_semantico.html')

        # 1. Generar embedding para la consulta del usuario
        q_emb = generar_embedding(q)
        
        # 2. Buscar en ChromaDB los IDs y puntuaciones de los recursos más similares
        ids, scores = query_similar(q_emb, top_k)

        if not ids:
            return render_template("resultados_busqueda.html", resultados=[], query=q)

        # 3. Obtener los detalles completos de los recursos desde SQLite usando los IDs
        conn = get_conn()
        # El placeholder '?' se repite por cada ID encontrado
        placeholders = ', '.join('?' for _ in ids)
        query_sql = f"SELECT * FROM recursos WHERE id IN ({placeholders})"
        # ChromaDB devuelve IDs como strings, los convertimos a enteros
        recursos_dict = {str(r['id']): dict(r) for r in conn.execute(query_sql, [int(i) for i in ids]).fetchall()}
        conn.close()

        # 4. Combinar los resultados de SQLite con las puntuaciones de ChromaDB
        results_sorted = []
        for i, resource_id_str in enumerate(ids):
            recurso = recursos_dict.get(resource_id_str)
            if recurso:
                recurso['score'] = scores[i]
                results_sorted.append(recurso)
        
        return render_template("resultados_busqueda.html", resultados=results_sorted, query=q)

    return render_template('buscar_semantico.html')

# --- Manejadores de Socket.IO para WebRTC ---
rooms = {} 
@socketio.on('join')
def on_join(data):
    room = data['room']
    sid = request.sid
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

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
        