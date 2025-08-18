#!/usr/bin/env python3
import requests
from io import BytesIO

# Test the form submission
def test_new_project():
    # First get login session
    session = requests.Session()
    
    # Try to login (assuming admin/admin credentials)
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    login_response = session.post('http://localhost:5000/login', data=login_data)
    print(f"Login status: {login_response.status_code}")
    
    if login_response.status_code == 200:
        # Now try to submit new project form
        project_data = {
            'titulo': 'Proyecto de Prueba',
            'descripcion': 'Esta es una descripción de prueba para el proyecto.',
            'caracteristica_texto_nueva': ['Característica 1', 'Característica 2'],
            'caracteristica_icono_nueva': ['fas fa-star', 'fas fa-heart'],
            'caracteristica_color_nueva': ['primary', 'success']
        }
        
        # Add empty file to satisfy form
        files = {'imagen': ('', BytesIO(), 'image/jpeg')}
        
        response = session.post('http://localhost:5000/admin/project/new', 
                              data=project_data, files=files)
        
        print(f"Project creation status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response content preview: {response.text[:500]}")
        
        if response.status_code == 302:
            print("Redirect detected - likely successful!")
        elif response.status_code == 200:
            print("Form returned - check for errors")
    else:
        print("Login failed")

if __name__ == "__main__":
    test_new_project()