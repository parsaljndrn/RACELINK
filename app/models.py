from datetime import datetime
from flask_login import UserMixin
from app import db, login_manager
from sqlalchemy import UniqueConstraint

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# User Table
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='runner')
    date_registered = db.Column(db.DateTime, default=datetime.utcnow)

    marathons = db.relationship('MarathonEvent', backref='organizer', lazy=True)
    bookings = db.relationship('Booking', backref='runner', lazy=True)
    runner_profile = db.relationship('RunnerProfile', backref='user', uselist=False)

# Runner Details
class RunnerProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    address = db.Column(db.String(500))
    phone = db.Column(db.String(15))
    gender = db.Column(db.String(1))
    birthdate = db.Column (db.Date)
    emergency_contact_name = db.Column (db.String(100))
    emergency_contact_number = db.Column (db.String(15))

# Marathon Events
class MarathonEvent(db.Model):
    id = db.Column (db.Integer, primary_key=True)
    title = db.Column (db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # number of participants

    bookings = db.relationship('Booking', backref='marathon', lazy=True)
    distances = db.relationship('MarathonDistance', backref='marathon',  cascade='all, delete-orphan')
    tshirt_sizes = db.relationship('MarathonTshirtSize', backref='marathon', lazy=True)

# Available distances for each marathon
class MarathonDistance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    marathon_id = db.Column(db.Integer, db.ForeignKey('marathon_event.id'), nullable=False)
    distance = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('marathon_id', 'distance', name='unique_distance_per_marathon'),
    )

# Available shirt sizes for each marathon
class MarathonTshirtSize(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    marathon_id = db.Column(db.Integer, db.ForeignKey('marathon_event.id'), nullable=False)
    size = db.Column(db.String(10), nullable=False)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    marathon_id = db.Column(db.Integer, db.ForeignKey('marathon_event.id'), nullable=False)
    distance = db.Column(db.String(50))
    price = db.Column(db.Float) 
    tshirt_size = db.Column(db.String(10))
    payment_status = db.Column(db.String(20), default='pending')
    bib_number = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='pending') 

    payment_proof = db.relationship(
        'PaymentProof',
        backref='booking',  # This creates `payment.booking` automatically
        uselist=False
    )

    # Enforce unique bib per marathon
    __table_args__ = (
        UniqueConstraint('marathon_id', 'bib_number', name='unique_bib_per_marathon'),
    )

# Payments
class PaymentProof(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    file_path = db.Column(db.String(200), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Pending')
    amount = db.Column(db.Float, nullable=False) 