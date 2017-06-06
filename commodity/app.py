import datetime

from flask import Flask, render_template
from flask_ask import Ask, statement, question
import requests


app = Flask(__name__)
ask = Ask(app, '/')
with open('speech_assets/LIST_OF_COMMODITIES') as f:
    app.config['SUPPORTED'] = [ c.strip() for c in f.readlines() ]
HELP = "You can ask for the available commodities or for the price of a specific commodity. What can I do for you?"


@ask.launch
def launched():
    return question('Welcome to Commodity Prices. ' + HELP)


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
            speech_output = "I'm sorry but I don't track the commodity {}. ".format(commodity)
            speech_output += "You can ask about any of the following: " + ", ".join(app.config['SUPPORTED'])
            return question(speech_output)
        else:
            d = datetime.datetime.strptime(r.json()['last'], '%Y-%m-%d %H:%M:%S.%f')
            if d.date() == datetime.datetime.today():
                date_str = 'As of {} today, '.format(d.time().strftime('%I:%M %p'))
            else:
                date_str = 'As of {} on {}, '.format(d.time().strftime('%I:%M %p'), d.date().strftime('%B %d'))
            speech_output = "{} the price of {} is ${}.".format(date_str, commodity, r.json()[commodity])
    except requests.exceptions.HTTPError:
        speech_output = "I'm sorry, there was an error retrieving the price. Please try again later."
    except AttributeError:
        # happens when commodity is None
        speech_output = "I'm sorry, I didn't receive a valid commodity in your request. "
        speech_output += "You can ask about any of the following: " + ", ".join(app.config['SUPPORTED'])
        return question(speech_output)
    return statement(speech_output).simple_card('Commodity Prices', speech_output)


@ask.intent('AvailableCommodities')
def available():
    speech_output = "The following are supported commodities: " + ", ".join(app.config['SUPPORTED'])
    return statement(speech_output).simple_card('Commodity Prices', speech_output)


@ask.intent('AMAZON.HelpIntent')
def help():
    return question(HELP).reprompt("I didn't get that, what can I do for you?")


@ask.intent('AMAZON.StopIntent')
def stop():
    return statement('Goodbye')


@ask.intent('AMAZON.CancelIntent')
def cancel():
    return statement('Goodbye')


if __name__ == '__main__':
    app.run(port=4343)

