from app import db
from datetime import datetime


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


class Recurso(db.Model):
    __tablename__ = 'recursos'
    
    id = db.Column(db.Integer, primary_key=True)
    proyecto_id = db.Column(db.Integer, db.ForeignKey('proyectos.id'), nullable=False)
    tipo = db.Column(db.String(50), nullable=False, default='imagen')
    nombre = db.Column(db.String(200), nullable=False)
    contenido = db.Column(db.LargeBinary, nullable=False)
    orden = db.Column(db.Integer, default=0)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
