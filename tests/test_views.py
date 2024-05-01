# tests/test_views.py

from main import app
import pytest
from flask_login import current_user

# Fixture para configurar el cliente de prueba
@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# Prueba de inicio de sesión exitoso
def test_login_successful(client):
    # Simular una solicitud de inicio de sesión con credenciales válidas
    response = client.post('/login', data={'email': 'quiquemich@gmail.com', 'password': 'password'}, follow_redirects=True)
    
    # Verificar que la página de inicio se cargue después del inicio de sesión exitoso
    assert b'Events' in response.data and current_user.is_authenticated  # Ajusta este texto según lo que esperas que aparezca en la página de inicio después del inicio de sesión exitoso

# Prueba de inicio de sesión fallido
def test_login_failed(client):
    # Simular una solicitud de inicio de sesión con credenciales inválidas
    response = client.post('/login', data={'email': 'correo_incorrecto@example.com', 'password': 'contraseña_incorrecta'}, follow_redirects=True)
    print(response)
    # Verificar que la página de inicio de sesión se recargue después del inicio de sesión fallido
    assert b'Login' in response.data  # Ajusta este texto según lo que esperas que aparezca en la página de inicio de sesión después del inicio de sesión fallido
