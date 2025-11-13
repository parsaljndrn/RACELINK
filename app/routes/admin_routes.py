from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db
from app.models import MarathonEvent, Booking, PaymentProof, User, MarathonDistance
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
    title = request.form['title']
    description = request.form['description']
    date = request.form['date']
    location = request.form['location']

    # Create marathon event
    new_event = MarathonEvent(
        title=title,
        description=description,
        date=date,
        location=location,
        organizer_id=current_user.id
    )
    db.session.add(new_event)
    db.session.flush()  # to get new_event.id before commit

    # Get all distances
    distance_names = request.form.getlist('distance_name[]')
    distance_prices = request.form.getlist('price[]')

    # Debug: check what Flask received
    print("Distances:", distance_names)
    print("Prices:", distance_prices)

    # Add distances
    for name, price in zip(distance_names, distance_prices):
        distance = MarathonDistance(
            marathon_id=new_event.id,
            distance=name,
            price=float(price)
        )
        db.session.add(distance)

    db.session.commit()
    flash('Marathon added successfully!', 'success')
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

    # These come as lists
    distances = request.form.getlist('distances[]')
    prices = request.form.getlist('prices[]')

    # You’ll likely need to update related distance entries, not MarathonEvent directly.
    # Example: if you have a MarathonDistance model
    MarathonDistance.query.filter_by(marathon_id=event_id).delete()
    for d, p in zip(distances, prices):
        new_distance = MarathonDistance(distance=d, price=p, marathon_id=event_id)
        db.session.add(new_distance)

    db.session.commit()
    flash('Marathon updated!', 'info')
    return redirect(url_for('admin.manage_events'))

#delete
@admin.route('/admin/ManageEvents/delete_marathon/<int:event_id>', methods=['POST'])
@login_required
@organizer_required
def delete_marathon(event_id):
    try:
        marathon = MarathonEvent.query.get_or_404(event_id)
        db.session.delete(marathon)
        db.session.commit()
        return jsonify({'success': True, 'title': marathon.title})
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'error': str(e)})

# view payments
@admin.route('/admin/event/<int:event_id>/payments')
@login_required
@organizer_required
def view_event_payments(event_id):
    print("Fetching payments for event:", event_id)
    pending = PaymentProof.query.join(Booking).filter(
        Booking.marathon_id == event_id,
        PaymentProof.status == 'Pending'
    ).all()

    approved = PaymentProof.query.join(Booking).filter(
        Booking.marathon_id == event_id,
        PaymentProof.status == 'Approved'
    ).all()

    def serialize(payment, include_bib=False):
        marathon_id = payment.booking.marathon_id
        distance_name = payment.booking.distance  # assuming this is a string like "10K"
    
        distance_obj = MarathonDistance.query.filter_by(
            marathon_id=marathon_id,
            distance=distance_name
        ).first()

        price = distance_obj.price if distance_obj else 0  # fallback

        data = {
            'id': payment.id,
            'runner': payment.booking.runner.name,
            'marathon': payment.booking.marathon.title,
            'amount': payment.booking.price,
            'status': payment.status,
            'file_path': url_for('static', filename=payment.file_path.replace('static/', ''))
        }
        if include_bib:
            data['bib_number'] = payment.booking.bib_number or '-'
        return data

    pending_data = [serialize(p) for p in pending]
    approved_data = [serialize(p, include_bib=True) for p in approved]

    return jsonify({'pending': pending_data, 'approved': approved_data})

#approve payments
@admin.route('/admin/approve_payment/<int:payment_id>', methods=['POST'])
@login_required
@organizer_required
def approve_payment(payment_id):
    payment = PaymentProof.query.get_or_404(payment_id)
    booking = payment.booking
    marathon_id = booking.marathon_id

    # 🔹 Find the highest existing bib number in this marathon
    last_booking = (
        Booking.query
        .filter(Booking.marathon_id == marathon_id, Booking.bib_number != None)
        .order_by(Booking.bib_number.desc())
        .first()
    )

    # 🔹 Determine the next bib number
    next_bib = int(last_booking.bib_number) + 1 if last_booking and last_booking.bib_number else 1
    booking.bib_number = str(next_bib)

    # 🔹 Update statuses
    booking.payment_status = 'Approved'
    payment.status = 'Approved'

    # 🔹 Commit to database
    db.session.commit()

    flash(f"Payment approved! Bib #{booking.bib_number} assigned to {booking.runner.name}.", "success")

    # 🔹 Return JSON so your modal can refresh automatically
    return jsonify({
        'success': True,
        'bib_number': booking.bib_number,
        'runner': booking.runner.name,
        'marathon': booking.marathon.title
    })

#distance
@admin.route('/admin/marathon/<int:event_id>/distances')
@login_required
@organizer_required
def get_marathon_distances(event_id):
    from app.models import MarathonDistance

    distances = MarathonDistance.query.filter_by(marathon_id=event_id).all()

    return jsonify([
        {
            'id': d.id,
            'distance': d.distance,
            'price': d.price
        }
        for d in distances
    ])

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