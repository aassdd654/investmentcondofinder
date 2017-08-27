
# coding: utf-8
from datetime import datetime
from flask import Flask, render_template, session, redirect, url_for
from FlaskWebProject import app

# ...............................................#
# form #
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Required

# ...............................................#

class NameForm(FlaskForm):
    name = StringField('Choose The Zipcode:', validators=[Required()])
    submit = SubmitField('Submit')


# ...............................................#

@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm() #this line passes the class NameForm(FlaskForm)'s attributes to new form
    if form.validate_on_submit():
        session['name'] = form.name.data
        return redirect(url_for('index'))
    return render_template('investmentcondofinder.html',form=form,
    name=session.get('name'),title='Investment Condo Finder',
    current_time=datetime.utcnow())


# ...............................................#

@app.route('/contact')
def home():
    """Renders feedback page."""
    return render_template(
        'contact.html',
        title='contact',
        year=datetime.now().year,
    )

@app.route('/about')
def awesome():
    """Renders About Us Introduction of the project and me"""
    return render_template(
        'about.html',
        title='about us',
    )

# ...............................................#
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
