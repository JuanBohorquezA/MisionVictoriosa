from app import db
from datetime import datetime
import base64


class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    def get_id(self):
        return str(self.id)


class Proyecto(db.Model):
    __tablename__ = 'proyectos'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    imagen = db.Column(db.LargeBinary)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with recursos
    recursos = db.relationship('Recurso', backref='proyecto', cascade='all, delete-orphan')
    # Relationship with caracteristicas
    caracteristicas = db.relationship('Caracteristica', backref='proyecto', cascade='all, delete-orphan')
    
    @property
    def imagen_base64(self):
        """Convert image blob to base64 for display"""
        if self.imagen:
            return f"data:image/jpeg;base64,{base64.b64encode(self.imagen).decode('utf-8')}"
        return None
    
    @property
    def todas_imagenes(self):
        """Get all images for this project (main + additional resources)"""
        imagenes = []
        
        # Add main image first if exists
        if self.imagen_base64:
            imagenes.append({
                'imagen_base64': self.imagen_base64,
                'nombre': 'Imagen Principal',
                'tipo': 'principal'
            })
        
        # Add additional images from recursos
        recursos_list = list(self.recursos)
        for recurso in recursos_list:
            if recurso.tipo == 'imagen' and recurso.imagen_base64:
                imagenes.append({
                    'imagen_base64': recurso.imagen_base64,
                    'nombre': recurso.nombre,
                    'tipo': 'adicional'
                })
        
        return imagenes


class Recurso(db.Model):
    __tablename__ = 'recursos'
    
    id = db.Column(db.Integer, primary_key=True)
    proyecto_id = db.Column(db.Integer, db.ForeignKey('proyectos.id'), nullable=False)
    tipo = db.Column(db.String(50), nullable=False, default='imagen')
    nombre = db.Column(db.String(200), nullable=False)
    contenido = db.Column(db.LargeBinary, nullable=False)
    orden = db.Column(db.Integer, default=0)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def imagen_base64(self):
        """Convert image blob to base64 for display"""
        if self.contenido:
            return f"data:image/jpeg;base64,{base64.b64encode(self.contenido).decode('utf-8')}"
        return None


class Caracteristica(db.Model):
    __tablename__ = 'caracteristicas'
    
    id = db.Column(db.Integer, primary_key=True)
    proyecto_id = db.Column(db.Integer, db.ForeignKey('proyectos.id'), nullable=False)
    texto = db.Column(db.String(100), nullable=False)
    icono = db.Column(db.String(50), nullable=False, default='fas fa-star')
    color = db.Column(db.String(20), nullable=False, default='primary')
    orden = db.Column(db.Integer, default=0)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Caracteristica {self.texto}>'
