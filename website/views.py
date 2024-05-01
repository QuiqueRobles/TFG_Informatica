import os
import json
from flask import Blueprint, render_template, request, flash, jsonify, url_for,Flask, current_app, redirect
from flask_login import login_required, current_user
from .models import User,Admin,Event
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
    for event in eventos_activos:
        print(event.name)
    if current_user.is_admin == True:
        print("Renderizando homeAdmin")
        return render_template("homeAdmin.html", user=current_user, active_event=eventos_activos)
    return render_template("home.html", user=current_user, active_event=eventos_activos)



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
    print(payment_intent_id)
    if payment_intent_id:
        # Payment intent ID received, proceed to create entry in the database
        try:
            print("SUUUU2")
            number_member_tickets = int(request.form['number_member_tickets'])
            number_child_member_tickets = int(request.form['number_child_member_tickets'])
            number_guest_tickets = int(request.form['number_guest_tickets'])
            number_child_tickets = int(request.form['number_child_tickets'])
            guests_names = request.form['guests_names']
            print(number_member_tickets)
            print(number_child_member_tickets)
            print(number_child_tickets)
            print(number_guest_tickets)
            print(guests_names)

            
            return render_template('success.html')
        except Exception as e:
            # Manejar cualquier error que pueda ocurrir al crear la entrada en la base de datos
            print("SUUUU3")
            return render_template('error.html', message='Failed to create database entry')
    else:
        print("SUUUU4")
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
        intent = stripe.PaymentIntent.create(
            amount=700,
            currency='eur',
            automatic_payment_methods={
                'enabled': True,
            },
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

def calculate_order_amount(data):
    # Calcula el monto total sumando los productos multiplicados por su cantidad
    member_tickets = data.get('number_member_tickets', 0)
    child_member_tickets = data.get('number_child_member_tickets', 0)
    guest_tickets = data.get('number_guest_tickets', 0)
    child_tickets = data.get('number_child_tickets', 0)
    
    member_price = float(data.get('member_price', 0))
    child_member_price = float(data.get('member_child_price', 0))
    guest_price = float(data.get('guest_price', 0))
    child_price = float(data.get('child_price', 0))

    total_amount = (member_tickets * member_price) + (child_member_tickets * child_member_price) + (guest_tickets * guest_price) + (child_tickets * child_price)
    
    return int(total_amount * 100)  # Convertir a centavos para Stripe
  