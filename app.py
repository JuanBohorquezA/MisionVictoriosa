import os
import logging
import base64
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Database configuration
DATABASE = 'mision_victoriosa.db'

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Create usuarios table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    
    # Create proyectos table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            imagen BLOB
        )
    ''')
    
    conn.commit()
    conn.close()

def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debe iniciar sesión para acceder a esta página.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Home page with public sections"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get all projects for public display
    cursor.execute('SELECT id, titulo, descripcion, imagen FROM proyectos ORDER BY id DESC')
    projects = cursor.fetchall()
    
    # Convert BLOB images to base64 for display
    projects_with_images = []
    for project in projects:
        project_dict = dict(project)
        if project['imagen']:
            image_data = base64.b64encode(project['imagen']).decode('utf-8')
            project_dict['imagen_base64'] = f"data:image/jpeg;base64,{image_data}"
        else:
            project_dict['imagen_base64'] = None
        projects_with_images.append(project_dict)
    
    conn.close()
    
    is_authenticated = 'user_id' in session
    return render_template('index.html', projects=projects_with_images, is_authenticated=is_authenticated)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and authentication"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, password_hash FROM usuarios WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Inicio de sesión exitoso.', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Usuario o contraseña incorrectos.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    flash('Sesión cerrada exitosamente.', 'success')
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin():
    """Admin dashboard"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get all projects
    cursor.execute('SELECT id, titulo, descripcion FROM proyectos ORDER BY id DESC')
    projects = cursor.fetchall()
    
    # Get all users
    cursor.execute('SELECT id, username FROM usuarios ORDER BY id')
    users = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin.html', projects=projects, users=users)

@app.route('/admin/project/new', methods=['GET', 'POST'])
@login_required
def new_project():
    """Create new project"""
    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        imagen_file = request.files.get('imagen')
        
        imagen_blob = None
        if imagen_file and imagen_file.filename:
            imagen_blob = imagen_file.read()
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO proyectos (titulo, descripcion, imagen) VALUES (?, ?, ?)',
            (titulo, descripcion, imagen_blob)
        )
        conn.commit()
        conn.close()
        
        flash('Proyecto creado exitosamente.', 'success')
        return redirect(url_for('admin'))
    
    return render_template('project_form.html', project=None, action='Crear')

@app.route('/admin/project/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    """Edit existing project"""
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        imagen_file = request.files.get('imagen')
        
        # Get current project data
        cursor.execute('SELECT imagen FROM proyectos WHERE id = ?', (project_id,))
        current_project = cursor.fetchone()
        
        if current_project:
            imagen_blob = current_project['imagen']  # Keep current image by default
            
            # Update image if new one is uploaded
            if imagen_file and imagen_file.filename:
                imagen_blob = imagen_file.read()
            
            cursor.execute(
                'UPDATE proyectos SET titulo = ?, descripcion = ?, imagen = ? WHERE id = ?',
                (titulo, descripcion, imagen_blob, project_id)
            )
            conn.commit()
            flash('Proyecto actualizado exitosamente.', 'success')
        else:
            flash('Proyecto no encontrado.', 'error')
        
        conn.close()
        return redirect(url_for('admin'))
    
    # GET request - show form with current data
    cursor.execute('SELECT id, titulo, descripcion FROM proyectos WHERE id = ?', (project_id,))
    project = cursor.fetchone()
    conn.close()
    
    if not project:
        flash('Proyecto no encontrado.', 'error')
        return redirect(url_for('admin'))
    
    return render_template('project_form.html', project=project, action='Editar')

@app.route('/admin/project/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    """Delete project"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM proyectos WHERE id = ?', (project_id,))
    conn.commit()
    conn.close()
    
    flash('Proyecto eliminado exitosamente.', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/user/new', methods=['GET', 'POST'])
@login_required
def new_user():
    """Create new user"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if username already exists
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM usuarios WHERE username = ?', (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            flash('El nombre de usuario ya existe.', 'error')
            conn.close()
            return render_template('user_form.html', action='Crear')
        
        # Create new user
        password_hash = generate_password_hash(password)
        cursor.execute(
            'INSERT INTO usuarios (username, password_hash) VALUES (?, ?)',
            (username, password_hash)
        )
        conn.commit()
        conn.close()
        
        flash('Usuario creado exitosamente.', 'success')
        return redirect(url_for('admin'))
    
    return render_template('user_form.html', action='Crear')

@app.route('/contact', methods=['POST'])
def contact():
    """Handle contact form submission"""
    nombre = request.form.get('nombre', '')
    email = request.form.get('email', '')
    mensaje = request.form.get('mensaje', '')
    
    # In a real application, you would send an email or save to database
    # For now, just show a success message
    flash(f'Gracias {nombre}, hemos recibido tu mensaje. Te contactaremos pronto.', 'success')
    return redirect(url_for('index'))

@app.route('/image/<int:project_id>')
def serve_image(project_id):
    """Serve project image from database"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT imagen FROM proyectos WHERE id = ?', (project_id,))
    project = cursor.fetchone()
    conn.close()
    
    if project and project['imagen']:
        response = make_response(project['imagen'])
        response.headers['Content-Type'] = 'image/jpeg'
        return response
    else:
        # Return a placeholder or 404
        return '', 404

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
