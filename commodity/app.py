import datetime

from flask import Flask, render_template
from flask_ask import Ask, statement
import requests


app = Flask(__name__)
ask = Ask(app, '/')


@ask.intent('CommodityPrice', mapping={'commodity': 'Commodity'})
def price(commodity):
    commodity = commodity.lower()
    url = 'http://spot.seanmckaybeck.com/api/' + commodity
    try:
        r = requests.get(url)
        if 'error' in r.json():
            speech_output = "Unknown commodity {}.".format(commodity)
        else:
            d = datetime.datetime.strptime(r.json()['last'], '%Y-%m-%d %H:%M:%S.%f')
            if d.date() == datetime.datetime.today():
                date_str = 'As of {} today, '.format(d.time().strftime('%I:%M %p'))
            else:
                date_str = 'As of {} on {}, '.format(d.time().strftime('%I:%M %p'), d.date().strftime('%B %d'))
            speech_output = "{} the price of {} is ${}.".format(date_str, commodity, r.json()[commodity])
    except requests.exceptions.HTTPError:
        speech_output = "I'm sorry, there was an error retrieving the price. Try again later."
    return statement(speech_output).simple_card('Commodity', speech_output)


if __name__ == '__main__':
    app.run()

