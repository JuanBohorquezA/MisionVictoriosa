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
            imagen BLOB,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create recursos table for multiple images per project
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recursos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proyecto_id INTEGER NOT NULL,
            tipo TEXT NOT NULL DEFAULT 'imagen',
            nombre TEXT NOT NULL,
            contenido BLOB NOT NULL,
            orden INTEGER DEFAULT 0,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos (id) ON DELETE CASCADE
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

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debe iniciar sesión para acceder a esta página.', 'error')
            return redirect(url_for('login'))
        if session.get('username') != 'admin':
            flash('Solo el administrador puede acceder a esta función.', 'error')
            return redirect(url_for('admin'))
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
    
    # Convert BLOB images to base64 for display and get additional resources
    projects_with_images = []
    for project in projects:
        project_dict = dict(project)
        
        # Get main image (legacy)
        if project['imagen']:
            image_data = base64.b64encode(project['imagen']).decode('utf-8')
            project_dict['imagen_base64'] = f"data:image/jpeg;base64,{image_data}"
        else:
            project_dict['imagen_base64'] = None
        
        # Get additional resources (images)
        cursor.execute('''
            SELECT id, nombre, contenido, orden 
            FROM recursos 
            WHERE proyecto_id = ? AND tipo = 'imagen' 
            ORDER BY orden, id
        ''', (project['id'],))
        recursos = cursor.fetchall()
        
        project_dict['recursos'] = []
        for recurso in recursos:
            if recurso['contenido']:
                resource_data = base64.b64encode(recurso['contenido']).decode('utf-8')
                project_dict['recursos'].append({
                    'id': recurso['id'],
                    'nombre': recurso['nombre'],
                    'imagen_base64': f"data:image/jpeg;base64,{resource_data}",
                    'orden': recurso['orden']
                })
        
        # Create combined images list (main image + resources)
        project_dict['todas_imagenes'] = []
        if project_dict['imagen_base64']:
            project_dict['todas_imagenes'].append({
                'id': 'main',
                'nombre': 'Imagen principal',
                'imagen_base64': project_dict['imagen_base64'],
                'orden': -1
            })
        project_dict['todas_imagenes'].extend(project_dict['recursos'])
        
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
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Create project
        imagen_blob = None
        if imagen_file and imagen_file.filename:
            imagen_blob = imagen_file.read()
        
        cursor.execute(
            'INSERT INTO proyectos (titulo, descripcion, imagen) VALUES (?, ?, ?)',
            (titulo, descripcion, imagen_blob)
        )
        project_id = cursor.lastrowid
        
        # Handle multiple additional images
        imagenes_adicionales = request.files.getlist('imagenes_adicionales')
        orden = 1
        for imagen_adicional in imagenes_adicionales:
            if imagen_adicional and imagen_adicional.filename:
                imagen_content = imagen_adicional.read()
                if imagen_content:  # Only save if there's actual content
                    cursor.execute(
                        'INSERT INTO recursos (proyecto_id, tipo, nombre, contenido, orden) VALUES (?, ?, ?, ?, ?)',
                        (project_id, 'imagen', imagen_adicional.filename, imagen_content, orden)
                    )
                    orden += 1
        
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
            
            # Handle new additional images
            imagenes_adicionales = request.files.getlist('imagenes_adicionales')
            if imagenes_adicionales:
                # Get current max order
                cursor.execute('SELECT COALESCE(MAX(orden), 0) FROM recursos WHERE proyecto_id = ?', (project_id,))
                max_orden = cursor.fetchone()[0]
                orden = max_orden + 1
                
                for imagen_adicional in imagenes_adicionales:
                    if imagen_adicional and imagen_adicional.filename:
                        imagen_content = imagen_adicional.read()
                        if imagen_content:  # Only save if there's actual content
                            cursor.execute(
                                'INSERT INTO recursos (proyecto_id, tipo, nombre, contenido, orden) VALUES (?, ?, ?, ?, ?)',
                                (project_id, 'imagen', imagen_adicional.filename, imagen_content, orden)
                            )
                            orden += 1
            
            conn.commit()
            flash('Proyecto actualizado exitosamente.', 'success')
        else:
            flash('Proyecto no encontrado.', 'error')
        
        conn.close()
        return redirect(url_for('admin'))
    
    # GET request - show form with current data
    cursor.execute('SELECT id, titulo, descripcion FROM proyectos WHERE id = ?', (project_id,))
    project = cursor.fetchone()
    
    # Get existing resources
    if project:
        cursor.execute('''
            SELECT id, nombre, contenido, orden 
            FROM recursos 
            WHERE proyecto_id = ? AND tipo = 'imagen' 
            ORDER BY orden, id
        ''', (project_id,))
        recursos = cursor.fetchall()
        
        project_dict = dict(project)
        project_dict['recursos'] = []
        for recurso in recursos:
            if recurso['contenido']:
                resource_data = base64.b64encode(recurso['contenido']).decode('utf-8')
                project_dict['recursos'].append({
                    'id': recurso['id'],
                    'nombre': recurso['nombre'],
                    'imagen_base64': f"data:image/jpeg;base64,{resource_data}",
                    'orden': recurso['orden']
                })
        project = project_dict
    
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
@admin_required
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

