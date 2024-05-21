import os
import json
import pyqrcode
from flask import Blueprint, render_template, request, flash, jsonify, url_for,Flask, current_app, redirect, send_file, make_response
from flask_login import login_required, current_user
from .models import User,Admin,Event,Event_Attendance,Fee
from . import db
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
    event_details = []

    for event in eventos_activos:
        attendances = Event_Attendance.query.filter_by(event_id=event.id).all()
        
        total_tickets_sold = sum(
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

    if current_user.is_admin == True:
        print("Renderizando homeAdmin")
        return render_template("homeAdmin.html", user=current_user, active_event=eventos_activos, event_details=event_details)
    return render_template("home.html", user=current_user, active_event=eventos_activos, event_details=event_details)

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
    user_fee = Fee.query.filter_by(user_fee=current_user.id).first()
    return render_template('event.html', event=event, user=current_user, user_fee=user_fee)

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
                birthday=datetime.strptime('0001-01-01', '%Y-%m-%d').date()
        

    current_user.first_name = first_name
    current_user.surname = surname
    current_user.nif = nif
    current_user.phone_number = phone_number
    current_user.address = address
    if not current_user.is_admin:
        current_user.birthday = birthday
    if not current_user.is_admin:
        if current_user.partner:
                for partner in current_user.partner:
                    partner.name = request.form['partner_name']
                    partner.nif = request.form['partner_nif']
                    partner.phone_number = request.form['partner_phone_number']
                    birthday = request.form['partner_birthday']
                    try:
                        birthday = datetime.strptime(birthday, '%Y-%m-%d').date()
                    except:
                        birthday=datetime.strptime('0001-01-01', '%Y-%m-%d').date()
                    partner.birthday=birthday

        if current_user.children:
                for child in current_user.children:
                    child.name = request.form['child_name']
                    child.nif = request.form['child_nif']
                    child.phone_number = request.form['child_phone_number']
                    birthday = request.form['child_birthday']
                    try:
                        birthday = datetime.strptime(birthday, '%Y-%m-%d').date()
                    except:
                        birthday=datetime.strptime('0001-01-01', '%Y-%m-%d').date()
                    child.birthday=birthday
    flash("Profile data updated correctly")
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
                total_price=totalAmount,
                cash_payment_in_event=False
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
    
@views.route('/success_cash_template', methods=['GET', 'POST'])
@login_required
def success_cash_template():
    return render_template('success.html')

@views.route('/success_cash', methods=['GET', 'POST'])
@login_required
def success_cash():
        try:
            # Extraer los datos del formulario de la solicitud
            data = request.json
            print("esto va bien")
            # Aquí puedes acceder a los datos del formulario
            number_member_tickets = data['number_member_tickets']
            number_child_member_tickets = data['number_child_member_tickets']
            number_guest_tickets = data['number_guest_tickets']
            number_child_tickets = data['number_child_tickets']
            guests_names = data['guests_names']
            totalAmount = data['totalAmount']
            event_id = data['event_id']

            
            # Crear una nueva instancia de Event_Attendance con los datos del formulario
            event_attendance = Event_Attendance(
                number_member_tickets=number_member_tickets,
                number_memberchild_tickets=number_child_member_tickets,
                number_guest_tickets=number_guest_tickets,
                number_child_tickets=number_child_tickets,
                guests_names=guests_names,
                user_id=current_user.id,
                event_id=event_id,
                total_price=totalAmount,
                cash_payment_in_event=True
            )
            
            # Agregar la nueva instancia a la sesión y confirmar los cambios en la base de datos
            db.session.add(event_attendance)
            db.session.commit()
            return render_template('success.html')
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
    user_attendance = None
    if request.method == 'POST':
        event_id = request.form['event_id']
        searched_event= Event.query.filter_by(id=event_id).first()
        user_email = request.form['user_email']
        searched_user = User.query.filter_by(email=user_email).first()
        if searched_user:
            user_attendance = Event_Attendance.query.filter_by(event_id=event_id, user_id=searched_user.id).first()
            if user_attendance:
                return render_template('manage_event_attendances.html', user=current_user, events=events, users=users, user_attendance=user_attendance, searched_event=searched_event,searched_user=searched_user)  
            else:
                flash('This user does not have tickets', category='error')
                return render_template('manage_event_attendances.html', user=current_user, events=events, users=users, user_attendance=user_attendance)
        else:
            flash('There was an error', category='error')
            return render_template('manage_event_attendances.html', user=current_user, events=events, users=users, user_attendance=user_attendance)
    return render_template('manage_event_attendances.html', user=current_user, events=events, users=users, user_attendance=user_attendance)


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


def generate_qr(event):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(f"Event: {event.name}\nDate: {event.date.strftime('%B %d, %Y')}\nDescription: {event.description}")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    return qr_img

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
    user_name = f"{current_user.first_name} {current_user.surname}"
    user_email = current_user.email
    ticket_info = [
        [Paragraph("Attendee:", style_normal), user_name],
        [Paragraph("Email:", style_normal), user_email],
        [Paragraph("Event Name:", style_normal), event.name],
        [Paragraph("Event Date:", style_normal), event.date.strftime('%B %d, %Y')],
        [Paragraph("Description:", style_normal), event.description],
        [Paragraph("Tickets:", style_normal), {
            "Member": user_attendance.number_member_tickets,
            "Guest": user_attendance.number_guest_tickets,
            "Child": user_attendance.number_child_tickets,
            "Member's Child": user_attendance.number_memberchild_tickets
        }],
        [Paragraph("Total Price:", style_normal), f"${user_attendance.total_price}"],
        [Paragraph("Guest Names:", style_normal), ', '.join(user_attendance.guests_names)],
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
    qr_data = f"Event: {event.name}\nDate: {event.date.strftime('%B %d, %Y')}\nDescription: {event.description}"
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