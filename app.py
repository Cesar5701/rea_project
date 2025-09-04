# app.py (fragmento principal)
import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
from flask_socketio import SocketIO, emit, join_room, leave_room
from ipfs_client import upload_to_ipfs
from nlp_utils import generar_embedding, clasificar_texto, embedding_to_blob, blob_to_embedding

load_dotenv()
DB = "rea.db"
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "devsecret")
socketio = SocketIO(app)

def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

# SE RESTAURA LA RUTA /webrtc
@app.route('/webrtc')
def webrtc():
    """Renderiza la página de la sala P2P."""
    return render_template('webrtc.html')

@app.route('/nuevo', methods=['GET', 'POST'])
def nuevo():
    # ... (el resto de tu código sigue igual)
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
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO recursos (titulo, descripcion, categoria, enlace, cid, filename, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (titulo, descripcion, categoria_detectada, gateway_url, cid, filename, emb_blob))
        conn.commit()
        conn.close()
        flash("Recurso guardado y clasificado: " + categoria_detectada, "success")
        return redirect(url_for('recursos'))
    return render_template('nuevo.html')


@app.route('/recursos')
def recursos():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM recursos ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return render_template("recursos.html", recursos=rows)

@app.route('/buscar_semantico', methods=['GET', 'POST'])
def buscar_semantico():
    if request.method == 'POST':
        q = request.form.get('q', '').strip()
        top_k = int(request.form.get('k', 5))
        q_emb = generar_embedding(q)

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, titulo, descripcion, categoria, enlace, cid, embedding FROM recursos")
        rows = cur.fetchall()
        conn.close()

        import numpy as np
        results = []
        for r in rows:
            if r["embedding"] is None:
                continue
            try:
                emb_stored = blob_to_embedding(r["embedding"])
                cos = float(np.dot(q_emb, emb_stored) / (np.linalg.norm(q_emb) * np.linalg.norm(emb_stored) + 1e-9))
                results.append({**dict(r), "score": cos})
            except:
                continue

        results_sorted = sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]
        return render_template("resultados_busqueda.html", resultados=results_sorted, query=q)

    return render_template('buscar_semantico.html')

# --- Manejadores de Socket.IO ---
@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    emit('system', {'msg': f'Un nuevo peer se ha unido a la sala.'}, to=room, include_self=False)

@socketio.on('leave')
def on_leave(data):
    room = data['room']
    leave_room(room)
    emit('system', {'msg': f'Un peer ha abandonado la sala.'}, to=room, include_self=False)

@socketio.on('signal')
def on_signal(data):
    room = data['room']
    emit('signal', {'data': data['data']}, to=room, include_self=False)

# --- Bloque para iniciar ---
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)