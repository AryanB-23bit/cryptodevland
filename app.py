from flask import Flask, render_template, url_for, redirect, flash
from flask_wtf import FlaskForm
from sqlalchemy import PickleType
from wtforms import StringField, IntegerField, SubmitField, DecimalField
from wtforms.validators import InputRequired, NumberRange
from flask_sqlalchemy import SQLAlchemy
import pickle

# making an instance of a Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///landgrab.db'
db = SQLAlchemy(app)


# making the only route of the app

@app.route('/', methods=['GET', 'POST'])
def home_page():
    form = LandgrabForm()
    if form.validate_on_submit():
        userLand = Land(form.top_left_x.data, form.top_left_y.data, form.height.data,
                        form.width.data)
        landDisputeFlag = isValidGrab(userLand)
        if landDisputeFlag is None:
            pickled_LandObj = pickle.dumps(userLand)
            landgrab = Landgrab(applicant_name=form.applicant_name.data,
                                applicant_land=pickled_LandObj)
            db.session.add(landgrab)
            db.session.commit()
            flashStr = f'Congratulations {form.applicant_name.data}! Your land grab has been approved!'
            flash(flashStr, 'success')
        else:
            flashStr = f'Our deepest condolences {form.applicant_name.data}. ' \
                       f'Your land grab has been rejected due to an overlap with a land at {landDisputeFlag}'
            flash(flashStr, 'error')

        return redirect(url_for('home_page'))

    return render_template('cdl.html', form=form)


# Land object
class Land:
    def __init__(self, topLeftX, topLeftY, height, width):
        self.height = height
        self.width = width
        self.topLeftX = topLeftX
        self.topLeftY = topLeftY
        self.bottomRightX = topLeftX + width
        self.bottomRightY = topLeftY - height

    def __repr__(self):
        return f'[{self.topLeftX},{self.topLeftY}] of width {self.width} and height {self.height}'


# logic for a valid land grab
# a function to test if two non-angled rectangle overlap on a 2d plane, outputs a bool
# an overlap is interpreted in this context as any part of a land PASSING over other
# two rectangle sharing a border is not considered overlap in this context. The function works with floats
def isValidGrab(newUserLand):
    landRecords = db.session.query(Landgrab).all()
    for land in landRecords:
        landObj = pickle.loads(land.applicant_land)
        if newUserLand.topLeftX == landObj.topLeftX and \
                newUserLand.topLeftY == landObj.topLeftY:
            return landObj
        elif not ((newUserLand.topLeftX >= landObj.bottomRightX) or
                  (landObj.topLeftX >= newUserLand.bottomRightX) or
                  (newUserLand.bottomRightY >= landObj.topLeftY) or
                  (landObj.bottomRightY >= newUserLand.topLeftY)):
            return landObj
    return None


# making the form class
class LandgrabForm(FlaskForm):
    applicant_name = StringField(label='Applicant Name', validators=[InputRequired()])
    top_left_x = IntegerField(label='Top-Left X-Coordinate',
                              validators=[InputRequired(), NumberRange(min=-2147483647, max=2147483647)])
    top_left_y = IntegerField(label='Top-Left Y-Coordinate',
                              validators=[InputRequired(), NumberRange(min=-2147483647, max=2147483647)])
    height = DecimalField(label='Height', validators=[InputRequired(), NumberRange(min=1, max=2147483647)])
    width = DecimalField(label='Width', validators=[InputRequired(), NumberRange(min=1, max=2147483647)])
    submit = SubmitField(label='SUBMIT')


# making the object relational model for the database
class Landgrab(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    applicant_name = db.Column(db.String(length=60), nullable=False)
    applicant_land = db.Column(PickleType(), nullable=False)

    def __repr__(self):
        return f'{self.rectangle}'


if __name__ == '__main__':
    app.run()
