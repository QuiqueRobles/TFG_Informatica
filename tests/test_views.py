# tests/test_views.py

from main import app
import pytest
from flask_login import current_user
from website.models import Event,User,db

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

def test_login_as_admin(client):
    response = client.post('/login', data={'email': 'qroblesuriel@gmail.com', 'password': 'quique'}, follow_redirects=True)
    assert b'You are the boss now. Create and destroy. ADMIN MODE ACTIVATED' in response.data  # Verifica que el inicio de sesión sea exitoso

# Prueba de registro de usuario
def test_register_user(client):
    # Simular una solicitud de registro con datos válidos
    with open('tests/test_images/userLogo.png', 'rb') as f:
        response = client.post('/sign-up', 
                               data={'email': 'test3@example.com', 
                                     'firstName': 'Test', 
                                     'profile_image': (f, 'userLogo.png'), 
                                     'password1': 'password', 
                                     'password2': 'password', 
                                     'NIF': '12345678A',
                                     'birthday': '2024-12-12'                                      
                                     },
                                     
                               follow_redirects=True)
    
    # Verificar que se muestre un mensaje de éxito después del registro
    assert b'Events' in response.data

    # Verificar que el usuario se haya creado en la base de datos
    user = User.query.filter_by(email='test3@example.com').first()
    assert user is not None
    db.session.delete(user)
    db.session.commit()


# Prueba de cierre de sesión
def test_logout(client):
    client.post('/login', data={'username': 'quiquemich@gmail.com', 'password': 'password'}, follow_redirects=True)
    response = client.get('/logout', follow_redirects=True)
    assert b'Login' in response.data

# Prueba de creación de evento
def test_create_event(client):
    login_as_admin(client)
    # Simular una solicitud de creación de evento con datos válidos
    with open('tests/test_images/eventoEjemplo.jpeg', 'rb') as f:
        response = client.post('/', 
                               data={'name': 'NombreDeEventoTest', 
                                     'date': '2024-05-01',
                                     'max_guest_num': 100,
                                     'member_price': 20,
                                     'member_child_price': 10,
                                     'child_price': 15,
                                     'guest_price': 30,
                                     'img_url': (f, 'eventoEjemplo.jpeg'),
                                     'description': 'This is a test event'}, 
                               follow_redirects=True)
    
    # Verificar que se muestre un mensaje de éxito después de crear el evento
    assert b'Event added correctly!' in response.data

    # Verificar que el evento se haya creado en la base de datos
    event = Event.query.filter_by(name='NombreDeEventoTest').first()
    assert event is not None

    # Eliminar el evento creado después de la prueba
    db.session.delete(event)
    db.session.commit()

def test_delete_event(client):
    # Iniciar sesión como administrador
    login_as_admin(client)

    # Crear un evento de prueba
    create_test_event(client)

    # Obtener el ID del evento creado
    event_id = Event.query.filter_by(name='NombreDeEventoTest').first().id

    # Simular una solicitud para eliminar el evento recién creado
    response = client.post(f'/delete-event/{event_id}', follow_redirects=True)

    # Verificar que se muestre un mensaje de éxito después de eliminar el evento
    assert b'Event deleted successfully' in response.data

    # Verificar que el evento haya sido eliminado de la base de datos
    event = Event.query.get(event_id)
    assert event is None



#################################################################
################################################################


def login_as_user(client):
    response= client.post('/login', data={'email': 'quiquemich@gmail.com', 'password': 'password'}, follow_redirects=True)
    return

def login_as_admin(client):
    response = client.post('/login', data={'email': 'qroblesuriel@gmail.com', 'password': 'quique'}, follow_redirects=True)
    assert b'You are the boss now. Create and destroy. ADMIN MODE ACTIVATED' in response.data  # Verifica que el inicio de sesión sea exitoso

def create_test_event(client):
    with open('tests/test_images/eventoEjemplo.jpeg', 'rb') as f:
        response = client.post('/', 
                               data={'name': 'NombreDeEventoTest', 
                                     'date': '2024-05-01',
                                     'max_guest_num': 100,
                                     'member_price': 20,
                                     'member_child_price': 10,
                                     'child_price': 15,
                                     'guest_price': 30,
                                     'img_url': (f, 'eventoEjemplo.jpeg'),
                                     'description': 'This is a test event'}, 
                               follow_redirects=True)
    return response