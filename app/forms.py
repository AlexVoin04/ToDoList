from flask_wtf import FlaskForm
from wtforms.fields import StringField
# from wtforms.validators import Required
from wtforms.validators import InputRequired, Length, Regexp


class TaskForm(FlaskForm):
    label = StringField('label', validators=[InputRequired(), Length(min=4), Regexp('^[\w,а-яА-Я\s]+$', message='Only English and Russian letters, digits, and commas are allowed')])
