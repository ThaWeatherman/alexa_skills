import datetime

from flask import Flask, render_template
from flask_ask import Ask, statement, question
import requests


app = Flask(__name__)
ask = Ask(app, '/')


@ask.launch
def launched():
    return question('Welcome to Commodity Prices')


@ask.session_ended
def session_ended():
    return "{}", 200


@ask.intent('CommodityPrice', mapping={'commodity': 'Commodity'})
def price(commodity):
    try:
        commodity = commodity.lower()
        url = 'http://spot.seanmckaybeck.com/api/' + commodity
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
    except AttributeError:
        # happens when commodity is None
        speech_output = "I'm sorry, I didn't receive a commodity in your request."
    return statement(speech_output).simple_card('Commodity', speech_output)


@ask.intent('AvailableCommodities')
def available():
    url = 'http://spot.seanmckaybeck.com/api/all'
    try:
        r = requests.get(url)
        speech_output = 'The following are supported commodities: '
        d = r.json()
        del d['last']
        a = ', '.join(d.keys())
        speech_output += a
    except requests.exceptions.HTTPError:
        speech_output = "I'm sorry, there was an error retrieving the available commodities. Try again later."
    return statement(speech_output).simple_card('Commodity', speech_output)


if __name__ == '__main__':
    app.run(port=4343)

