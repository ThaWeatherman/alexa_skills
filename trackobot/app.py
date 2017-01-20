from flask import Flask, render_template
from flask_ask import Ask, statement
import requests
import trackopy


app = Flask(__name__)
app.config.from_pyfile('config.py')
ask = Ask(app, '/')
t = trackopy.Trackobot(app.config['USERNAME'], app.config['PASSWORD'])
decks = t.decks()  # TODO wat do if decks list is updated?


def _find_deck_id(hero, deck_name):
    for deck in decks['decks']:
        if deck['name'].lower() == deck_name.lower() and deck['hero'].lower() == hero.lower():
            return deck['id']
    return 0  # passing 0 for a deck id is fine. trackobot just ignores it


@ask.intent('Stats')
def stats(ashero, asdeck, vshero, vsdeck):
    resp = ''
    if ashero is None and asdeck is None and vshero is None and vsdeck is None:
        stats = t.stats(stats_type='classes', time_range='current_month')
        total = stats['stats']['overall']['total']
        wins = stats['stats']['overall']['wins']
        losses = stats['stats']['overall']['losses']
        resp = render_template('msg', total=total, win=wins, loss=losses)
    elif (ashero is not None or vshero is not None) and asdeck is None and vsdeck is None:
        stats = t.stats(stats_type='classes', time_range='current_month', as_hero=ashero, vs_hero=vshero)
        total = stats['stats']['overall']['total']
        wins = stats['stats']['overall']['wins']
        losses = stats['stats']['overall']['losses']
        if ashero is not None and vshero is None:
            resp = render_template('as_msg', total=total, ashero=ashero, win=wins, loss=losses)
        elif ashero is None and vshero is not None:
            resp = render_template('against_msg', total=total, vshero=vshero, win=wins, loss=losses)
        else:
            resp = render_template('as_against_msg', total=total, ashero=ashero, vshero=vshero, win=wins, loss=losses)
    elif (ashero is not None and asdeck is not None) or (vshero is not None and vsdeck is not None):
        if ashero is not None:
            as_deck = _find_deck_id(ashero, asdeck)
        if vshero is not None:
            vs_deck = _find_deck_id(vshero, vsdeck)
        stats = t.stats(stats_type='decks', time_range='current_month', as_deck=as_deck, vs_deck=vs_deck)
        total = stats['stats']['overall']['total']
        wins = stats['stats']['overall']['wins']
        losses = stats['stats']['overall']['losses']
        if ashero is not None and vshero is None:
            resp = render_template('as_msg', total=total, ashero=asdeck+' '+ashero, win=wins, loss=losses)
        elif vshero is not None and ashero is None:
            resp = render_template('against_msg', total=total, vshero=vsdeck+' '+vshero, win=wins, loss=losses)
        else:
            resp = render_template('as_against_msg', total=total, ashero=asdeck+' '+ashero, vshero=vsdeck+' '+vshero, win=wins, loss=losses)
    else:
        resp = render_template('error_msg', ashero=ashero, asdeck=asdeck, vshero=vshero, vsdeck=vsdeck)
    return statement(resp).simple_card('Trackobot', resp)


if __name__ == '__main__':
    app.run(port=4347)

