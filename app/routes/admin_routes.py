from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db
from app.models import MarathonEvent, Booking, PaymentProof, User
from flask import jsonify

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

#orgqnizer dashboard
@admin.route('/admin/admin_dashboard')
@login_required
@organizer_required
def admin_dashboard():
    marathons = MarathonEvent.query.all()
    return render_template('admin/dashboard.html', marathons=marathons)

#Manage Events Page (base sa wireframe)
@admin.route('/admin/ManageEvents', methods=['GET', 'POST'])
@login_required
@organizer_required
def manage_events():
    marathons = MarathonEvent.query.all()
    return render_template('admin/manage_events.html', marathons=marathons)

#View Event details
@admin.route('/admin/EventDetails', methods=['GET', 'POST'])
@login_required
@organizer_required
def event_details():
    marathons = MarathonEvent.query.all()
    return render_template('admin/manage_events.html', marathons=marathons)

#add new event
@admin.route('/admin/ManageEvents/addEvent', methods=['GET', 'POST'])
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
        return redirect(url_for('admin.manage_events'))

    return redirect(url_for('admin.manage_events'))

#edit an event
@admin.route('/admin/ManageEvents/edit_marathon/<int:event_id>', methods=['POST'])
@login_required
@organizer_required
def edit_marathon(event_id):
    marathon = MarathonEvent.query.get_or_404(event_id)
    marathon.name = request.form['name']
    marathon.date = request.form['date']
    marathon.location = request.form['location']
    marathon.distance = request.form['distance']
    marathon.registration_fee = request.form['registration_fee']

    db.session.commit()
    flash('Marathon updated!', 'info')
    return redirect(url_for('admin.manage_events'))

#delete
@admin.route('/admin/ManageEvents/delete_marathon/<int:event_id>', methods=['POST'])
@login_required
@organizer_required
def delete_marathon(event_id):
    marathon = MarathonEvent.query.get_or_404(event_id)
    db.session.delete(marathon)
    db.session.commit()
    flash('Marathon deleted.', 'warning')
    return redirect(url_for('admin.manage_events'))

# view payments
@admin.route('/admin/event/<int:event_id>/payments')
@login_required
@organizer_required
def view_event_payments(event_id):
    pending = PaymentProof.query.join(Booking).filter(
        Booking.marathon_id == event_id,
        PaymentProof.status == 'Pending'
    ).all()

    approved = PaymentProof.query.join(Booking).filter(
        Booking.marathon_id == event_id,
        PaymentProof.status == 'Approved'
    ).all()

    def serialize(payment):
        return {
            'id': payment.id,
            'runner': payment.booking.runner.name,        # use name instead of user_id
            'marathon': payment.booking.marathon.title,  # use title instead of id
            'amount': payment.booking.marathon.registration_fee,
            'status': payment.status,
            'file_path': url_for('static', filename=payment.file_path)  # <-- fixed
        }

    pending_data = [serialize(p) for p in pending]
    approved_data = [serialize(p) for p in approved]

    return jsonify({'pending': pending_data, 'approved': approved_data})

#approve payments
@admin.route('/admin/approve_payment/<int:payment_id>', methods=['POST'])
@login_required
@organizer_required
def approve_payment(payment_id):
    payment = PaymentProof.query.get_or_404(payment_id)
    payment.status = 'Approved'
    db.session.commit()
    flash('Payment approved.', 'success')
    return jsonify({'success': True}) 

#Profile Information

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