import os
import json
from flask import Blueprint, render_template, request, flash, jsonify, url_for,Flask, current_app, redirect
from flask_login import login_required, current_user
from .models import User,Admin,Event,Event_Attendance,Fee
from . import db
from datetime import datetime
from sqlalchemy.sql import func
from werkzeug.utils import secure_filename
import stripe



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
    
    if current_user.is_admin == True:
        print("Renderizando homeAdmin")
        return render_template("homeAdmin.html", user=current_user, active_event=eventos_activos)
    return render_template("home.html", user=current_user, active_event=eventos_activos)

@views.route('/my_events', methods=['GET', 'POST'])
@login_required
def my_events():
    user_attendances = Event_Attendance.query.filter_by(user_id=current_user.id).all()
    events = [Event.query.get(attendance.event_id) for attendance in user_attendances]
    now = datetime.now()
    return render_template('my_events.html', user_attendances=user_attendances, events=events, user=current_user,now=now)

@views.route('/about_us', methods=['GET', 'POST'])
def about_us():
    return render_template('about_us.html', user=current_user)

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
    event = Event.query.get_or_404(event_id)
    return render_template('event.html', event=event, user=current_user)

@views.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    return render_template('profile.html', user=current_user)


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
                user_id=current_user.id,
                event_id=event_id,
                total_price=totalAmount
            )
            
            # Agregar la nueva instancia a la sesión y confirmar los cambios en la base de datos
            db.session.add(event_attendance)
            db.session.commit()

            
            return render_template('success.html')
        except Exception as e:
            # Manejar cualquier error que pueda ocurrir al crear la entrada en la base de datos
            print(e)
            return render_template('error.html', message='Failed to create database entry')
    else:
        # No se recibió el ID del intento de pago, manejar el error adecuadamente
        return render_template('error.html', message='Payment intent ID not provided')
    
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
        total_amount = float(data.get('totalAmount'))
        receipt_email = current_user.email
        print(receipt_email)
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
    if event_image and allowed_file(event_image.filename):
        # Asegurar el nombre del archivo
        filename = secure_filename(event_image.filename)
        # Guardar la imagen en la carpeta "static"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        print(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        event_image.save(filepath)
        print(url_for('static',filename=f'images/{filename}'))
        # Obtener la URL relativa de la imagen
        img_url = url_for('static',filename=f'images/{filename}')
    else: 
        img_url=url_for('static',filename=f'images/gremaLogo.png')
        
    #AQUÍ HAY QUE CONTROLAR ALGUNOS ERRORES AL RELLENAR EL FORM
    new_event = Event(name=name, date=date, max_guest_num=max_guest_num, member_price=member_price, member_child_price=member_child_price, guest_price=guest_price, child_price=child_price, img_url=img_url, description=description, admin_id=current_user.id)
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
