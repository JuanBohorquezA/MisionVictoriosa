#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup

def test_navigation():
    session = requests.Session()
    
    # Login first
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    login_response = session.post('http://localhost:5000/login', data=login_data)
    print(f"Login status: {login_response.status_code}")
    
    if login_response.status_code == 200:
        # Test navigation from admin panel
        admin_response = session.get('http://localhost:5000/admin')
        print(f"Admin page status: {admin_response.status_code}")
        
        # Parse HTML to find navigation links
        soup = BeautifulSoup(admin_response.text, 'html.parser')
        nav_links = soup.find_all('a', class_='nav-link')
        
        print("\nNavigation links found in admin panel:")
        for link in nav_links:
            href = link.get('href', 'No href')
            text = link.get_text(strip=True)
            print(f"  - {text}: {href}")
        
        # Test each navigation link
        test_urls = [
            ('/', 'Home page'),
            ('/#sobre-nosotros', 'Sobre nosotros section'),
            ('/#proyectos', 'Proyectos section'),  
            ('/#contacto', 'Contacto section')
        ]
        
        print("\nTesting navigation URLs:")
        for url, description in test_urls:
            test_url = f"http://localhost:5000{url}"
            try:
                response = session.get(test_url)
                print(f"  - {description}: {response.status_code}")
            except Exception as e:
                print(f"  - {description}: ERROR - {e}")

if __name__ == "__main__":
    test_navigation()