# tests/test_views.py

from main import app
import pytest
import json
from datetime import date
from flask_login import current_user
from website.models import Event,User,db,Fee,Partner,Child

# Fixture para configurar el cliente de prueba
@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# Prueba de inicio de sesión exitoso
def test_login_successful(client):
    # Simular una solicitud de inicio de sesión con credenciales válidas
    response = client.post('/login', data={'email': 'user@gmail.com', 'password': 'userTFG_2024'}, follow_redirects=True)
    
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
    response = client.post('/login', data={'email': 'admin@gmail.com', 'password': 'adminTFG_2024'}, follow_redirects=True)
    assert b'Welcome to GREMA Events Admin' in response.data  # Verifica que el inicio de sesión sea exitoso

# Prueba de registro de usuario
# Prueba de registro de usuario
def test_register_user(client):
    # Simular una solicitud de registro con datos válidos
    with open('test_images/userLogo.png', 'rb') as f:
        response = client.post('/sign-up', 
                               data={'email': 'test3@example.com', 
                                     'firstName': 'Test', 
                                     'surname': 'User', 
                                     'profile_image': (f, 'userLogo.png'), 
                                     'password1': 'password', 
                                     'password2': 'password', 
                                     'NIF': '12345678A',
                                     'birthday': '2024-12-12',
                                     'phone_number': '123456789',
                                     'address': '123 Test Street'
                                    },
                               follow_redirects=True)
    
    # Verificar que el usuario se haya creado en la base de datos
    user = User.query.filter_by(email='test3@example.com').first()
    assert user is not None
    assert user.first_name == 'Test'
    assert user.surname == 'User'
    assert user.nif == '12345678A'
    assert user.birthday.strftime('%Y-%m-%d') == '2024-12-12'
    assert user.phone_number == 123456789
    assert user.address == '123 Test Street'

    # Limpiar la base de datos eliminando el usuario creado
    db.session.delete(user)
    db.session.commit()

def test_register_user_with_children(client):
    # Simular una solicitud de registro con datos válidos
    with open('test_images/userLogo.png', 'rb') as profile_img:
        with open('test_images/userLogo.png', 'rb') as child_img:
            response = client.post('/sign-up', 
                                   data={'email': 'test_with_children@example.com', 
                                         'firstName': 'Test', 
                                         'surname': 'UserWithChildren', 
                                         'profile_image': (profile_img, 'userLogo.png'), 
                                         'password1': 'password', 
                                         'password2': 'password', 
                                         'NIF': '12345678A',
                                         'birthday': '2024-12-12',
                                         'phone_number': '123456789',
                                         'address': '123 Test Street',
                                         'familyStatus': 'children',
                                         'childrenCount': '2',
                                         'childName_1': 'Child1',
                                         'childNIF_1': 'C12345678A',
                                         'childBirthday_1': '2020-01-01',
                                         'childPhoneNumber_1': '987654321',
                                         'child_image_1': (child_img, 'childLogo.png'),
                                         'childName_2': 'Child2',
                                         'childNIF_2': 'C87654321A',
                                         'childBirthday_2': '2021-02-02',
                                         'childPhoneNumber_2': '987654322',
                                         'child_image_2': (child_img, 'childLogo.png')
                                        },
                                   follow_redirects=True)
    
    # Verificar que el usuario se haya creado en la base de datos
    user = User.query.filter_by(email='test_with_children@example.com').first()
    assert user is not None
    assert user.first_name == 'Test'
    assert user.surname == 'UserWithChildren'
    assert user.nif == '12345678A'
    assert user.birthday.strftime('%Y-%m-%d') == '2024-12-12'
    assert user.phone_number == 123456789
    assert user.address == '123 Test Street'

    # Verificar que los hijos se hayan creado en la base de datos
    children = user.children  # Suponiendo que tienes una relación de hijos en el modelo User
    assert len(children) == 2

    child1 = children[0]
    assert child1.name == 'Child1'
    assert child1.nif == 'C12345678A'
    assert child1.birthday.strftime('%Y-%m-%d') == '2020-01-01'
    assert child1.phone_number == 987654321

    child2 = children[1]
    assert child2.name == 'Child2'
    assert child2.nif == 'C87654321A'
    assert child2.birthday.strftime('%Y-%m-%d') == '2021-02-02'
    assert child2.phone_number == 987654322

    # Limpiar la base de datos eliminando el usuario creado y sus hijos
    db.session.delete(user)
    db.session.commit()


