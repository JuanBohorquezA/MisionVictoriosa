"""
Script para crear un proyecto de demostración con imágenes
Demuestra que el sistema de carga de imágenes funciona correctamente
"""

import base64
from app import app, db
from models import Proyecto, Recurso

def create_demo_project():
    """Crear un proyecto de demostración con imágenes"""
    with app.app_context():
        try:
            # Leer imagen principal
            with open('static/img/Community_center_project_fb34a5ba.png', 'rb') as f:
                imagen_principal = f.read()
            
            # Crear el proyecto
            proyecto = Proyecto(
                titulo="Centro Comunitario Sostenible",
                descripcion="Un moderno centro comunitario equipado con paneles solares y espacios verdes, diseñado para ser un punto de encuentro donde personas de diferentes orígenes puedan colaborar en proyectos educativos y de desarrollo comunitario. Este proyecto busca crear un espacio sostenible que sirva como modelo para futuras iniciativas comunitarias.",
                imagen=imagen_principal
            )
            db.session.add(proyecto)
            db.session.flush()  # Obtener el ID del proyecto
            
            # Agregar imagen adicional como recurso
            with open('static/img/Interior_community_spaces_f7314107.png', 'rb') as f:
                imagen_interior = f.read()
            
            recurso = Recurso(
                proyecto_id=proyecto.id,
                tipo='imagen',
                nombre='interior_centro_comunitario.png',
                contenido=imagen_interior,
                orden=1
            )
            db.session.add(recurso)
            
            db.session.commit()
            print(f"✅ Proyecto demo creado exitosamente!")
            print(f"   ID: {proyecto.id}")
            print(f"   Título: {proyecto.titulo}")
            print(f"   Imagen principal: ✓")
            print(f"   Recursos adicionales: 1")
            
        except Exception as e:
            print(f"❌ Error creando proyecto demo: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    create_demo_project()