@app.route('/admin/user/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    """Edit existing user (admin only)"""
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form.get('password')
        
        # Check if username already exists for other users
        cursor.execute('SELECT id FROM usuarios WHERE username = ? AND id != ?', (username, user_id))
        existing_user = cursor.fetchone()
        
        if existing_user:
            flash('El nombre de usuario ya existe.', 'error')
            cursor.execute('SELECT id, username FROM usuarios WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            conn.close()
            return render_template('user_form.html', user=user, action='Editar')
        
        # Update user
        if password:
            password_hash = generate_password_hash(password)
            cursor.execute(
                'UPDATE usuarios SET username = ?, password_hash = ? WHERE id = ?',
                (username, password_hash, user_id)
            )
        else:
            cursor.execute(
                'UPDATE usuarios SET username = ? WHERE id = ?',
                (username, user_id)
            )
        
        conn.commit()
        conn.close()
        
        flash('Usuario actualizado exitosamente.', 'success')
        return redirect(url_for('admin'))
    
    # GET request - show form with current data
    cursor.execute('SELECT id, username FROM usuarios WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        flash('Usuario no encontrado.', 'error')
        return redirect(url_for('admin'))
    
    return render_template('user_form.html', user=user, action='Editar')

@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Delete user (admin only)"""
    # Prevent deletion of admin user
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM usuarios WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        flash('Usuario no encontrado.', 'error')
    elif user['username'] == 'admin':
        flash('No se puede eliminar al usuario administrador.', 'error')
    else:
        cursor.execute('DELETE FROM usuarios WHERE id = ?', (user_id,))
        conn.commit()
        flash('Usuario eliminado exitosamente.', 'success')
    
    conn.close()
    return redirect(url_for('admin'))

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

@app.route('/proyecto/<int:project_id>')
def project_detail(project_id):
    """View project details"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, titulo, descripcion, imagen FROM proyectos WHERE id = ?', (project_id,))
    project = cursor.fetchone()
    
    if not project:
        flash('Proyecto no encontrado.', 'error')
        return redirect(url_for('index'))
    
    # Convert BLOB image to base64 for display
    project_dict = dict(project)
    if project['imagen']:
        image_data = base64.b64encode(project['imagen']).decode('utf-8')
        project_dict['imagen_base64'] = f"data:image/jpeg;base64,{image_data}"
    else:
        project_dict['imagen_base64'] = None
    
    # Get additional resources (images)
    cursor.execute('''
        SELECT id, nombre, contenido, orden 
        FROM recursos 
        WHERE proyecto_id = ? AND tipo = 'imagen' 
        ORDER BY orden, id
    ''', (project_id,))
    recursos = cursor.fetchall()
    
    project_dict['recursos'] = []
    for recurso in recursos:
        if recurso['contenido']:
            resource_data = base64.b64encode(recurso['contenido']).decode('utf-8')
            project_dict['recursos'].append({
                'id': recurso['id'],
                'nombre': recurso['nombre'],
                'imagen_base64': f"data:image/jpeg;base64,{resource_data}",
                'orden': recurso['orden']
            })
    
    # Create combined images list (main image + resources)
    project_dict['todas_imagenes'] = []
    if project_dict['imagen_base64']:
        project_dict['todas_imagenes'].append({
            'id': 'main',
            'nombre': 'Imagen principal',
            'imagen_base64': project_dict['imagen_base64'],
            'orden': -1
        })
    project_dict['todas_imagenes'].extend(project_dict['recursos'])
    
    conn.close()
    
    is_authenticated = 'user_id' in session
    return render_template('project_detail.html', project=project_dict, is_authenticated=is_authenticated)

@app.route('/admin/recurso/<int:recurso_id>/delete', methods=['POST'])
@login_required
def delete_recurso(recurso_id):
    """Delete a project resource"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get project_id for redirect
    cursor.execute('SELECT proyecto_id FROM recursos WHERE id = ?', (recurso_id,))
    recurso = cursor.fetchone()
    
    if recurso:
        cursor.execute('DELETE FROM recursos WHERE id = ?', (recurso_id,))
        conn.commit()
        flash('Recurso eliminado exitosamente.', 'success')
        project_id = recurso['proyecto_id']
    else:
        flash('Recurso no encontrado.', 'error')
        project_id = None
    
    conn.close()
    
    if project_id:
        return redirect(url_for('edit_project', project_id=project_id))
    else:
        return redirect(url_for('admin'))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
