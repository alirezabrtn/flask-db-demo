from app import app, db
from flask import render_template, request, redirect, url_for, flash
from .models import User
from .forms import UserForm
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST
import psutil

# Define basic system health metrics
cpu_usage = Gauge('system_cpu_usage_percent', 'Current CPU usage percentage')
memory_usage = Gauge('system_memory_usage_percent', 'Current memory usage percentage')
disk_usage = Gauge('system_disk_usage_percent', 'Current disk usage percentage')

def update_system_metrics():
    """Update system metrics with current values"""
    # CPU usage
    cpu_usage.set(psutil.cpu_percent(interval=1))
    
    # Memory usage
    memory = psutil.virtual_memory()
    memory_usage.set(memory.percent)
    
    # Disk usage (root filesystem)
    disk = psutil.disk_usage('/')
    disk_percent = (disk.used / disk.total) * 100
    disk_usage.set(disk_percent)

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    update_system_metrics()
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

###
# Routing for your application.
###

@app.route('/')
def home():
    """Render website's home page."""
    return render_template('home.html')


@app.route('/about/')
def about():
    """Render the website's about page."""
    return render_template('about.html', name="Mary Jane")

@app.route('/users')
def users():
    users = User.query.all()

    return render_template('users.html', users=users)

@app.route('/users/new', methods=['post', 'get'])
def new_user():
    new_user_form = UserForm()
    if new_user_form.validate_on_submit():
        username = new_user_form.username.data
        email = new_user_form.email.data
        password = new_user_form.password.data

        user = User(username, email, password)
        db.session.add(user)
        db.session.commit()

        flash('User successfully added!', 'success')
        redirect(url_for('users'))

    flash_errors(new_user_form)
    return render_template('add_user.html', form=new_user_form)


###
# The functions below should be applicable to all Flask apps.
###

# Flash errors from the form if validation fails
def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
            ), 'danger')

@app.route('/<file_name>.txt')
def send_text_file(file_name):
    """Send your static text file."""
    file_dot_text = file_name + '.txt'
    return app.send_static_file(file_dot_text)


@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also tell the browser not to cache the rendered page. If we wanted
    to we could change max-age to 600 seconds which would be 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response


@app.errorhandler(404)
def page_not_found(error):
    """Custom 404 page."""
    return render_template('404.html'), 404
