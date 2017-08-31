"""
The flask application package.
"""

from flask import Flask
from flask_bootstrap import Bootstrap
from flask_moment import Moment
import urllib3
urllib3.disable_warnings()


app = Flask(__name__)
app.config['SECRET_KEY'] = 'investmentcondofinder'
bootstrap=Bootstrap(app)
moment = Moment(app)

#import FlaskWebProject.views
import FlaskWebProject.investmentcondofinder
import FlaskWebProject.Investment_Condo_Finder_Submit_V3
