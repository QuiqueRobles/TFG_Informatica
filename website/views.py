import os
import json
import pyqrcode
from flask import Blueprint, render_template, request, flash, jsonify, url_for,Flask, current_app, redirect, send_file, make_response
from flask_login import login_required, current_user
from .models import User,Admin,Event,Event_Attendance,Fee,Partner,Child
from . import db, mail
from datetime import datetime
from sqlalchemy.sql import func
from werkzeug.utils import secure_filename
import stripe
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image , Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_CENTER
import base64
from flask_mail import Mail, Message
#from pyzbar.pyzbar import decode




# This is your test secret API key.
stripe.api_key = 'sk_test_51OfpDEDOahdbfVYL96nj0GqiZBFZ29gMakRAGrfaL4pfNseHyPe6Q3R72I30lCGpjIqUXTKFqfY2VZT91xmfDGNy005JdTBKzm'

views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST': 
        create_event()
    todos_los_eventos = Event.query.all()
    eventos_activos = [evento for evento in todos_los_eventos if evento.date >= datetime.now()]
    event_details = calculate_event_details()
    if current_user.is_admin == True:
        print("Renderizando homeAdmin")
        return render_template("homeAdmin.html", user=current_user, active_event=eventos_activos, event_details=event_details)
    return render_template("home.html", user=current_user, active_event=eventos_activos, event_details=event_details)


@login_required
@views.route('/update-event/<int:event_id>', methods=['GET', 'POST'])
def update_event(event_id):
    event = Event.query.get_or_404(event_id)
    if request.method == 'POST':
        event.name = request.form['name']
        date_str=request.form['date']
        event.date = datetime.strptime(date_str, '%Y-%m-%d').date()
        event.max_guest_num = request.form['max_guest_num']
        event.member_price = request.form['member_price']
        event.member_child_price = request.form['member_child_price']
        event.guest_price = request.form['guest_price']
        event.description = request.form['description']
        
        if 'img_url' in request.files:
            img_file = request.files['img_url']
            if img_file:
                filename = secure_filename(img_file.filename)
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                img_file.save(filepath)
                img_url = url_for('static', filename=f'images/{filename}')
                event.img_url=img_url

        db.session.commit()

        return redirect(url_for('views.home')) # Redirect to the admin home or events page
    return render_template('update_event.html', event=event, user=current_user)

@views.route('/my_events', methods=['GET', 'POST'])
@login_required
def my_events():
    user_attendances = Event_Attendance.query.filter_by(user_id=current_user.id).all()
    events = [Event.query.get(attendance.event_id) for attendance in user_attendances]
    now = datetime.now()
    return render_template('my_events.html', user_attendances=user_attendances, events=events, user=current_user,now=now)

@views.route('/about_us', methods=['GET'])
def about_us():
    user_count = db.session.query(User).count()
    event_count = db.session.query(Event).count()
    family_count = db.session.query(Fee).count()
    
    return render_template('about_us.html', user=current_user, user_count=user_count, event_count=event_count, family_count=family_count)

@views.route('/become_member', methods=['GET', 'POST'])
@login_required
def become_member():
    return render_template('become_member.html', user=current_user)

@views.route('/delete-event/<int:event_id>', methods=['POST'])
def delete_event(event_id): 
    print("Deleting event")
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    return jsonify({'message': 'Event deleted successfully'})


@views.route('/event-attendance/<int:event_id>', methods=['GET', 'POST'])
@login_required
def event_attendance(event_id):    
    event_details = calculate_event_details()
    event = Event.query.get_or_404(event_id)
    user_fee = Fee.query.filter_by(user_fee=current_user.id).first()
    return render_template('event.html', event=event, user=current_user, user_fee=user_fee, event_details=event_details)




