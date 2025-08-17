import os
import logging
import base64
from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.DEBUG)


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# configure the database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
# initialize the app with the extension, flask-sqlalchemy >= 3.0.x
db.init_app(app)

with app.app_context():
    # Make sure to import the models here or their tables won't be created
    import models  # noqa: F401

    db.create_all()

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
    from models import Proyecto, Recurso
    
    # Get all projects for public display
    projects = Proyecto.query.order_by(Proyecto.id.desc()).all()
    
    # Convert BLOB images to base64 for display and get additional resources
    projects_with_images = []
    for project in projects:
        project_dict = {
            'id': project.id,
            'titulo': project.titulo,
            'descripcion': project.descripcion
        }
        
        # Get main image (legacy)
        if project.imagen:
            image_data = base64.b64encode(project.imagen).decode('utf-8')
            project_dict['imagen_base64'] = f"data:image/jpeg;base64,{image_data}"
        else:
            project_dict['imagen_base64'] = None
        
        # Get additional resources (images)
        recursos = Recurso.query.filter_by(
            proyecto_id=project.id, 
            tipo='imagen'
        ).order_by(Recurso.orden, Recurso.id).all()
        
        project_dict['recursos'] = []
        for recurso in recursos:
            if recurso.contenido:
                resource_data = base64.b64encode(recurso.contenido).decode('utf-8')
                project_dict['recursos'].append({
                    'id': recurso.id,
                    'nombre': recurso.nombre,
                    'imagen_base64': f"data:image/jpeg;base64,{resource_data}",
                    'orden': recurso.orden
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
    
    is_authenticated = 'user_id' in session
    return render_template('index.html', projects=projects_with_images, is_authenticated=is_authenticated)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and authentication"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        from models import Usuario
        user = Usuario.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
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
    from models import Proyecto, Usuario
    
    # Get all projects
    projects = Proyecto.query.order_by(Proyecto.id.desc()).all()
    
    # Get all users
    users = Usuario.query.order_by(Usuario.id).all()
    
    return render_template('admin.html', projects=projects, users=users)

@app.route('/admin/project/new', methods=['GET', 'POST'])
@login_required
def new_project():
    """Create new project"""
    if request.method == 'POST':
        from models import Proyecto, Recurso
        
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        imagen_file = request.files.get('imagen')
        
        # Create project
        imagen_blob = None
        if imagen_file and imagen_file.filename:
            imagen_blob = imagen_file.read()
        
        proyecto = Proyecto()
        proyecto.titulo = titulo
        proyecto.descripcion = descripcion
        proyecto.imagen = imagen_blob
        db.session.add(proyecto)
        db.session.flush()  # Get the ID before commit
        
        # Handle multiple additional images
        imagenes_adicionales = request.files.getlist('imagenes_adicionales')
        orden = 1
        for imagen_adicional in imagenes_adicionales:
            if imagen_adicional and imagen_adicional.filename:
                imagen_content = imagen_adicional.read()
                if imagen_content:  # Only save if there's actual content
                    recurso = Recurso()
                    recurso.proyecto_id = proyecto.id
                    recurso.tipo = 'imagen'
                    recurso.nombre = imagen_adicional.filename
                    recurso.contenido = imagen_content
                    recurso.orden = orden
                    db.session.add(recurso)
                    orden += 1
        
        db.session.commit()
        flash('Proyecto creado exitosamente.', 'success')
        return redirect(url_for('admin'))
    
    return render_template('project_form.html', project=None, action='Crear')

@app.route('/admin/project/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    """Edit existing project"""
    from models import Proyecto, Recurso
    
    proyecto = Proyecto.query.get_or_404(project_id)
    
    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        imagen_file = request.files.get('imagen')
        
        # Update project data
        proyecto.titulo = titulo
        proyecto.descripcion = descripcion
        
        # Update image if new one is uploaded
        if imagen_file and imagen_file.filename:
            proyecto.imagen = imagen_file.read()
        
        # Handle new additional images
        imagenes_adicionales = request.files.getlist('imagenes_adicionales')
        if imagenes_adicionales:
            # Get current max order
            max_orden = db.session.query(db.func.max(Recurso.orden)).filter_by(proyecto_id=project_id).scalar() or 0
            orden = max_orden + 1
            
            for imagen_adicional in imagenes_adicionales:
                if imagen_adicional and imagen_adicional.filename:
                    imagen_content = imagen_adicional.read()
                    if imagen_content:  # Only save if there's actual content
                        recurso = Recurso()
                        recurso.proyecto_id = project_id
                        recurso.tipo = 'imagen'
                        recurso.nombre = imagen_adicional.filename
                        recurso.contenido = imagen_content
                        recurso.orden = orden
                        db.session.add(recurso)
                        orden += 1
        
        db.session.commit()
        flash('Proyecto actualizado exitosamente.', 'success')
        return redirect(url_for('admin'))
    
    # GET request - show form with current data
    project_dict = {
        'id': proyecto.id,
        'titulo': proyecto.titulo,
        'descripcion': proyecto.descripcion
    }
    
    # Add main image if exists
    if proyecto.imagen:
        image_data = base64.b64encode(proyecto.imagen).decode('utf-8')
        project_dict['imagen_base64'] = f"data:image/jpeg;base64,{image_data}"
    else:
        project_dict['imagen_base64'] = None
    
    # Get existing resources
    recursos = Recurso.query.filter_by(
        proyecto_id=project_id, 
        tipo='imagen'
    ).order_by(Recurso.orden, Recurso.id).all()
    
    project_dict['recursos'] = []
    for recurso in recursos:
        if recurso.contenido:
            resource_data = base64.b64encode(recurso.contenido).decode('utf-8')
            project_dict['recursos'].append({
                'id': recurso.id,
                'nombre': recurso.nombre,
                'imagen_base64': f"data:image/jpeg;base64,{resource_data}",
                'orden': recurso.orden
            })
    
    return render_template('project_form.html', project=project_dict, action='Editar')

@app.route('/admin/project/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    """Delete project"""
    from models import Proyecto
    
    proyecto = Proyecto.query.get_or_404(project_id)
    db.session.delete(proyecto)
    db.session.commit()
    
    flash('Proyecto eliminado exitosamente.', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/user/new', methods=['GET', 'POST'])
@admin_required
def new_user():
    """Create new user"""
    if request.method == 'POST':
        from models import Usuario
        
        username = request.form['username']
        password = request.form['password']
        
        # Check if username already exists
        existing_user = Usuario.query.filter_by(username=username).first()
        
        if existing_user:
            flash('El nombre de usuario ya existe.', 'error')
            return render_template('user_form.html', action='Crear')
        
        # Create new user
        password_hash = generate_password_hash(password)
        usuario = Usuario()
        usuario.username = username
        usuario.password_hash = password_hash
        db.session.add(usuario)
        db.session.commit()
        
        flash('Usuario creado exitosamente.', 'success')
        return redirect(url_for('admin'))
    
    return render_template('user_form.html', action='Crear')

@app.route('/admin/user/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    """Edit existing user (admin only)"""
    from models import Usuario
    
    usuario = Usuario.query.get_or_404(user_id)
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form.get('password')
        
        # Check if username already exists for other users
        existing_user = Usuario.query.filter(
            Usuario.username == username,
            Usuario.id != user_id
        ).first()
        
        if existing_user:
            flash('El nombre de usuario ya existe.', 'error')
            return render_template('user_form.html', user=usuario, action='Editar')
        
        # Update user
        usuario.username = username
        if password:
            usuario.password_hash = generate_password_hash(password)
        
        db.session.commit()
        flash('Usuario actualizado exitosamente.', 'success')
        return redirect(url_for('admin'))
    
    return render_template('user_form.html', user=usuario, action='Editar')

@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Delete user (admin only)"""
    from models import Usuario
    
    usuario = Usuario.query.get_or_404(user_id)
    
    if usuario.username == 'admin':
        flash('No se puede eliminar al usuario administrador.', 'error')
    else:
        db.session.delete(usuario)
        db.session.commit()
        flash('Usuario eliminado exitosamente.', 'success')
    
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
    from models import Proyecto
    
    proyecto = Proyecto.query.get_or_404(project_id)
    
    if proyecto.imagen:
        response = make_response(proyecto.imagen)
        response.headers['Content-Type'] = 'image/jpeg'
        return response
    else:
        # Return a placeholder or 404
        return '', 404

@app.route('/proyecto/<int:project_id>')
def project_detail(project_id):
    """View project details"""
    from models import Proyecto, Recurso
    
    proyecto = Proyecto.query.get_or_404(project_id)
    
    # Convert BLOB image to base64 for display
    project_dict = {
        'id': proyecto.id,
        'titulo': proyecto.titulo,
        'descripcion': proyecto.descripcion
    }
    
    if proyecto.imagen:
        image_data = base64.b64encode(proyecto.imagen).decode('utf-8')
        project_dict['imagen_base64'] = f"data:image/jpeg;base64,{image_data}"
    else:
        project_dict['imagen_base64'] = None
    
    # Get additional resources (images)
    recursos = Recurso.query.filter_by(
        proyecto_id=project_id, 
        tipo='imagen'
    ).order_by(Recurso.orden, Recurso.id).all()
    
    project_dict['recursos'] = []
    for recurso in recursos:
        if recurso.contenido:
            resource_data = base64.b64encode(recurso.contenido).decode('utf-8')
            project_dict['recursos'].append({
                'id': recurso.id,
                'nombre': recurso.nombre,
                'imagen_base64': f"data:image/jpeg;base64,{resource_data}",
                'orden': recurso.orden
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
    
    is_authenticated = 'user_id' in session
    return render_template('project_detail.html', project=project_dict, is_authenticated=is_authenticated)

@app.route('/admin/recurso/<int:recurso_id>/delete', methods=['POST'])
@login_required
def delete_recurso(recurso_id):
    """Delete a project resource"""
    from models import Recurso
    
    recurso = Recurso.query.get_or_404(recurso_id)
    project_id = recurso.proyecto_id
    
    db.session.delete(recurso)
    db.session.commit()
    flash('Recurso eliminado exitosamente.', 'success')
    
    if project_id:
        return redirect(url_for('edit_project', project_id=project_id))
    else:
        return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
