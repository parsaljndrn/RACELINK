from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import MarathonEvent, Booking, PaymentProof, MarathonDistance
import os
from werkzeug.utils import secure_filename

runner = Blueprint('runner', __name__, url_prefix='/runner')

#viewing all marathons
@runner.route('/marathons')
def view_marathons():
    marathons = MarathonEvent.query.all()
    return render_template('runner/marathons.html', marathons=marathons)


@runner.route('/marathon/<int:event_id>/distances')
def get_marathon_distances(event_id):
    distances = MarathonDistance.query.filter_by(marathon_id=event_id).all()
    return jsonify([
        {"id": d.id, "distance": d.distance, "price": d.price} 
        for d in distances
    ])

# Create booking
@runner.route('/marathons/book/<int:event_id>', methods=['POST'])
@login_required
def book_marathon(event_id):
    distance_id = request.form.get('distance', type=int)
    tshirt = request.form.get('tshirt')

    if not distance_id or not tshirt:
        return {"error": "Missing fields"}, 400

    distance_obj = MarathonDistance.query.get(distance_id)
    if not distance_obj:
        return {"error": "Invalid distance selected"}, 400

    booking = Booking(
        user_id=current_user.id,
        marathon_id=event_id,
        distance=distance_obj.distance,
        price=distance_obj.price,
        tshirt_size=tshirt,
        payment_status='Pending'
    )
    db.session.add(booking)
    db.session.commit()

    return {"booking_id": booking.id}


# Upload payment proof
@runner.route('/upload_payment/<int:booking_id>', methods=['POST'])
@login_required
def upload_payment(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    payment_image = request.files.get('payment_image')
    amount = request.form.get('amount')

    if not payment_image or not amount:
        flash("Please upload a file and enter amount")
        return redirect(url_for('runner.view_marathons'))

    # Make sure uploads folder exists
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'app', 'static', 'uploads')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Use secure filename
    filename = secure_filename(payment_image.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    payment_image.save(file_path)

    # Create payment proof record
    payment = PaymentProof(
        booking_id=booking.id,
        file_path=f"uploads/{filename}",  # relative path for HTML
        status='Pending',
        amount=float(amount)
    )
    db.session.add(payment)
    db.session.commit()

    flash("Payment uploaded successfully, waiting for approval")
    return redirect(url_for('runner.view_marathons'))

#viewing ng mga na book na marathon
@runner.route('/my_bookings')
@login_required
def my_bookings():
    bookings = Booking.query.filter_by(user_id=current_user.id).all()
    return render_template('runner/my_bookings.html', bookings=bookings)

#cancel booking
@runner.route('/cancel_booking/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    db.session.delete(booking)
    db.session.commit()
    flash('Booking cancelled.', 'warning')
    return redirect(url_for('runner.my_bookings'))