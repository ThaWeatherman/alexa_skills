from flask import Flask, render_template
from flask_ask import Ask, statement
import requests
import trackopy


app = Flask(__name__)
app.config.from_pyfile('config.py')
ask = Ask(app, '/')
t = trackopy.Trackobot(app.config['USERNAME'], app.config['PASSWORD'])


@ask.intent('Stats')
def status(ashero, asdeck, vshero, vsdeck):
    resp = ''
    if ashero is None and asdeck is None and vshero is None and vsdeck is None:
        stats = t.stats(stats_type='classes', time_range='current_month')
        total = stats['stats']['overall']['total']
        wins = stats['stats']['overall']['wins']
        losses = stats['stats']['overall']['losses']
        resp = 'For the current month, you have played {} games, with {} wins and {} losses'.format(total, wins, losses)
    elif (ashero is not None or vshero is not None) and asdeck is None and vsdeck is None:
        stats = t.stats(stats_type='classes', time_range='current_month', as_hero=ashero, vs_hero=vshero)
        total = stats['stats']['overall']['total']
        wins = stats['stats']['overall']['wins']
        losses = stats['stats']['overall']['losses']
        if ashero is not None and vshero is None:
            resp = 'For the current month, you have played {} games as {}, with {} wins and {} losses'.format(total, ashero, wins, losses)
        elif ashero is None and vshero is not None:
            resp = 'For the current month, you have played {} games against {}, with {} wins and {} losses'.format(total, vshero, wins, losses)
        else:
            resp = 'For the current month, you have played {} games as {} against {}, with {} wins and {} losses'.format(total, ashero, vshero, wins, losses)
    return statement(resp).simple_card('Trackobot', resp)


if __name__ == '__main__':
    app.run(port=4347)

