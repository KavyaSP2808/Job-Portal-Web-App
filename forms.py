from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length


# ================================
# User Registration Form
# ================================

class RegisterForm(FlaskForm):
    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=3, max=100)]
    )

    email = StringField(
        'Email',
        validators=[DataRequired(), Email()]
    )

    password = PasswordField(
        'Password',
        validators=[DataRequired(), Length(min=6)]
    )

    role = SelectField(
        'Role',
        choices=[
            ('job_seeker', 'Job Seeker'),
            ('employer', 'Employer')
        ],
        validators=[DataRequired()]
    )

    submit = SubmitField('Register')


# ================================
# Login Form
# ================================

class LoginForm(FlaskForm):
    email = StringField(
        'Email',
        validators=[DataRequired(), Email()]
    )

    password = PasswordField(
        'Password',
        validators=[DataRequired()]
    )

    submit = SubmitField('Login')


# ================================
# Job Posting Form (Employer)
# ================================

class JobForm(FlaskForm):
    title = StringField(
        'Job Title',
        validators=[DataRequired(), Length(max=200)]
    )

    description = TextAreaField(
        'Job Description',
        validators=[DataRequired()]
    )

    salary = StringField(
        'Salary',
        validators=[DataRequired()]
    )

    location = StringField(
        'Location',
        validators=[DataRequired()]
    )

    category = StringField(
        'Category',
        validators=[DataRequired()]
    )

    submit = SubmitField('Post Job')
