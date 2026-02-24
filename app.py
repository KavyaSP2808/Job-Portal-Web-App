import os
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, request, flash, abort
from models import db, User, Job, Application
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegisterForm, JobForm, LoginForm

load_dotenv()

app = Flask(__name__)

# ==========================
# CONFIGURATION
# ==========================

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret')
app.config['SESSION_COOKIE_SECURE'] = False  # Change to True in production (HTTPS)
app.config['SESSION_COOKIE_SAMESITE'] = "Lax"

database_url = os.environ.get("DATABASE_URL")

if database_url:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///jobportal.db"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# ==========================
# LOGIN MANAGER
# ==========================

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.session_protection = "strong"

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

with app.app_context():
    db.create_all()

# ==========================
# ROUTES
# ==========================

@app.route('/')
def home():
    page = request.args.get('page', 1, type=int)
    jobs = Job.query.order_by(Job.created_at.desc()).paginate(page=page, per_page=5)
    return render_template("index.html", jobs=jobs)


# --------------------------
# REGISTER
# --------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():

        existing_user = User.query.filter(
            (User.email == form.email.data) |
            (User.username == form.username.data)
        ).first()

        if existing_user:
            flash("User already exists with this email or username.")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256'
        )

        user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
            role=form.role.data
        )

        db.session.add(user)
        db.session.commit()

        flash("Registration successful! Please login.")
        return redirect(url_for('login'))

    return render_template("register.html", form=form)


# --------------------------
# LOGIN
# --------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and check_password_hash(user.password, form.password.data):
            login_user(user)

            
            return redirect(url_for('dashboard'))

        flash("Invalid credentials")

    return render_template("login.html", form=form)


# --------------------------
# LOGOUT
# --------------------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


# --------------------------
# DASHBOARD
# --------------------------
@app.route('/dashboard')
@login_required
def dashboard():

    if current_user.role == "employer":
        jobs = current_user.jobs

        return render_template(
            "dashboard.html",
            role="employer",
            jobs=jobs
        )

    elif current_user.role == "job_seeker":
        applications = current_user.applications

        return render_template(
            "dashboard.html",
            role="job_seeker",
            applications=applications
        )

    flash("Invalid role.")
    return redirect(url_for("home"))


# --------------------------
# POST JOB
# --------------------------
@app.route('/post-job', methods=['GET', 'POST'])
@login_required
def post_job():

    if current_user.role != "employer":
        abort(403)

    form = JobForm()

    if form.validate_on_submit():
        new_job = Job(
            title=form.title.data,
            description=form.description.data,
            salary=form.salary.data,
            location=form.location.data,
            category=form.category.data,
            employer_id=current_user.id
        )

        db.session.add(new_job)
        db.session.commit()

        flash("Job posted successfully!")
        return redirect(url_for('dashboard'))

    return render_template("post_job.html", form=form)


# --------------------------
# EDIT JOB
# --------------------------
@app.route('/edit-job/<int:job_id>', methods=['GET', 'POST'])
@login_required
def edit_job(job_id):

    job = Job.query.get_or_404(job_id)

    # Only job owner can edit
    if job.employer_id != current_user.id:
        abort(403)

    form = JobForm(obj=job)

    if form.validate_on_submit():
        job.title = form.title.data
        job.description = form.description.data
        job.salary = form.salary.data
        job.location = form.location.data
        job.category = form.category.data

        db.session.commit()

        flash("Job updated successfully!")
        return redirect(url_for('dashboard'))

    return render_template("post_job.html", form=form)

# --------------------------
# DELETE JOB
# --------------------------
@app.route('/delete-job/<int:job_id>', methods=['POST'])
@login_required
def delete_job(job_id):

    job = Job.query.get_or_404(job_id)

    if job.employer_id != current_user.id:
        abort(403)

    db.session.delete(job)
    db.session.commit()

    flash("Job deleted successfully!")
    return redirect(url_for('dashboard'))

# --------------------------
# UPDATE APPLICATION
# --------------------------
@app.route('/update-application/<int:app_id>', methods=['POST'])
@login_required
def update_application(app_id):

    application = Application.query.get_or_404(app_id)

    if application.job.employer_id != current_user.id:
        abort(403)

    status = request.form.get("status")

    if status not in ["Selected", "Rejected"]:
        flash("Invalid status.")
        return redirect(url_for('dashboard'))

    application.status = status
    db.session.commit()

    flash(f"Application {status} successfully!")
    return redirect(url_for('view_applications', job_id=application.job_id))


# --------------------------
# APPLY JOB (POST ONLY)
# --------------------------
@app.route('/apply/<int:job_id>', methods=['POST'])
@login_required
def apply(job_id):

    if current_user.role != "job_seeker":
        abort(403)

    existing_application = Application.query.filter_by(
        job_id=job_id,
        user_id=current_user.id
    ).first()

    if existing_application:
        flash("You have already applied for this job.")
        return redirect(url_for('home'))

    new_application = Application(
        job_id=job_id,
        user_id=current_user.id
    )

    db.session.add(new_application)
    db.session.commit()

    flash("Application submitted successfully!")
    return redirect(url_for('dashboard'))

# --------------------------
# VIEW APPLICATIONS
# --------------------------
@app.route('/view-applications/<int:job_id>')
@login_required
def view_applications(job_id):

    job = Job.query.get_or_404(job_id)

    if job.employer_id != current_user.id:
        abort(403)
        
    applications = job.applications    

    return render_template("view_applications.html", job=job, applications=applications)


if __name__ == "__main__":
    app.run(debug=True)
