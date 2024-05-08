from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from .models import User,Admin,Partner,Child
from werkzeug.security import generate_password_hash, check_password_hash
from . import db   ##means from __init__.py import db
from flask_login import login_user, login_required, logout_user, current_user
import os
from werkzeug.utils import secure_filename
from datetime import datetime

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

        ## USER ##  
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        surname = request.form.get('surname')
        bd = request.form.get('birthday')
        address = request.form.get('address')
        phone_number = request.form.get('phone_number')
        birthday= datetime.strptime(bd, '%Y-%m-%d').date()
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
            new_user = User(email=email, first_name=first_name, surname=surname, address=address, phone_number=phone_number, birthday=birthday, password=generate_password_hash(
                password1, method='pbkdf2:sha256'),nif=nif,user_profile_image_url=img_url)
            
            db.session.add(new_user)
            
            db.session.commit()
            login_user(new_user, remember=True)

            ## PARTNER ##

            if any(request.form.getlist('partnerName')):
                partner_name = request.form.get('partnerName')
                partner_birthday= datetime.strptime(bd, '%Y-%m-%d').date()
                partner_nif=request.form.get('partnerNIF')
                partner_phone_number = request.form.get('partnerPhoneNumber')
                new_partner = Partner(user_id= current_user.id, name=partner_name,nif=partner_nif,birthday=partner_birthday,phone_number=partner_phone_number)
                db.session.add(new_partner)
                db.session.commit()

            ## CHILDREN ##
            if 'childName_1' in request.form:  # Verifica si al menos se ha enviado información para un hijo
                children = []
                index = 1  # Comenzamos con el primer hijo
                while True:
                    # Comprobamos si existen los campos para el hijo actual
                    if f'childName_{index}' in request.form:
                        child_name = request.form.get(f'childName_{index}')
                        child_nif = request.form.get(f'childNIF_{index}')
                        child_birthday = datetime.strptime(request.form.get(f'childBirthday_{index}'), '%Y-%m-%d').date()
                        child_phone_number = request.form.get(f'childPhoneNumber_{index}')
                        
                        children.append({
                            'name': child_name,
                            'nif': child_nif,
                            'birthday': child_birthday,
                            'phone_number': child_phone_number
                        })
                        index += 1  # Pasamos al siguiente hijo
                    else:
                        break  # Salimos del bucle si no hay más hijos
                    
                # Procesar los datos de los hijos
                for child_data in children:
                    new_child = Child(
                        user_id=current_user.id, 
                        name=child_data['name'],
                        nif=child_data['nif'],
                        birthday=child_data['birthday'],
                        phone_number=child_data['phone_number']                    
                    )
                    db.session.add(new_child)
                
                db.session.commit()

            flash('Account created!', category='success')
            return redirect(url_for('views.home'))

    return render_template("sign_up.html", user=current_user)


def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']
