from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


# ==========================
# USER MODEL
# ==========================
class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # job_seeker, employer, admin

    # Relationships
    jobs = db.relationship(
        'Job',
        backref='employer',
        cascade="all, delete-orphan",
        lazy=True
    )

    applications = db.relationship(
        'Application',
        backref='applicant',
        cascade="all, delete-orphan",
        lazy=True
    )

    def __repr__(self):
        return f"<User {self.username}>"


# ==========================
# JOB MODEL
# ==========================
class Job(db.Model):
    __tablename__ = "job"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    salary = db.Column(db.String(100))
    location = db.Column(db.String(100))
    category = db.Column(db.String(100))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    employer_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete="CASCADE"),
        nullable=False
    )

    applications = db.relationship(
        'Application',
        backref='job',
        cascade="all, delete-orphan",
        lazy=True
    )

    def __repr__(self):
        return f"<Job {self.title}>"


# ==========================
# APPLICATION MODEL
# ==========================
class Application(db.Model):
    __tablename__ = "application"

    id = db.Column(db.Integer, primary_key=True)

    job_id = db.Column(
        db.Integer,
        db.ForeignKey('job.id', ondelete="CASCADE"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete="CASCADE"),
        nullable=False
    )

    status = db.Column(db.String(50), default="Pending")
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Application User:{self.user_id} Job:{self.job_id}>"
