# __init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
import os
from flask_mail import Mail
from itsdangerous import URLSafeTimedSerializer
from authlib.integrations.flask_client import OAuth


db = SQLAlchemy()
mail = Mail()
DB_NAME = "database.db"
s = None  # Inicializamos s fuera de create_app

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'hjshjhdjah kjshkjdhjs'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    base_dir = os.path.dirname(os.path.abspath(__file__))
    upload_folder = os.path.join(base_dir, "static", "images")
    app.config['UPLOAD_FOLDER'] = upload_folder
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Configuración de Flask-Mail para usar Gmail
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'grematfginformatica@gmail.com'
    app.config['MAIL_PASSWORD'] = 'cqjubziosxffbssb'
    app.config['MAIL_DEFAULT_SENDER'] = 'grematfginformatica@gmail.com'
    

    # Configuración de OAuth
    global oauth
    oauth = OAuth()
    oauth.init_app(app)

    # Configuración de Google OAuth
    app.config['GOOGLE_CLIENT_ID'] = '557189735141-bbebcuh44lq5ldekpr4mol7kuh4i9vuk.apps.googleusercontent.com'
    app.config['GOOGLE_CLIENT_SECRET'] = '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'
    app.config['GOOGLE_DISCOVERY_URL'] = "https://accounts.google.com/.well-known/openid-configuration"

    google = oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        server_metadata_url=app.config['GOOGLE_DISCOVERY_URL'],
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
    global s  # Hacemos que s sea global para que sea accesible desde auth.py
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

    db.init_app(app)
    mail.init_app(app)
    
    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User, Admin, Event, Event_Attendance, Child, Partner, Fee
    
    with app.app_context():
        db.create_all()

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        user = User.query.get(int(id))
        admin = Admin.query.get(int(id))
        if admin:
            return admin
        else:
            return user

    return app


def create_database(app):
    if not path.exists('website/' + DB_NAME):
        db.create_all(app=app)
        print('Created Database!')