@views.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@views.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    if request.method == 'POST':
        # Obtener los datos del formulario de edición
        first_name = request.form['first_name']
        surname = request.form['surname']
        nif = request.form['nif']
        phone_number = request.form['phone_number']
        address = request.form['address']
        if not current_user.is_admin:
            birthday = request.form['birthday']
            try:
                birthday = datetime.strptime(birthday, '%Y-%m-%d').date()
            except:
                birthday = datetime.strptime('0001-01-01', '%Y-%m-%d').date()

        current_user.first_name = first_name
        current_user.surname = surname
        current_user.nif = nif
        current_user.phone_number = phone_number
        current_user.address = address
        if not current_user.is_admin:
            current_user.birthday = birthday

        # Procesar las imágenes de perfil si se han subido
        profile_image = request.files.get('profile_image')
        
        if profile_image and allowed_file(profile_image.filename):
            filename = secure_filename(profile_image.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            profile_image.save(filepath)
            img_url = url_for('static', filename=f'images/{filename}')
            if not current_user.is_admin:
                current_user.user_profile_image_url=img_url
            else:
                current_user.admin_profile_image_url=img_url

        

        # Actualizar información de la pareja
        if not current_user.is_admin and current_user.partner:
            for idx, partner in enumerate(current_user.partner):
                partner.name = request.form.get(f'partner_name_{idx+1}')
                partner.nif = request.form.get(f'partner_nif_{idx+1}')
                partner.phone_number = request.form.get(f'partner_phone_number_{idx+1}')
                partner_birthday = request.form.get(f'partner_birthday_{idx+1}')
                try:
                    partner_birthday = datetime.strptime(partner_birthday, '%Y-%m-%d').date()
                except:
                    partner_birthday = datetime.strptime('0001-01-01', '%Y-%m-%d').date()
                partner.birthday = partner_birthday

                partner_profile_image = request.files.get(f'partner_profile_image_{idx+1}')

                if partner_profile_image and allowed_file(partner_profile_image.filename):
                    
                    filename = secure_filename(partner_profile_image.filename)
                    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    partner_profile_image.save(filepath)
                    img_url = url_for('static', filename=f'images/{filename}')
                    partner.partner_profile_image_url=img_url

                
                    

        # Actualizar información de los hijos
        if not current_user.is_admin and current_user.children:
            for idx, child in enumerate(current_user.children):
                child.name = request.form.get(f'child_name_{idx+1}')
                child.nif = request.form.get(f'child_nif_{idx+1}')
                child.phone_number = request.form.get(f'child_phone_number_{idx+1}')
                child_birthday = request.form.get(f'child_birthday_{idx+1}')
                try:
                    child_birthday = datetime.strptime(child_birthday, '%Y-%m-%d').date()
                except:
                    child_birthday = datetime.strptime('0001-01-01', '%Y-%m-%d').date()
                child.birthday = child_birthday

                child_profile_image = request.files.get(f'child_profile_image_{idx+1}')
                if child_profile_image and allowed_file(child_profile_image.filename):
                    
                    filename = secure_filename(child_profile_image.filename)
                    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    child_profile_image.save(filepath)
                    img_url = url_for('static', filename=f'images/{filename}')
                    child.child_profile_image_url=img_url
                

        flash("Profile data updated correctly")
        db.session.commit()
        return render_template('profile.html', user=current_user)

    return render_template('profile.html', user=current_user)

@views.route('/delete_partner/<int:partner_id>', methods=['POST'])
def delete_partner(partner_id):
    partner = Partner.query.get_or_404(partner_id)
    user_id = partner.user_id  # Assuming there's a user_id foreign key in Partner
    db.session.delete(partner)
    db.session.commit()
    flash('Partner has been deleted successfully.', 'success')
    return redirect(url_for('views.profile'))

@views.route('/delete_child/<int:child_id>', methods=['POST'])
def delete_child(child_id):
    child = Child.query.get_or_404(child_id)
    user_id = child.user_id  # Assuming there's a user_id foreign key in Child
    db.session.delete(child)
    db.session.commit()
    flash('Child has been deleted successfully.', 'success')
    return redirect(url_for('views.profile'))

@views.route('/add_partner/<int:user_id>', methods=['POST'])
def add_partner(user_id):
    print(current_user.partner)
    if current_user.partner:
        print("wow")
        flash("You cannot have more than one partner", category='error')
        return render_template("profile.html",user=current_user)
    user = User.query.get_or_404(user_id)
    name = request.form['partner_name']
    nif = request.form['partner_nif']
    phone_number = request.form['partner_phone_number']
    birthday = request.form['partner_birthday']

    try:
        birthday = datetime.strptime(birthday, '%Y-%m-%d').date()
    except:
        birthday = datetime.strptime('0001-01-01', '%Y-%m-%d').date()

    profile_image = request.files['partner_profile_image']


    if profile_image and allowed_file(profile_image.filename):
        filename = secure_filename(profile_image.filename)
        filepath=os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        profile_image.save(filepath)
        img_url= url_for('static',filename=f'images/{filename}')
    else:
        img_url=url_for('static',filename=f'images/userLogo.png')

    partner = Partner(name=name, nif=nif, phone_number=phone_number, birthday=birthday, user_id=user.id,partner_profile_image_url=img_url)
    

    db.session.add(partner)
    db.session.commit()
    flash('Partner has been added successfully.', 'success')

    return redirect(url_for('views.profile'))

# Ruta para añadir un Child
@views.route('/add_child/<int:user_id>', methods=['POST'])
def add_child(user_id):
    user = User.query.get_or_404(user_id)
    name = request.form['child_name']
    nif = request.form['child_nif']
    phone_number = request.form['child_phone_number']
    child_birthday = request.form['child_birthday']
    try:
        child_birthday = datetime.strptime(child_birthday, '%Y-%m-%d').date()
    except:
        child_birthday = datetime.strptime('0001-01-01', '%Y-%m-%d').date()
    profile_image = request.files['child_profile_image']

    if profile_image and allowed_file(profile_image.filename):
        filename = secure_filename(profile_image.filename)
        filepath=os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        profile_image.save(filepath)
        img_url= url_for('static',filename=f'images/{filename}')
    else:
        img_url=url_for('static',filename=f'images/userLogo.png')

    child = Child(name=name, nif=nif, phone_number=phone_number, birthday=child_birthday, user_id=user.id, child_profile_image_url=img_url)
    
    db.session.add(child)
    db.session.commit()
    flash('Child has been added successfully.', 'success')
    return redirect(url_for('views.profile'))

@views.route('/success', methods=['GET', 'POST'])
@login_required
def success():
    payment_intent_id = request.args.get('payment_intent')
    if payment_intent_id:
        # Payment intent ID received, proceed to create entry in the database
        try:
            # Extraer los datos del formulario de la solicitud
            number_member_tickets = request.args.get('number_member_tickets')
            number_child_member_tickets = request.args.get('number_child_member_tickets')
            number_guest_tickets = request.args.get('number_guest_tickets')
            number_child_tickets = request.args.get('number_child_tickets')
            vip_admin_tickets= request.args.get('vip_admin_tickets')
            guests_names = request.args.get('guests_names')
            event_id = request.args.get('event_id')
            totalAmount= request.args.get('totalAmount')

            
            # Crear una nueva instancia de Event_Attendance con los datos del formulario
            event_attendance = Event_Attendance(
                number_member_tickets=number_member_tickets,
                number_memberchild_tickets=number_child_member_tickets,
                number_guest_tickets=number_guest_tickets,
                number_child_tickets=number_child_tickets,
                guests_names=guests_names,
                vip_admin_tickets=vip_admin_tickets,
                user_id=current_user.id,
                event_id=event_id,
                total_price=totalAmount,
                cash_payment_in_event=False
            )
            
            # Agregar la nueva instancia a la sesión y confirmar los cambios en la base de datos
            db.session.add(event_attendance)
            db.session.commit()

            msg = Message('GREMA MEMBERSHIP', recipients=[current_user.email])
            msg.body = f"""
            
            Thank you for purchasing GREMA tickets!!! We are looking forward to seeing you in the event with your family!
            
            number_member_tickets={number_member_tickets},
            number_memberchild_tickets={number_child_member_tickets},
            number_guest_tickets={number_guest_tickets},
            number_child_tickets={number_child_tickets},
            guests_names={guests_names},
            total_price={totalAmount},
            
            http://localhost:5000/my_events
            """
            mail.send(msg)

            
            return render_template('success.html')
        except Exception as e:
            # Manejar cualquier error que pueda ocurrir al crear la entrada en la base de datos
            print(e)
            return render_template('error.html', message='Failed to create database entry')
    else:
        # No se recibió el ID del intento de pago, manejar el error adecuadamente
        return render_template('error.html', message='Payment intent ID not provided')
    
@views.route('/success_cash_template', methods=['GET', 'POST'])
@login_required
def success_cash_template():
    return render_template('success.html')

@views.route('/success_vip', methods=['GET', 'POST'])
@login_required
def success_vip():
        try:
            # Extraer los datos del formulario de la solicitud
            data = request.json
            # Aquí puedes acceder a los datos del formulario
            number_member_tickets = data['number_member_tickets']
            number_child_member_tickets = data['number_child_member_tickets']
            number_guest_tickets = data['number_guest_tickets']
            number_child_tickets = data['number_child_tickets']
            vip_admin_tickets=data['vip_admin_tickets']
            guests_names = data['guests_names']
            totalAmount = data['totalAmount']
            event_id = data['event_id']

            
            # Crear una nueva instancia de Event_Attendance con los datos del formulario
            event_attendance = Event_Attendance(
                number_member_tickets=number_member_tickets,
                number_memberchild_tickets=number_child_member_tickets,
                number_guest_tickets=number_guest_tickets,
                number_child_tickets=number_child_tickets,
                vip_admin_tickets=vip_admin_tickets,
                guests_names=guests_names,
                user_id=current_user.id,
                event_id=event_id,
                total_price=totalAmount,
                cash_payment_in_event=False
            )
            
            # Agregar la nueva instancia a la sesión y confirmar los cambios en la base de datos
            db.session.add(event_attendance)
            db.session.commit()

            msg = Message('GREMA MEMBERSHIP', recipients=[current_user.email])
            msg.body = f"""
            
            Your VIP tickets have been booked. Enjoy

            VIP tickets: {vip_admin_tickets}
            
            http://localhost:5000/my_events
            """
            mail.send(msg)

            return render_template('success.html', user=current_user)
        except Exception as e:
            # Manejar cualquier error que pueda ocurrir al crear la entrada en la base de datos
            print(e)
            return render_template('error.html', message='Failed to create database entry')


@views.route('/success_free', methods=['GET', 'POST'])
@login_required
def success_free():
        try:
            # Extraer los datos del formulario de la solicitud
            data = request.json
            # Aquí puedes acceder a los datos del formulario
            number_member_tickets = data['number_member_tickets']
            number_memberchild_tickets = data['number_child_member_tickets']
            number_guest_tickets = data['number_guest_tickets']
            number_child_tickets = data['number_child_tickets']
            vip_admin_tickets=data['vip_admin_tickets']
            guests_names = data['guests_names']
            totalAmount = data['totalAmount']
            event_id = data['event_id']

            
            # Crear una nueva instancia de Event_Attendance con los datos del formulario
            event_attendance = Event_Attendance(
                number_member_tickets=number_member_tickets,
                number_memberchild_tickets=number_memberchild_tickets,
                number_guest_tickets=number_guest_tickets,
                number_child_tickets=number_child_tickets,
                vip_admin_tickets=vip_admin_tickets,
                guests_names=guests_names,
                user_id=current_user.id,
                event_id=event_id,
                total_price=totalAmount,
                cash_payment_in_event=False
            )
            
            # Agregar la nueva instancia a la sesión y confirmar los cambios en la base de datos
            db.session.add(event_attendance)
            db.session.commit()

            msg = Message('GREMA MEMBERSHIP', recipients=[current_user.email])
            msg.body = f"""
            
            Your free tickets have been booked. Enjoy

            Ticket info: 
            number_member_tickets={number_member_tickets},
            number_member_child_tickets={number_memberchild_tickets},
            number_guest_tickets={number_guest_tickets},
            number_child_tickets={number_child_tickets},
            vip_admin_tickets={vip_admin_tickets},
            guests_names={guests_names},
            total_price={totalAmount},
            
            http://localhost:5000/my_events
            """
            mail.send(msg)

            return render_template('success.html', user=current_user)
        except Exception as e:
            # Manejar cualquier error que pueda ocurrir al crear la entrada en la base de datos
            print(e)
            return render_template('error.html', message='Failed to create database entry')


@views.route('/success_cash', methods=['GET', 'POST'])
@login_required
def success_cash():
        try:
            # Extraer los datos del formulario de la solicitud
            data = request.json
            # Aquí puedes acceder a los datos del formulario
            number_member_tickets = data['number_member_tickets']
            number_child_member_tickets = data['number_child_member_tickets']
            number_guest_tickets = data['number_guest_tickets']
            number_child_tickets = data['number_child_tickets']
            vip_admin_tickets=data['vip_admin_tickets']
            guests_names = data['guests_names']
            totalAmount = data['totalAmount']
            event_id = data['event_id']

            
            # Crear una nueva instancia de Event_Attendance con los datos del formulario
            event_attendance = Event_Attendance(
                number_member_tickets=number_member_tickets,
                number_memberchild_tickets=number_child_member_tickets,
                number_guest_tickets=number_guest_tickets,
                number_child_tickets=number_child_tickets,
                vip_admin_tickets=vip_admin_tickets,
                guests_names=guests_names,
                user_id=current_user.id,
                event_id=event_id,
                total_price=totalAmount,
                cash_payment_in_event=True
            )
            
            # Agregar la nueva instancia a la sesión y confirmar los cambios en la base de datos
            db.session.add(event_attendance)
            db.session.commit()

            msg = Message('GREMA MEMBERSHIP', recipients=[current_user.email])
            msg.body = f"""
            
            Thank you for purchasing GREMA tickets!!! We are looking forward to seeing you in the event with your family!
            
            number_member_tickets={number_member_tickets},
            number_memberchild_tickets={number_child_member_tickets},
            number_guest_tickets={number_guest_tickets},
            number_child_tickets={number_child_tickets},
            guests_names={guests_names},
            total_price={totalAmount},
            
            RECUERDA QUE DEBES PAGAR EN EFECTIVO ALLÍ!
            
            http://localhost:5000/my_events
            """
            mail.send(msg)

            return render_template('success.html', user=current_user)
        except Exception as e:
            # Manejar cualquier error que pueda ocurrir al crear la entrada en la base de datos
            print(e)
            return render_template('error.html', message='Failed to create database entry')
    
@views.route('/success_membership', methods=['GET', 'POST'])
@login_required
def success_membership():
    payment_intent_id = request.args.get('payment_intent')
    if payment_intent_id:
        try:
            fee = Fee(
                payed= True,
                year= datetime.now().year,
                user_fee= current_user.id
            )
            # Agregar la nueva instancia a la sesión y confirmar los cambios en la base de datos
            db.session.add(fee)
            db.session.commit()
            msg = Message('GREMA MEMBERSHIP', recipients=[current_user.email])
            msg.body = f'Thank you for becoming part of the GREMA Association!!! We are looking forward to seeing you in events with your family!'
            mail.send(msg)
            return render_template('success_membership.html')
        except Exception as e:
            # Manejar cualquier error que pueda ocurrir al crear la entrada en la base de datos
            print(e)
            return render_template('error.html', message='Failed to create database entry')
    else:
        # No se recibió el ID del intento de pago, manejar el error adecuadamente
        return render_template('error.html', message='Payment intent ID not provided')

@views.route('/error', methods=['GET', 'POST'])
@login_required
def error():
    return render_template('error.html', message='An error was detected')


@views.route('/manage_event_attendances', methods=['GET', 'POST'])
@login_required
def manage_event_attendances():
    events = Event.query.all()
    users = User.query.all()
    user_attendances = None
    searched_user = None
    searched_event = None
    
    if request.method == 'POST':
        event_id = request.form.get('event_id')
        user_email = request.form.get('user_email')
        user_nif = request.form.get('user_nif')
        user_last_name = request.form.get('user_last_name')
        
        if event_id:
            searched_event = Event.query.filter_by(id=event_id).first()

        if user_email:
            searched_user = User.query.filter_by(email=user_email).first()
            if not searched_user:
                searched_user = Admin.query.filter_by(email=user_email).first()
        elif user_nif:
            searched_user = User.query.filter_by(nif=user_nif).first()
            if not searched_user:
                searched_user = Admin.query.filter_by(nif=user_nif).first()
        elif user_last_name:
            searched_user = User.query.filter_by(surname=user_last_name).first()
            if not searched_user:
                searched_user = Admin.query.filter_by(surname=user_last_name).first()

        if searched_user and searched_event:
            user_attendances = Event_Attendance.query.filter_by(event_id=event_id, user_id=searched_user.id).all()
            if user_attendances:
                return render_template('manage_event_attendances.html', user=current_user, events=events, users=users, user_attendances=user_attendances, searched_event=searched_event, searched_user=searched_user)
            else:
                msg_not_tickets = "This user does not have tickets for this event"
                return render_template('manage_event_attendances.html', user=current_user, events=events, users=users, msg_not_tickets=msg_not_tickets)
        else:
            flash('User not found', category='error')
            return render_template('manage_event_attendances.html', user=current_user, events=events, users=users)

    return render_template('manage_event_attendances.html', user=current_user, events=events, users=users)



@views.route('/manage_memberships', methods=['GET', 'POST'])
@login_required
def manage_memberships():
    if request.method == 'POST':
        
        if 'user_email_add' and 'year_add' in request.form:
            user_email = request.form['user_email_add']
            user = User.query.filter_by(email=user_email).first()
            if user:
                year = request.form['year_add']
                fee = Fee(payed=True,user_fee=user.id, year=year)
                db.session.add(fee)
                db.session.commit()
                flash('Membership added successfully', 'success')
                return redirect(url_for('views.manage_memberships'))
            else:
                flash('No user with this email was found', 'error')
                return redirect(url_for('views.manage_memberships'))
        elif 'user_email_delete' and 'year_delete' in request.form:
            print("Entra en el form de delete")
            user_email = request.form['user_email_delete']
            year = request.form['year_delete']
            user = User.query.filter_by(email=user_email).first()
            fee = Fee.query.filter_by(user_fee=user.id, year=year).first()
            if fee:
                db.session.delete(fee)
                db.session.commit()
                flash('Membership removed successfully', 'success')
                return redirect(url_for('views.manage_memberships'))
            else:
                flash('Membership not found', 'error')
                return redirect(url_for('views.manage_memberships'))
    else:
        return render_template('manage_memberships.html', user=current_user)
    
@views.route('/check_fee', methods=['POST'])
@login_required
def check_fee():
    user_email = request.form.get('user_email')
    # Buscar al usuario por su correo electrónico
    user = User.query.filter_by(email=user_email).first()

    if user:
        # Buscar si el usuario tiene una cuota
        fee = Fee.query.filter_by(user_fee=user.id).first()

        if fee:
            user_fee_info = {
                'user_email': user.email,
                'has_fee': True,
                'year': fee.year
            }
        else:
            user_fee_info = {
                'user_email': user.email,
                'has_fee': False,
                'year': None
            }
    else:
        flash('User not found', 'error')
        return redirect(url_for('views.manage_memberships'))

    return render_template('manage_memberships.html', user_fee_info=user_fee_info, user=current_user)

@views.route('/download_event_pdf/<int:event_id>', methods=['POST'])
def download_event_pdf(event_id):
    # Obtener la información del evento
    event = Event.query.get(event_id)
    user_attendance = Event_Attendance.query.filter_by(event_id=event_id, user_id=current_user.id).first()
    # Generar el PDF
    pdf_data = generate_event_pdf(event, user_attendance,current_user)
    # Crear la respuesta del PDF
    response = make_response(pdf_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=event_{event_id}.pdf'
    return response

@views.route('/check-ticket-availability', methods=['POST'])
@login_required
def check_ticket_availability():
    try:
        data = request.get_json()
        
        # Verificación de los datos recibidos
        print("Datos recibidos:", data)
        
        # Obtener los datos del formulario
        number_member_tickets = int(data.get('number_member_tickets', 0))
        number_child_member_tickets = int(data.get('number_child_member_tickets', 0))
        number_guest_tickets = int(data.get('number_guest_tickets', 0))
        number_child_tickets = int(data.get('number_child_tickets', 0))
        vip_admin_tickets=int(data.get('vip_admin_tickets',0))
        event_id = int(data.get('event_id'))

        
        total_tickets = number_member_tickets + number_child_member_tickets + number_guest_tickets + number_child_tickets + vip_admin_tickets
        
        # Verificar que no se superen las entradas disponibles
        event = Event.query.filter_by(id=event_id).first()
        
        if not event:
            return jsonify({"error": "Event not found"}), 404
        
        print("Evento encontrado:", event)
        
        attendances = Event_Attendance.query.filter_by(event_id=event_id).all()
        
        total_tickets_sold = sum(
            (attendance.number_guest_tickets or 0) + 
            (attendance.number_child_tickets or 0) + 
            (attendance.number_member_tickets or 0) + 
            (attendance.number_memberchild_tickets or 0)
            for attendance in attendances
        )
        
        print("Total de entradas vendidas:", total_tickets_sold)
        print("Total de entradas solicitadas:", total_tickets)
        
        if total_tickets_sold + total_tickets > event.max_guest_num:
            return jsonify({"available": False, "message": "Not enough tickets available"}), 403
        
        return jsonify({"available": True})
    except Exception as e:
        print("Error:", str(e))
        return jsonify(error=str(e)), 403


@views.route('/create-payment-intent', methods=['POST'])
@login_required
def create_payment():
    try:
        data = json.loads(request.data) 

        # Obtener los datos del formulario
        number_member_tickets = data.get('number_member_tickets')
        number_child_member_tickets = data.get('number_child_member_tickets')
        number_guest_tickets = data.get('number_guest_tickets')
        number_child_tickets = data.get('number_child_tickets')  
        event_id = data.get('event_id')
        

        total_amount = float(data.get('totalAmount'))
        receipt_email = current_user.email
        
        #Calculate amount for Stripe
        amountStripe= int(total_amount*100)
        
        intent = stripe.PaymentIntent.create(
            amount=amountStripe,
            currency='eur',
            automatic_payment_methods={
                'enabled': True,
            },
            receipt_email=receipt_email
        )
        return jsonify({
            'clientSecret': intent['client_secret']
        })
    except Exception as e:
        return jsonify(error=str(e)), 403
    

@views.route('/process_qr', methods=['POST'])
def process_qr():
    try:
        # Asegurarse de que se recibe el JSON correctamente
        data = request.json.get('data', '')
        print(f"Raw data received: {data}")

        # Si data es un string JSON, cargarlo como diccionario
        if isinstance(data, str):
            data = json.loads(data)

        # Extraer los datos del QR
        qr_info = {}
        for line in data.split('\n'):
            if ':' in line:
                key, value = line.split(': ', 1)
                qr_info[key.strip()] = value.strip()

        print(f"Extracted QR Info: {qr_info}")

        # Verificar si la información del QR coincide con los registros en la base de datos
        event_name = qr_info.get('Event')
        date_str = qr_info.get('Date')
        description = qr_info.get('Description')
        user_name = qr_info.get('User')
        user_email = qr_info.get('Email')
        member_tickets = int(qr_info.get('Member Tickets', 0))
        guest_tickets = int(qr_info.get('Guest Tickets', 0))
        child_tickets = int(qr_info.get('Child Tickets', 0))
        member_child_tickets = int(qr_info.get("Member's Child Tickets", 0))
        total_price = float(qr_info.get('Total Price', '').replace('$', '').replace(',', ''))
        paid = qr_info.get('Paid', '').lower() == "yes"

        # Buscar en la base de datos los registros que coincidan con la información del QR
        event = Event.query.filter_by(name=event_name).first()
        if event:
            if event.date.strftime('%B %d, %Y') == date_str:
                user = User.query.filter_by(email=user_email).first()
                if user:
                    user_attendance = Event_Attendance.query.filter_by(user_id=user.id, event_id=event.id).first()
                    if user_attendance:
                        # Comprobar si los detalles de la asistencia coinciden
                        if (user_attendance.number_member_tickets == member_tickets and
                                user_attendance.number_guest_tickets == guest_tickets and
                                user_attendance.number_child_tickets == child_tickets and
                                user_attendance.number_memberchild_tickets == member_child_tickets and
                                user_attendance.total_price == total_price and
                                paid):
                            flash("Correct ticket!! Enjoy the event!!")
                            return jsonify({"status": "success", "message": "QR data is correct.", "data": qr_info})
                        elif (user_attendance.number_member_tickets == member_tickets and
                                user_attendance.number_guest_tickets == guest_tickets and
                                user_attendance.number_child_tickets == child_tickets and
                                user_attendance.number_memberchild_tickets == member_child_tickets and
                                user_attendance.total_price == total_price and not paid):
                            flash("Correct ticket!! Enjoy the event!!")
                            flash("El usuario debe pagar en efectivo", "orange")
                            return jsonify({"status": "success", "message": "QR data is correct.", "data": qr_info})
                        else:
                            return jsonify({"status": "error", "message": "QR data does not match the records."})
                    else:
                        return jsonify({"status": "error", "message": "User attendance not found."})
                else:
                    return jsonify({"status": "error", "message": "User not found."})
            else:
                return jsonify({"status": "error", "message": "Event details do not match the records."})
        else:
            return jsonify({"status": "error", "message": "Event not found."})
    except Exception as e:
        print(f"Error processing QR: {e}")
        return jsonify({"status": "error", "message": "An error occurred while processing the QR code."})




@views.route('/qr_reader', methods=['GET','POST'])
def reader_qr():
    return render_template('qr_reader.html', user=current_user)


@views.route('/download_event_attendees', methods=['POST'])
@login_required
def download_event_attendees():
    event_id = request.form.get('event_id')
    event = Event.query.get(event_id)
    attendances = Event_Attendance.query.filter_by(event_id=event_id).all()

    if not event or not attendances:
        flash('No attendees found for this event', 'error')
        return redirect(url_for('manage_event_attendances'))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()

    elements = []
    
    # Estilos para el título y subtítulo
    title_style = styles['Title']
    subtitle_style = styles['Heading3']
    
    # Estilo para el texto normal en la tabla
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=10,  # Tamaño de letra reducido para que quepa mejor en la página
        textColor=colors.black,
        alignment=1,
    )
    
    # Estilo para el encabezado de la tabla
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=normal_style,
        fontSize=10,
        textColor=colors.white,
        alignment=1,
        fontName='Helvetica-Bold'
    )

    # Título y subtítulo
    elements.append(Paragraph(f"Attendees of {event.name}", title_style))
    elements.append(Paragraph(f"Event Date: {event.date}", subtitle_style))
    elements.append(Spacer(1, 12))

    # Datos de la tabla
    table_data = [
        [Paragraph('User Name', table_header_style),
         Paragraph('User Email', table_header_style),
         Paragraph('Vip Tickets', table_header_style),
         Paragraph('Guest Tickets', table_header_style),
         Paragraph('Child Tickets', table_header_style),
         Paragraph('Member Tickets', table_header_style),
         Paragraph('Member Child Tickets', table_header_style)]
    ]

    for attendance in attendances:
        admin = Admin.query.get(attendance.user_id)
        user = User.query.get(attendance.user_id)
        if user:
            guest_names = attendance.guests_names.split(', ')

            table_data.append([
                Paragraph(user.first_name + ' ' + user.surname, normal_style),
                Paragraph(user.email, normal_style),
                Paragraph(str(attendance.vip_admin_tickets), normal_style),
                Paragraph(str(attendance.number_guest_tickets), normal_style),
                Paragraph(str(attendance.number_child_tickets), normal_style),
                Paragraph(str(attendance.number_member_tickets), normal_style),
                Paragraph(str(attendance.number_memberchild_tickets), normal_style)
            ])

        if admin:
            guest_names = attendance.guests_names.split(', ')
            table_data.append([
                Paragraph(admin.first_name + ' ' + admin.surname, normal_style),
                Paragraph(admin.email, normal_style),
                Paragraph(str(attendance.vip_admin_tickets), normal_style),
                Paragraph(str(attendance.number_guest_tickets), normal_style),
                Paragraph(str(attendance.number_child_tickets), normal_style),
                Paragraph(str(attendance.number_member_tickets), normal_style),
                Paragraph(str(attendance.number_memberchild_tickets), normal_style)
            ])


    # Especificar los anchos de las columnas
    column_widths = [120, 120, 60, 60, 60, 60, 60]
    # Creación de la tabla
    table = Table(table_data,colWidths=column_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name=f"attendees_{event.name}.pdf", mimetype='application/pdf')


