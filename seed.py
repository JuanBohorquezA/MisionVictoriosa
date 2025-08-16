import sqlite3
from werkzeug.security import generate_password_hash

def seed_admin_user():
    """Create initial admin user"""
    conn = sqlite3.connect('mision_victoriosa.db')
    cursor = conn.cursor()
    
    # Check if admin user already exists
    cursor.execute('SELECT id FROM usuarios WHERE username = ?', ('admin',))
    existing_admin = cursor.fetchone()
    
    if not existing_admin:
        # Create admin user
        password_hash = generate_password_hash('admin123')
        cursor.execute(
            'INSERT INTO usuarios (username, password_hash) VALUES (?, ?)',
            ('admin', password_hash)
        )
        conn.commit()
        print("Admin user created successfully!")
        print("Username: admin")
        print("Password: admin123")
    else:
        print("Admin user already exists.")
    
    conn.close()

if __name__ == '__main__':
    seed_admin_user()
