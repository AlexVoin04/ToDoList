from flask_wtf import FlaskForm
from wtforms.fields import StringField
#from wtforms.validators import Required
from wtforms.validators import InputRequired

class TaskForm(FlaskForm):
	label = StringField('label', validators = [InputRequired()])
