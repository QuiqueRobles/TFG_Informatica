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

@views.route('/create-payment-intent', methods=['POST'])
@login_required
def create_payment():
    try:
        data = json.loads(request.data)
        intent = stripe.PaymentIntent.create(
            #amount=calculate_order_amount(data['items']),
            amount=500,
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

def calculate_order_amount(items):
    # Replace this constant with a calculation of the order's amount
    # Calculate the order total on the server to prevent
    # people from directly manipulating the amount on the client
    return 1000