from wtforms.validators import InputRequired, Email, Length
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField


# Create login or register form
class LoginRegisterForm(FlaskForm):
    email = StringField('Please type your e-mail address', [Email()])
    submit = SubmitField(label='Continue')


# Create register form
class RegisterForm(FlaskForm):
    email = StringField('Please type your e-mail address', [Email()], render_kw={'readonly': True})
    nickname = StringField('Please type your nickname', [InputRequired()])
    password = PasswordField('Password', [InputRequired(), Length(min=8, max=80)])
    password_check = PasswordField('Type your password again', [InputRequired(), Length(min=8, max=80)])
    submit = SubmitField(label='Register')


# create login form
class LoginForm(FlaskForm):
    email = StringField('Please type your e-mail address', [Email()], render_kw={'readonly': True})
    password = PasswordField('Password', [InputRequired(), Length(min=8, max=80)])
    submit = SubmitField(label='Login')


# create forgot password form
class ForgotPasswordForm(FlaskForm):
    email = StringField('Please type your e-mail address', [Email()])
    submit = SubmitField(label='Reset Password')


# create reset form
class ResetPasswordForm(FlaskForm):
    password = PasswordField('New password', [InputRequired(), Length(min=8, max=80)])
    password_check = PasswordField('Type your password again', [InputRequired(), Length(min=8, max=80)])
    submit = SubmitField(label='Reset Password')
