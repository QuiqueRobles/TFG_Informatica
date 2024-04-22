from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from .models import User,Admin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db   ##means from __init__.py import db
from flask_login import login_user, login_required, logout_user, current_user
import os
from werkzeug.utils import secure_filename

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        admin= Admin.query.filter_by(email=email).first()
        user = User.query.filter_by(email=email).first()
        if admin:
            if check_password_hash(admin.password, password):
                flash('Logged in successfully as ADMIN!', category='success')
                login_user(admin, remember=False)
                print("Contraseña de admin aceptada")
                return redirect(url_for('views.home'))
            elif not user and not admin:
                flash('Incorrect password for admin, try again.', category='error')
                return render_template("login.html", user=current_user)
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                print("Contraseña de user aceptada")
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')
    return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        profile_image= request.files['profile_image']
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        nif=request.form.get('NIF')
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(first_name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            if profile_image and allowed_file(profile_image.filename):
                # Asegurar el nombre del archivo
                filename = secure_filename(profile_image.filename)
                # Guardar la imagen en la carpeta "static"
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                print(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                profile_image.save(filepath)
                print(url_for('static',filename=f'images/{filename}'))
            # Obtener la URL relativa de la imagen
                img_url = url_for('static',filename=f'images/{filename}')
            else: 
                img_url=url_for('static',filename=f'images/userLogo.png')
            new_user = User(email=email, first_name=first_name, password=generate_password_hash(
                password1, method='pbkdf2:sha256'),nif=nif,user_profile_image_url=img_url)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('views.home'))

    return render_template("sign_up.html", user=current_user)


def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']
