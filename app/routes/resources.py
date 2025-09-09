from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required

from app import get_conn
from app.ipfs_client import upload_to_ipfs
from app.nlp_utils import generar_embedding, clasificar_texto, embedding_to_blob
from app.vector_db import add_embedding as add_embedding_to_chroma
from app.vector_db import query_similar

resources_bp = Blueprint('resources', __name__, template_folder='../templates')

@resources_bp.route('/nuevo', methods=['GET', 'POST'])
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

        if emb_vec is not None:
            resource_id = cursor.lastrowid
            metadata = {"titulo": titulo, "categoria": categoria_detectada}
            add_embedding_to_chroma(resource_id, emb_vec, metadata)

        conn.close()
        flash(flash_message, flash_category)
        return redirect(url_for('resources.recursos'))
    return render_template('nuevo.html')

@resources_bp.route('/recursos')
@login_required
def recursos():
    conn = get_conn()
    recursos_data = conn.execute("SELECT * FROM recursos ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("recursos.html", recursos=recursos_data)

@resources_bp.route('/buscar_semantico', methods=['GET', 'POST'])
@login_required
def buscar_semantico():
    if request.method == 'POST':
        q = request.form.get('q', '').strip()
        top_k = int(request.form.get('k', 5))
        if not q:
            flash("Por favor, introduce una consulta para buscar.", "error")
            return render_template('buscar_semantico.html')

        q_emb = generar_embedding(q)
        ids, scores = query_similar(q_emb, top_k)

        if not ids:
            return render_template("resultados_busqueda.html", resultados=[], query=q)

        conn = get_conn()
        placeholders = ', '.join('?' for _ in ids)
        query_sql = f"SELECT * FROM recursos WHERE id IN ({placeholders})"
        recursos_dict = {str(r['id']): dict(r) for r in conn.execute(query_sql, [int(i) for i in ids]).fetchall()}
        conn.close()

        results_sorted = []
        for i, resource_id_str in enumerate(ids):
            recurso = recursos_dict.get(resource_id_str)
            if recurso:
                recurso['score'] = scores[i]
                results_sorted.append(recurso)
        
        return render_template("resultados_busqueda.html", resultados=results_sorted, query=q)

    return render_template('buscar_semantico.html')