def test_register_user_with_partner(client):
    # Simular una solicitud de registro con datos válidos
    with open('test_images/userLogo.png', 'rb') as profile_img:
        with open('test_images/userLogo.png', 'rb') as partner_img:
            response = client.post('/sign-up', 
                                   data={'email': 'test_with_partner@example.com', 
                                         'firstName': 'Test', 
                                         'surname': 'UserWithPartner', 
                                         'profile_image': (profile_img, 'userLogo.png'), 
                                         'password1': 'password', 
                                         'password2': 'password', 
                                         'NIF': '12345678A',
                                         'birthday': '2024-12-12',
                                         'phone_number': '123456789',
                                         'address': '123 Test Street',
                                         'familyStatus': 'partner',
                                         'partnerName': 'PartnerName',
                                         'partnerNIF': 'P12345678A',
                                         'partnerBirthday': '2023-11-11',
                                         'partnerPhoneNumber': '987654321',
                                         'partner_image': (partner_img, 'partnerLogo.png')
                                        },
                                   follow_redirects=True)
    
    # Verificar que el usuario se haya creado en la base de datos
    user = User.query.filter_by(email='test_with_partner@example.com').first()
    assert user is not None
    assert user.first_name == 'Test'
    assert user.surname == 'UserWithPartner'
    assert user.nif == '12345678A'
    assert user.birthday.strftime('%Y-%m-%d') == '2024-12-12'
    assert user.phone_number == 123456789
    assert user.address == '123 Test Street'

    # Verificar que la pareja se haya creado en la base de datos
    partner = user.partner  # Suponiendo que tienes una relación de pareja en el modelo User
    partner = partner[0]
    assert partner is not None
    assert partner.name == 'PartnerName'
    assert partner.nif == 'P12345678A'
    assert partner.birthday.strftime('%Y-%m-%d') == '2023-11-11'
    assert partner.phone_number == 987654321

    # Limpiar la base de datos eliminando el usuario creado y su pareja
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
    with open('test_images/eventoEjemplo.jpeg', 'rb') as f:
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

def test_search_upcoming_events(client):
    login_as_admin(client)

    # Crear un evento de prueba
    create_test_event(client)

    # Simular la búsqueda de un evento
    response = client.get('/?search=NombreDeEventoTest', follow_redirects=True)
    assert b'NombreDeEventoTest' in response.data

    # Limpiar la base de datos eliminando el evento creado
    event = Event.query.filter_by(name='NombreDeEventoTest').first()
    db.session.delete(event)
    db.session.commit()


def test_family_friendly_events(client):
    login_as_admin(client)

    # Crear un evento de prueba familiar
    with open('test_images/eventoEjemplo.jpeg', 'rb') as f:
        response = client.post('/', 
                               data={'name': 'FamilyEventTest', 
                                     'date': '2024-05-01',
                                     'max_guest_num': 100,
                                     'member_price': 20,
                                     'member_child_price': 10,
                                     'child_price': 15,
                                     'guest_price': 30,
                                     'img_url': (f, 'eventoEjemplo.jpeg'),
                                     'description': 'This is a family test event',
                                     'isFamilyFriendly': True}, 
                               follow_redirects=True)
    
    # Verificar que se muestre un mensaje de éxito después de crear el evento
    assert b'Event added correctly!' in response.data

    # Simular la visualización de eventos familiares
    response = client.get('/', follow_redirects=True)
    assert b'FamilyEventTest' in response.data

    # Limpiar la base de datos eliminando el evento creado
    event = Event.query.filter_by(name='FamilyEventTest').first()
    db.session.delete(event)
    db.session.commit()




#################################################################
################################################################


def login_as_user(client):
    response= client.post('/login', data={'email': 'quiquemich@gmail.com', 'password': 'password'}, follow_redirects=True)
    return

def login_as_admin(client):
    response = client.post('/login', data={'email': 'qroblesuriel@gmail.com', 'password': 'quique'}, follow_redirects=True)
    assert b'Welcome to GREMA Events Admin' in response.data  # Verifica que el inicio de sesión sea exitoso

def create_test_event(client):
    with open('test_images/eventoEjemplo.jpeg', 'rb') as f:
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

def create_test_user(client):
    with app.app_context():
        user = User(email='testuser@example.com', first_name='Test', surname='User', password='password', nif="12345678A",
                    phone_number="123456789", address="123 Test St", birthday=date(1980, 1, 1), is_admin=False)
        db.session.add(user)
        db.session.commit()
    return user

def login_as_user_payment(client, user):
    with client.session_transaction() as sess:
        sess['_user_id'] = user.id