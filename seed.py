from app import app, db
from models import Usuario
from werkzeug.security import generate_password_hash

def seed_admin_user():
    """Create initial admin user"""
    with app.app_context():
        # Check if admin user already exists
        existing_admin = Usuario.query.filter_by(username='admin').first()
        
        if not existing_admin:
            # Create admin user
            password_hash = generate_password_hash('admin123')
            admin_user = Usuario(username='admin', password_hash=password_hash)
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created successfully!")
            print("Username: admin")
            print("Password: admin123")
        else:
            print("Admin user already exists.")

if __name__ == '__main__':
    seed_admin_user()
