"""
Script de configuración automática para Misión Victoriosa
Configura la base de datos y crea el usuario administrador si no existen
"""

import os
from app import app, db
from models import Usuario
from werkzeug.security import generate_password_hash


def setup_database():
    """Configura la base de datos y crea tablas si no existen"""
    with app.app_context():
        try:
            # Crear todas las tablas
            db.create_all()
            print("✓ Base de datos configurada correctamente")
            
            # Verificar si existe el usuario admin
            admin_user = Usuario.query.filter_by(username='admin').first()
            
            if not admin_user:
                # Crear usuario administrador
                password_hash = generate_password_hash('admin123')
                admin = Usuario(username='admin', password_hash=password_hash)
                db.session.add(admin)
                db.session.commit()
                
                print("✓ Usuario administrador creado")
                print("  Username: admin")
                print("  Password: admin123")
            else:
                print("✓ Usuario administrador ya existe")
                
        except Exception as e:
            print(f"Error configurando la base de datos: {str(e)}")
            return False
            
    return True


def check_environment():
    """Verifica que las variables de entorno estén configuradas"""
    required_vars = ['DATABASE_URL']
    missing_vars = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Variables de entorno faltantes: {', '.join(missing_vars)}")
        return False
    
    print("✓ Variables de entorno configuradas")
    return True


if __name__ == '__main__':
    print("🚀 Configurando Misión Victoriosa...")
    
    # Verificar entorno
    if not check_environment():
        print("❌ Error: Variables de entorno no configuradas")
        exit(1)
    
    # Configurar base de datos
    if setup_database():
        print("✅ Configuración completada exitosamente")
    else:
        print("❌ Error durante la configuración")
        exit(1)