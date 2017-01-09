from flask import Flask, render_template
from flask_ask import Ask, statement
import requests


app = Flask(__name__)
ask = Ask(app, '/')


@ask.intent('OperationStatus')
def status():
    r = requests.get('http://status.seanmckaybeck.com')
    resp = render_template('status', code=r.json()['status'])
    return statement(resp).simple_card('Status', resp)


if __name__ == '__main__':
    app.run()

