from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import MarathonEvent, Booking, PaymentProof

runner = Blueprint('runner', __name__, url_prefix='/runner')

#viewing all marathons
@runner.route('/marathons')
def view_marathons():
    marathons = MarathonEvent.query.all()
    return render_template('runner/marathons.html', marathons=marathons)

#magbobook ng marathon
@runner.route('/book/<int:event_id>', methods=['GET', 'POST'])
@login_required
def book_marathon(event_id):
    marathon = MarathonEvent.query.get_or_404(event_id)

    if request.method == 'POST':
        booking = Booking(
            user_id=current_user.id,
            marathon_id=event_id,
            status='Pending'
        )
        db.session.add(booking)
        db.session.commit()
        flash('Marathon booked successfully! Please upload payment proof.', 'success')
        return redirect(url_for('runner.upload_payment', booking_id=booking.id))

    return render_template('runner/book.html', marathon=marathon)

#maguupload ng payment
@runner.route('/upload_payment/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def upload_payment(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    if request.method == 'POST':
        file = request.files['payment_proof']
        if file:
            proof = PaymentProof(
                booking_id=booking.id,
                file_path=file.filename
            )
            db.session.add(proof)
            db.session.commit()
            flash('Payment proof uploaded. Awaiting approval.', 'info')
            return redirect(url_for('runner.my_bookings'))

    return render_template('runner/upload_payment.html', booking=booking)

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