from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func




class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, server_default="5")
    nif =db.Column(db.Integer, nullable=False)
    is_admin= False
    phone_number=db.Column(db.Integer)
    address=db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150), nullable=False)
    birthday = db.Column(db.Date) 
    creation_date = db.Column(db.Date, default=func.current_date()) 
    first_name = db.Column(db.String(150))
    

class Admin(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    is_admin = True
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    phone_number=db.Column(db.Integer)
    first_name = db.Column(db.String(150))
    creation_date = db.Column(db.Date, default=func.current_date()) 
    address=db.Column(db.String(150))
    events = db.relationship('Event')


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name= db.Column(db.String(80))
    date = db.Column(db.DateTime(timezone=True), default=func.current_date())
    max_guest_num = db.Column(db.Integer)
    member_price=db.Column(db.Float)
    member_child_price=db.Column(db.Float)
    guest_price=db.Column(db.Float)
    img_url=db.Column(db.String(300))
    description=db.Column(db.String(800))
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'))
    

class Event_Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date = db.Column(db.DateTime(timezone=True), default=func.current_date())
    number_guest_tickets = db.Column(db.Integer)
    number_child_tickets = db.Column(db.Integer)
    number_member_tickets = db.Column(db.Integer)
    number_memberchild_tickets = db.Column(db.Integer)
    member_price=db.Column(db.Float)
    guests_names = db.Column(db.String(300))
    total_price= db.Column(db.Float)


class Fee(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    payed= db.Column(db.Boolean)
    year= db.Column(db.String(4))

class Child(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    nif =db.Column(db.Integer)
    birthday = db.Column(db.Date) 
    creation_date = db.Column(db.Date, default=func.current_date()) 
    name = db.Column(db.String(150))
    phone_number=db.Column(db.Integer)

class Partner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    nif =db.Column(db.Integer)
    birthday = db.Column(db.Date) 
    creation_date = db.Column(db.Date, default=func.current_date()) 
    name = db.Column(db.String(150))
    phone_number=db.Column(db.Integer)