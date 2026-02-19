from flask import Flask, render_template, redirect, url_for, request, flash
from models import db, User, Job, Application
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegisterForm, JobForm, LoginForm
import os

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret')

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    "DATABASE_URL",
    "sqlite:///jobportal.db"
)


db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Create DB
with app.app_context():
    db.create_all()


# Home
@app.route('/')
def home():
    jobs = Job.query.all()
    return render_template("index.html", jobs=jobs)


# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)

        user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
            role=form.role.data
        )

        db.session.add(user)
        db.session.commit()

        flash("Registration successful!")
        return redirect(url_for('login'))

    return render_template("register.html", form=form)



# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash("Invalid credentials")

    return render_template("login.html",form=form)


# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


# Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == "employer":
        jobs = Job.query.filter_by(employer_id=current_user.id).all()
        return render_template("dashboard.html", jobs=jobs)

    elif current_user.role == "job_seeker":
        applications = Application.query.filter_by(user_id=current_user.id).all()
        return render_template("dashboard.html", applications=applications)

    return render_template("dashboard.html")



# Post Job (Employer only)
@app.route('/post-job', methods=['GET', 'POST'])
@login_required
def post_job():
    if current_user.role != "employer":
        flash("Access denied")
        return redirect(url_for('dashboard'))

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


# Apply Job (Job Seeker only)
@app.route('/apply/<int:job_id>')
@login_required
def apply(job_id):

    # Only job seekers can apply
    if current_user.role != "job_seeker":
        flash("Only job seekers can apply for jobs.")
        return redirect(url_for('home'))

    # Check if already applied
    existing_application = Application.query.filter_by(
        job_id=job_id,
        user_id=current_user.id
    ).first()

    if existing_application:
        flash("You have already applied for this job.")
        return redirect(url_for('home'))

    # Create new application
    new_application = Application(
        job_id=job_id,
        user_id=current_user.id
    )

    db.session.add(new_application)
    db.session.commit()

    flash("Application submitted successfully!")
    return redirect(url_for('dashboard'))

@app.route('/edit-job/<int:job_id>', methods=['GET', 'POST'])
@login_required
def edit_job(job_id):

    job = Job.query.get_or_404(job_id)

    # Security: Only owner can edit
    if job.employer_id != current_user.id:
        flash("Unauthorized access.")
        return redirect(url_for('dashboard'))

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

    return render_template('post_job.html', form=form)


@app.route('/delete-job/<int:job_id>', methods=['POST'])
@login_required
def delete_job(job_id):

    job = Job.query.get_or_404(job_id)

    # Security: Only owner can delete
    if job.employer_id != current_user.id:
        flash("Unauthorized action.")
        return redirect(url_for('dashboard'))

    db.session.delete(job)
    db.session.commit()

    flash("Job deleted successfully!")
    return redirect(url_for('dashboard'))

@app.route('/update-application/<int:app_id>/<string:status>')
@login_required
def update_application(app_id, status):

    application = Application.query.get_or_404(app_id)

    # Only employer who owns the job can update
    if application.job.employer_id != current_user.id:
        flash("Unauthorized action.")
        return redirect(url_for('dashboard'))

    if status not in ["Selected", "Rejected"]:
        flash("Invalid status.")
        return redirect(url_for('dashboard'))

    application.status = status
    db.session.commit()

    flash(f"Application {status} successfully!")
    return redirect(url_for('view_applications', job_id=application.job_id))

@app.route('/view-applications/<int:job_id>')
@login_required
def view_applications(job_id):

    job = Job.query.get_or_404(job_id)

    if job.employer_id != current_user.id:
        flash("Unauthorized access.")
        return redirect(url_for('dashboard'))

    applications = job.applications

    return render_template("view_applications.html", job=job, applications=applications)


if __name__ == "__main__":
    app.run(debug=True)