#################################################
#################################################

#FUNCTIONS#

def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def create_event():
    name=request.form.get('name')
    date_str=request.form.get('date')
    date = datetime.strptime(date_str, '%Y-%m-%d').date()
    max_guest_num=int(request.form.get('max_guest_num'))
    member_price=float(request.form.get('member_price'))
    member_child_price=float(request.form.get('member_child_price'))
    child_price=float(request.form.get('child_price'))
    guest_price=float(request.form.get('guest_price'))
    description=request.form.get('description')
    event_image = request.files['img_url']
    print(request.form.get('isFamilyFriendly'))
    is_family_friendly = request.form.get('isFamilyFriendly') == 'on'
    print(is_family_friendly)
    if event_image and allowed_file(event_image.filename):
        # Asegurar el nombre del archivo
        filename = secure_filename(event_image.filename)
        # Guardar la imagen en la carpeta "static"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        event_image.save(filepath)
        print(url_for('static',filename=f'images/{filename}'))
        # Obtener la URL relativa de la imagen
        img_url = url_for('static',filename=f'images/{filename}')
    else: 
        img_url=url_for('static',filename=f'images/gremaLogo.png')
        
    #AQUÍ HAY QUE CONTROLAR ALGUNOS ERRORES AL RELLENAR EL FORM
    new_event = Event(name=name, date=date, max_guest_num=max_guest_num, member_price=member_price, member_child_price=member_child_price, guest_price=guest_price, child_price=child_price, img_url=img_url, description=description, admin_id=current_user.id, is_family_friendly=is_family_friendly)
    db.session.add(new_event) #adding the note to the database 
    db.session.commit()
    flash('Event added correctly!', category='success')
    return 


