from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db
from app.models import MarathonEvent, Booking, PaymentProof, User

admin = Blueprint('admin', __name__)

#para sure na organizer ang nag login
def organizer_required(func):
    from functools import wraps
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'organizer':
            flash('Access denied: Organizers only.', 'danger')
            return redirect(url_for('main.index'))
        return func(*args, **kwargs)
    return decorated_function

#view lahat ng events ni organizer
@admin.route('/admin/marathons')
@login_required
@organizer_required
def manage_marathons():
    marathons = MarathonEvent.query.all()
    return render_template('admin/marathons.html', marathons=marathons)

#add new event
@admin.route('/admin/add_marathon', methods=['GET', 'POST'])
@login_required
@organizer_required
def add_marathon():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        date = request.form['date']
        location = request.form['location']
        registration_fee = request.form['registration_fee']

        #dito ma cecreate
        new_event = MarathonEvent(
            title=title,
            date=date,
            description=description,
            location=location,
            registration_fee=registration_fee,
            organizer_id=current_user.id 
        )
        db.session.add(new_event)
        db.session.commit()
        flash('Marathon added successfully!', 'success')
        return redirect(url_for('admin.manage_marathons'))

    return render_template('admin/add_marathon.html')

#edit an event
@admin.route('/admin/edit_marathon/<int:event_id>', methods=['GET', 'POST'])
@login_required
@organizer_required
def edit_marathon(event_id):
    marathon = MarathonEvent.query.get_or_404(event_id)

    if request.method == 'POST':
        marathon.name = request.form['name']
        marathon.date = request.form['date']
        marathon.location = request.form['location']
        marathon.distance = request.form['distance']
        marathon.registration_fee = request.form['registration_fee']

        db.session.commit()
        flash('Marathon updated!', 'info')
        return redirect(url_for('admin.manage_marathons'))

    return render_template('admin/edit_marathons.html', marathon=marathon)

#delete
@admin.route('/admin/delete_marathon/<int:event_id>', methods=['POST'])
@login_required
@organizer_required
def delete_marathon(event_id):
    marathon = MarathonEvent.query.get_or_404(event_id)
    db.session.delete(marathon)
    db.session.commit()
    flash('Marathon deleted.', 'warning')
    return redirect(url_for('admin.manage_marathons'))

# view payments
@admin.route('/admin/payments')
@login_required
@organizer_required
def manage_payments():
    pending = PaymentProof.query.filter_by(status='Pending').all()
    approved = PaymentProof.query.filter_by(status='Approved').all()
    return render_template('admin/payments.html', pending=pending, approved=approved)
#approve payments
@admin.route('/admin/approve_payment/<int:payment_id>', methods=['POST'])
@login_required
@organizer_required
def approve_payment(payment_id):
    payment = PaymentProof.query.get_or_404(payment_id)
    payment.status = 'Approved'
    db.session.commit()
    flash('Payment approved.', 'success')
    return redirect(url_for('admin.manage_payments'))

#sales report
@admin.route('/admin/reports')
@login_required
@organizer_required
def generate_report():
    from app.models import User, MarathonEvent, Booking, PaymentProof

    #overall
    total_runners = User.query.filter_by(role='runner').count()
    total_marathons = MarathonEvent.query.count()
    total_bookings = Booking.query.count()

    #per-marathon report
    marathons = MarathonEvent.query.all()
    reports = []
    for marathon in marathons:
        total_runners_in_marathon = Booking.query.filter_by(marathon_id=marathon.id).count()
        approved_payments = PaymentProof.query.filter_by(status='Approved').count()
        pending_payments = PaymentProof.query.filter_by(status='Pending').count()

        reports.append({
            'marathon_name': marathon.name,
            'total_runners': total_runners_in_marathon,
            'approved_payments': approved_payments,
            'pending_payments': pending_payments
        })

    return render_template(
        'admin/reports.html',
        total_runners=total_runners,
        total_marathons=total_marathons,
        total_bookings=total_bookings,
        reports=reports
    )
#fallback if di admin
@admin.before_request
def restrict_to_admins():
    if not current_user.is_authenticated or current_user.role != 'organizer':
        abort(403)