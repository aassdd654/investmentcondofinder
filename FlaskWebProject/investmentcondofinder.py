
# coding: utf-8
from datetime import datetime
from flask import Flask, render_template, session, redirect, url_for, request, flash
from FlaskWebProject import app
from FlaskWebProject import Investment_Condo_Finder_Submit_V3
# ...............................................#
# form #
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DecimalField, FloatField, IntegerField, SelectField
from wtforms.validators import Required, NumberRange


# ...............................................#

class InputForm(FlaskForm):
    #zipcode = StringField('Choose The Zipcode:', validators=[Required()])
    zipcode = SelectField('Choose The Zipcode:', validators=[Required()],
    choices=[
    ('San Francisco, CA 94158', 'San Francisco, CA 94158'),
    ('San Francisco, CA 94103', 'San Francisco, CA 94103'),
    ('San Francisco, CA 94105', 'San Francisco, CA 94105'),
    ('San Francisco, CA 94107', 'San Francisco, CA 94107'),
    ])
    downpayment = FloatField('downpayment:',validators=[Required(),
    NumberRange(min=100000, max=500000, message='between 100,000 and 500,000')])
    principal = FloatField("Mortgage Loan $USD: ", validators=[Required(),
    NumberRange(min=100000, max=2000000, message='between 100,000 and 2,000,000')])
    interest_rate = DecimalField("Interest Rate %: ", validators=[Required(),
    NumberRange(min=1, max=10, message="between 1 and 10")])
    amortization_period = IntegerField("Mortgage Years: ", validators=[Required(),
    NumberRange(min=1, max=10, message="between 1 and 30")])
    #deal = Deal(downpayment, principal, interest_rate, amortization_period)
    submit = SubmitField('Submit')

# ...............................................#

@app.route('/', methods=['GET', 'POST'])
def index():
    form = InputForm() #this line passes the class InputForm(FlaskForm)'s attributes to new form
    if form.validate_on_submit():
        session['zipcode'] = form.zipcode.data
        session['downpayment'] = form.downpayment.data
        session['principal'] = form.principal.data
        session['interest_rate'] = form.interest_rate.data
        session['amortization_period'] = form.amortization_period.data
        return redirect(url_for('index'))
    return render_template(
    'investmentcondofinder.html',
    form=form,
    title='Investment Condo Finder',
    zipcode=session.get('zipcode'),
    downpayment=session.get('downpayment'),
    principal=session.get('principal'),
    interest_rate=session.get('interest_rate'),
    amortization_period=session.get('amortization_period'),
    current_time=datetime.utcnow(),
    name='PPP')

@app.route('/result', methods=['GET', 'POST'])
def result():
    """Renders input result page."""

    form = InputForm
    """
    listings[zpid] = [0.home_detail_link,
                      1.property_tax,
                      2.rental_estimate,
                      3.price_estimate,
                      4.hoa,
                      5.address,
                      6.interest of the first year loan,
                      7.principal of the first year loan
                      8.judgement : ["Good Deal (•◡•)", "Perfect Deal [̲̅$̲̅(̲̅5̲̅)̲̅$̲̅]", 'Pass', 'Incomplete']
                      9.gross_income (rental_estimate - all expenses(interest, property_tax, hoa))
                      10.net_income profit (rental_estimate - all expenses(interest, property_tax, hoa) - principal)
                      11.coverage percentage of principal/rental]
    """

    if request.method == 'POST':
        #x = "San Francisco, CA 94158"
        zipcode = request.form[('zipcode')]
        downpayment =  request.form[('downpayment')]
        principal = request.form[('principal')]
        interest_rate = request.form[('interest_rate')]
        amortization_period = request.form[('amortization_period')]
        affordable_amount = Investment_Condo_Finder_Submit_V3.display_investment_budget(downpayment, principal, interest_rate, amortization_period)
        result = Investment_Condo_Finder_Submit_V3.find_valuable_listing(zipcode, downpayment, principal, interest_rate, amortization_period)

        return render_template('result.html',title="condo listings",
        year=datetime.now().year,
        affordable_amount=affordable_amount,
        result=result)

# ...............................................#

@app.route('/contact', methods=['GET', 'POST'])
def home():
    """Renders feedback page."""
    if request.method == 'POST':
        return render_template('contact.html',title='Contact',year=datetime.now().year,)

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