@views.context_processor
def inject_membership():
    if current_user.is_authenticated:
        is_member = Fee.query.filter_by(user_fee=current_user.id, payed=True).first() is not None
    else:
        is_member = False
    return dict(is_member=is_member)




def generate_event_pdf(event, user_attendance, current_user):
    # Crear un documento PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    # Estilo para los encabezados y el texto del documento
    styles = getSampleStyleSheet()
    style_heading = styles['Heading1']
    style_normal = styles['Normal']

    # Encabezado del ticket
    event_name = Paragraph(event.name, style_heading)
    event_date = Paragraph(f"Date: {event.date.strftime('%B %d, %Y')}", style_normal)
    event_description = Paragraph(f"Description: {event.description}", style_normal)

    # Información de asistencia del usuario
    if current_user.is_admin:
        user_name =f"{current_user.first_name}"
    else:
        user_name = f"{current_user.first_name} {current_user.surname}"
    
    user_email = current_user.email
    ticket_info = [
        [Paragraph("Attendee:", style_normal), user_name],
        [Paragraph("Email:", style_normal), user_email],
        [Paragraph("Event Name:", style_normal), event.name],
        [Paragraph("Event Date:", style_normal), event.date.strftime('%B %d, %Y')],
        [Paragraph("Description:", style_normal), event.description],
        [Paragraph("Tickets:", style_normal), {
            "VIP": user_attendance.vip_admin_tickets,
            "Member": user_attendance.number_member_tickets,
            "Guest": user_attendance.number_guest_tickets,
            "Child": user_attendance.number_child_tickets,
            "Member's Child": user_attendance.number_memberchild_tickets
        }],
        [Paragraph("Total Price:", style_normal), f"${user_attendance.total_price}"],
        [Paragraph("Guest Names:", style_normal), user_attendance.guests_names],
        [Paragraph("Paid:", style_normal), "Yes" if not user_attendance.cash_payment_in_event else "No"]
    ]

    # Crear la tabla de información del ticket
    ticket_table = Table(ticket_info)
    ticket_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10)
    ]))

    # Logo de la Asociación GREMA
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(base_dir, "static", "images", "gremaLogo.png")
    print(logo_path)
    logo = Image(logo_path, width=100, height=100)

    # Crear el código QR
    qr_data = f"""
    Event: {event.name}
    Date: {event.date.strftime('%B %d, %Y')}
    Description: {event.description}
    User: {user_name}
    Email: {user_email}
    Vip Tickets: {user_attendance.vip_admin_tickets}
    Member Tickets: {user_attendance.number_member_tickets}
    Guest Tickets: {user_attendance.number_guest_tickets}
    Child Tickets: {user_attendance.number_child_tickets}
    Member's Child Tickets: {user_attendance.number_memberchild_tickets}
    Total Price: ${user_attendance.total_price}
    Paid: {"Yes" if not user_attendance.cash_payment_in_event else "No"}
    """
    qr = pyqrcode.create(qr_data)

    # Guardar el código QR en un archivo temporal
    qr_temp_file = BytesIO()
    qr.png(qr_temp_file, scale=5)

    # Leer el código QR desde el archivo temporal
    qr_img = Image(qr_temp_file)
    qr_img.drawHeight = 100
    qr_img.drawWidth = 100

    # Construir el contenido del PDF
    content = [
        logo,
        event_name,
        event_date,
        event_description,
        Spacer(1, 12),
        ticket_table,
        Spacer(1, 12),
        qr_img
    ]

    # Construir el documento PDF
    doc.build(content)

    # Devolver el contenido del PDF
    buffer.seek(0)
    return buffer.getvalue()

def calculate_event_details():
    todos_los_eventos = Event.query.all()
    eventos_activos = [evento for evento in todos_los_eventos if evento.date >= datetime.now()]
    event_details = []

    for event in eventos_activos:
        attendances = Event_Attendance.query.filter_by(event_id=event.id).all()
        
        total_tickets_sold = sum(
            (attendance.vip_admin_tickets or 0) +
            (attendance.number_guest_tickets or 0) + 
            (attendance.number_child_tickets or 0) + 
            (attendance.number_member_tickets or 0) + 
            (attendance.number_memberchild_tickets or 0) 
            for attendance in attendances
        )
        
        tickets_remaining = event.max_guest_num - total_tickets_sold
        
        if (total_tickets_sold/event.max_guest_num > 0.6):
            warning_few_tickets= True
        else:
            warning_few_tickets=False
            
        if (total_tickets_sold/event.max_guest_num==1):
            sold_out=True
        else:
            sold_out=False
            
        event_details.append({
            'event': event.id,
            'tickets_remaining': tickets_remaining,
            'warning_few_tickets': warning_few_tickets,
            'sold_out':sold_out
        })

    return event_details