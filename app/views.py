from app import app, db
from flask import render_template, request, redirect, url_for, flash, Response
from .models import User
from .forms import UserForm
import time
import psutil
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from functools import wraps


# Prometheus metrics
app_info = Info('flask_app_info', 'Application information')
app_info.info({'version': '1.0.0', 'name': 'flask-db-demo'})

request_count = Counter(
    'flask_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'flask_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

cpu_usage = Gauge('system_cpu_usage_percent', 'CPU usage percentage')
memory_usage = Gauge('system_memory_usage_percent', 'Memory usage percentage')
disk_usage = Gauge('system_disk_usage_percent', 'Disk usage percentage')
user_count = Gauge('users_total', 'Total number of users in database')
app_health = Gauge('flask_app_health', 'Application health status (1=healthy, 0=unhealthy)')

def track_requests(f):
    """Decorator to track request metrics"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        try:
            response = f(*args, **kwargs)
            status_code = getattr(response, 'status_code', 200)
        except Exception as e:
            status_code = 500
            raise
        finally:
            request_count.labels(
                method=request.method,
                endpoint=f.__name__,
                status=status_code
            ).inc()
            
            request_duration.labels(
                method=request.method,
                endpoint=f.__name__
            ).observe(time.time() - start_time)
        
        return response
    return decorated_function

def update_metrics():
    """Update system and database metrics"""
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_usage.set(cpu_percent)
        
        memory = psutil.virtual_memory()
        memory_usage.set(memory.percent)
        
        disk = psutil.disk_usage('/')
        disk_usage.set((disk.used / disk.total) * 100)
        
        # Database metrics
        total_users = User.query.count()
        user_count.set(total_users)
        
        # Health check
        if cpu_percent < 80 and memory.percent < 85:
            app_health.set(1)  # Healthy
        else:
            app_health.set(0)  # Unhealthy
            
    except Exception as e:
        print(f"Error updating metrics: {e}")
        app_health.set(0)


@app.route('/health')
@track_requests
def health_check():
    """Basic health check endpoint"""
    try:
        db.session.execute('SELECT 1')
        status = "healthy"
        status_code = 200
    except Exception as e:
        status = "unhealthy"
        status_code = 503
    
    return {"status": status, "timestamp": time.time()}, status_code


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

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    update_metrics()
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


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
