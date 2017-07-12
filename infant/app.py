from base64 import b64encode
import datetime
from email.utils import formatdate
from functools import wraps
import time as ti

import aniso8601
from flask import Flask, session, render_template
from flask_ask import import Ask, statement, question
import humanize
import requests


app = Flask(__name__)
ask = Ask(app, "/")
BASE = "https://xwnldnhmzk.execute-api.us-east-1.amazonaws.com/dev"  # TODO load from conf file
SESSION_NAME = 'name'
SESSION_DATE = 'date'
SESSION_TIME = 'time'
SESSION_KIND = 'kind'
SESSION_SIDE = 'side'
SESSION_LENGTH = 'length'


# -----
# utils
# -----
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if hasattr(session, 'user') and hasattr(session.user, 'accessToken'):
            return f(*args, **kwargs)
        else:
            return statement('You must login before performing this action.').link_account_card()
    return decorated


def to_rfc822(dt: datetime.datetime) -> str:
    return formatdate(ti.mktime(dt.timetuple()))


def encoder(obj) -> str:
    if isinstance(obj, datetime.date) or isinstance(obj, datetime.time):
        return obj.isoformat()


def datetime_to_text(dt: datetime.datetime) -> str:
    date_str = humanize.naturalday(dt, format="%A %B %-d")
    time_str = dt.strftime("%-I %-M %p")
    return f"{date_str} at {time_str}"


def name_to_id(name: str, user_token: str) -> dict:
    endpoint = BASE + "/api/child/name"
    r = requests.get(endpoint,
                     headers={'Authorization': 'Basic %s' % b64encode(bytes(user_token+":"))},
                     data={'name': name})
    if r.status_code != 200:
        return None
    return r.json()


# -------
# intents
# -------
@ask.launch
def launched():
    return question('Welcome to Infant Tracker. ' + render_template("help"))


@ask.session_ended
def session_ended():
    return "{}", 200


@ask.intent('AMAZON.HelpIntent')
def help():
    return question(render_template("help")).reprompt("I didn't get that, what can I do for you?")


@ask.intent('AMAZON.StopIntent')
def stop():
    return statement('Goodbye')


@ask.intent('AMAZON.CancelIntent')
def cancel():
    return statement('Goodbye')


# needed actions:
# stats for the day
@ask.intent("ListChildrenIntent")
@login_required
def list_children():
    user_token = session.user.accessToken
    endpoint = "/api/child/all"
    r = requests.get(BASE+endpoint, headers={'Authorization': 'Basic %s' % b64encode(bytes(user_token+":"))})
    if r.status_code != 200:
        return statement(render_template("failed_request"))
    num_kids = len(r.json()["children"])
    if num_kids == 0:
        return statement("You have no children.").simple_card("You have no children")
    names = [child["name"] for child in r.json()["children"]]
    if num_kids == 1:
        ch = "child"
        name_str = names[0]
    else:
        ch = "children"
        name_str = ", ".join(names[:-1])
        name_str += " and " + names[-1]
    resp = f"You have {num_kids} {ch} named {named_str}"
    return statement(resp).simple_card(resp)


@ask.intent("AddChildIntent", mapping={'name': 'Name'})
@login_required
def add_child(name):
    if name is None:
        return question(render_template("child_name")).reprompt(render_template("child_name_reprompt"))
    user_token = session.user.accessToken
    endpoint = "/api/child"
    r = requests.post(BASE+endpoint,
                      headers={'Authorization': 'Basic %s' % b64encode(bytes(user_token+":"))},
                      data={'name': name})
    if r.status_code != 200:
        return statement(render_template("failed_request"))
    resp = f"{name} was added as your child"
    return statement(resp).simple_card(resp)


@ask.intent("DeleteChildIntent", mapping={'name': 'Name'})
@login_required
def delete_child(name):
    if name is None:
        return question(render_template("child_name")).reprompt(render_template("child_name_reprompt"))
    user_token = session.user.accessToken
    endpoint = "/api/child"
    child = name_to_id(name, user_token)
    if "children" in child:
        text = render_template("multiple_name")
        return statement(text).simple_card(text)
    child_id = child["_id"]
    r = requests.delete(BASE+endpoint,
                        headers={'Authorization': 'Basic %s' % b64encode(bytes(user_token+":"))},
                        data={'child_id': child_id})
    if r.status_code != 200:
        return statement(render_template("failed_request"))
    resp = f"{name} was deleted"
    return statement(resp).simple_card(resp)


@ask.intent("AddDiaperIntent",
            mapping={'name': 'Name', 'kind': 'Kind', 'date': 'Date', 'time': 'Time'},
            convert={'date': 'date', 'time': 'time'})
@login_required
def add_diaper(name, kind, date, time):
    if name is not None:
        if SESSION_KIND not in session.attributes or session.attributes[SESSION_KIND] is None:
            return _save_and_prompt("kind",
                                    **{SESSION_NAME: name, SESSION_DATE: date, SESSION_TIME: time})
        elif SESSION_DATE not in session.attributes or session.attributes[SESSION_DATE] is None:
            return _save_and_prompt("date",
                                    **{SESSION_NAME: name, SESSION_SIDE: side, SESSION_TIME: time})
        elif SESSION_TIME not in session.attributes or session.attributes[SESSION_TIME] is None:
            return _save_and_prompt("time",
                                    **{SESSION_NAME: name, SESSION_SIDE: side, SESSION_DATE: date})
    elif kind is not None:
        if SESSION_NAME not in session.attributes or session.attributes[SESSION_NAME] is None:
            return _save_and_prompt("name",
                                    **{SESSION_KIND: kind, SESSION_DATE: date, SESSION_TIME: time})
        elif SESSION_DATE not in session.attributes or session.attributes[SESSION_DATE] is None:
            return _save_and_prompt("date",
                                    **{SESSION_NAME: name, SESSION_SIDE: side, SESSION_TIME: time})
        elif SESSION_TIME not in session.attributes or session.attributes[SESSION_TIME] is None:
            return _save_and_prompt("time",
                                    **{SESSION_NAME: name, SESSION_SIDE: side, SESSION_DATE: date})
    elif date is not None:
        if SESSION_NAME not in session.attributes or session.attributes[SESSION_NAME] is None:
            return _save_and_prompt("name",
                                    **{SESSION_KIND: kind, SESSION_DATE: date, SESSION_TIME: time})
        elif SESSION_KIND not in session.attributes or session.attributes[SESSION_KIND] is None:
            return _save_and_prompt("kind",
                                    **{SESSION_NAME: name, SESSION_DATE: date, SESSION_TIME: time})
        elif SESSION_TIME not in session.attributes or session.attributes[SESSION_TIME] is None:
            return _save_and_prompt("time",
                                    **{SESSION_NAME: name, SESSION_SIDE: side, SESSION_DATE: date})
    elif time is not None:
        if SESSION_NAME not in session.attributes or session.attributes[SESSION_NAME] is None:
            return _save_and_prompt("name",
                                    **{SESSION_KIND: kind, SESSION_DATE: date, SESSION_TIME: time})
        elif SESSION_KIND not in session.attributes or session.attributes[SESSION_KIND] is None:
            return _save_and_prompt("kind",
                                    **{SESSION_NAME: name, SESSION_DATE: date, SESSION_TIME: time})
        elif SESSION_DATE not in session.attributes or session.attributes[SESSION_DATE] is None:
            return _save_and_prompt("date",
                                    **{SESSION_NAME: name, SESSION_SIDE: side, SESSION_TIME: time})
    else:
        return _gather("name")
    # the first 4 blocks will always fall through to here while the else will not
    endpoint = "/api/diaper"
    user_token = session.user.accessToken
    child = name_to_id(name, user_token)
    if "children" in child:
        text = render_template("multiple_name")
        return statement(text).simple_card(text)
    child_id = child["_id"]
    kind = session.attributes[SESSION_KIND]
    date = aniso8601.parse_date(session.attributes[SESSION_DATE])
    time = aniso8601.parse_time(session.attributes[SESSION_TIME])
    dt = datetime.datime.combine(date, time)
    r = requests.post(BASE+endpoint,
                      headers={'Authorization': 'Basic %s' % b64encode(bytes(user_token+":"))},
                      data={'child_id': child_id, 'kind': kind, 'datetime': to_rfc822(dt)})
    if r.status_code != 200:
        return statement(render_template("failed_request"))  # TODO handle 400
    return statement("Diaper added.").simple_card("Diaper added")


@ask.intent("AddFeedingIntent"
            mapping={'name': 'Name', 'side': 'Side', 'date': 'Date', 'time': 'Time', 'length': 'Length'},
            convert={'date': 'date', 'time': 'time'})
@login_required
def add_feeding(name, side, date, time, length):
    if name is not None:
        if SESSION_SIDE not in session.attributes or session.attributes[SESSION_SIDE] is None:
            return _save_and_prompt("side",
                                    **{SESSION_NAME: name, SESSION_DATE: date, SESSION_TIME: time, SESSION_LENGTH: length})
        elif SESSION_DATE not in session.attributes or session.attributes[SESSION_DATE] is None:
            return _save_and_prompt("date",
                                    **{SESSION_NAME: name, SESSION_SIDE: side, SESSION_TIME: time, SESSION_LENGTH: length})
        elif SESSION_TIME not in session.attributes or session.attributes[SESSION_TIME] is None:
            return _save_and_prompt("time",
                                    **{SESSION_NAME: name, SESSION_SIDE: side, SESSION_DATE: date, SESSION_LENGTH: length})
        elif SESSION_LENGTH not in session.attributes or session.attributes[SESSION_LENGTH] is None:
            return _save_and_prompt("length",
                                    **{SESSION_NAME: name, SESSION_SIDE: side, SESSION_DATE: date, SESSION_TIME: time})
    elif side is not None:
        if SESSION_NAME not in session.attributes or session.attributes[SESSION_NAME] is None:
            return _save_and_prompt("name",
                                    **{SESSION_TIME: time, SESSION_SIDE: side, SESSION_DATE: date, SESSION_LENGTH: length})
        elif SESSION_DATE not in session.attributes or session.attributes[SESSION_DATE] is None:
            return _save_and_prompt("date",
                                    **{SESSION_NAME: name, SESSION_SIDE: side, SESSION_TIME: time, SESSION_LENGTH: length})
        elif SESSION_TIME not in session.attributes or session.attributes[SESSION_TIME] is None:
            return _save_and_prompt("time",
                                    **{SESSION_NAME: name, SESSION_SIDE: side, SESSION_DATE: date, SESSION_LENGTH: length})
        elif SESSION_LENGTH not in session.attributes or session.attributes[SESSION_LENGTH] is None:
            return _save_and_prompt("length",
                                    **{SESSION_NAME: name, SESSION_SIDE: side, SESSION_DATE: date, SESSION_TIME: time})
    elif date is not None:
        if SESSION_SIDE not in session.attributes or session.attributes[SESSION_SIDE] is None:
            return _save_and_prompt("side",
                                    **{SESSION_NAME: name, SESSION_DATE: date, SESSION_TIME: time, SESSION_LENGTH: length})
        elif SESSION_NAME not in session.attributes or session.attributes[SESSION_NAME] is None:
            return _save_and_prompt("name",
                                    **{SESSION_TIME: time, SESSION_SIDE: side, SESSION_DATE: date, SESSION_LENGTH: length})
        elif SESSION_TIME not in session.attributes or session.attributes[SESSION_TIME] is None:
            return _save_and_prompt("time",
                                    **{SESSION_NAME: name, SESSION_SIDE: side, SESSION_DATE: date, SESSION_LENGTH: length})
        elif SESSION_LENGTH not in session.attributes or session.attributes[SESSION_LENGTH] is None:
            return _save_and_prompt("length",
                                    **{SESSION_NAME: name, SESSION_SIDE: side, SESSION_DATE: date, SESSION_TIME: time})
    elif time is not None:
        if SESSION_SIDE not in session.attributes or session.attributes[SESSION_SIDE] is None:
            return _save_and_prompt("side",
                                    **{SESSION_NAME: name, SESSION_DATE: date, SESSION_TIME: time, SESSION_LENGTH: length})
        elif SESSION_DATE not in session.attributes or session.attributes[SESSION_DATE] is None:
            return _save_and_prompt("date",
                                    **{SESSION_NAME: name, SESSION_SIDE: side, SESSION_TIME: time, SESSION_LENGTH: length})
        elif SESSION_NAME not in session.attributes or session.attributes[SESSION_NAME] is None:
            return _save_and_prompt("name",
                                    **{SESSION_TIME: time, SESSION_SIDE: side, SESSION_DATE: date, SESSION_LENGTH: length})
        elif SESSION_LENGTH not in session.attributes or session.attributes[SESSION_LENGTH] is None:
            return _save_and_prompt("length",
                                    **{SESSION_NAME: name, SESSION_SIDE: side, SESSION_DATE: date, SESSION_TIME: time})
    elif length is not None:
        if SESSION_SIDE not in session.attributes or session.attributes[SESSION_SIDE] is None:
            return _save_and_prompt("side",
                                    **{SESSION_NAME: name, SESSION_DATE: date, SESSION_TIME: time, SESSION_LENGTH: length})
        elif SESSION_DATE not in session.attributes or session.attributes[SESSION_DATE] is None:
            return _save_and_prompt("date",
                                    **{SESSION_NAME: name, SESSION_SIDE: side, SESSION_TIME: time, SESSION_LENGTH: length})
        elif SESSION_NAME not in session.attributes or session.attributes[SESSION_NAME] is None:
            return _save_and_prompt("name",
                                    **{SESSION_TIME: time, SESSION_SIDE: side, SESSION_DATE: date, SESSION_LENGTH: length})
        elif SESSION_TIME not in session.attributes or session.attributes[SESSION_TIME] is None:
            return _save_and_prompt("time",
                                    **{SESSION_NAME: name, SESSION_SIDE: side, SESSION_DATE: date, SESSION_LENGTH: length})
    else:
        return _gather("name")
    # the first 5 blocks will always fall through to here while the else will not
    endpoint = "/api/feeding"
    user_token = session.user.accessToken
    if name is None:
        name = session.attributes[SESSION_NAME]
    child = name_to_id(name, user_token)
    if "children" in child:
        text = render_template("multiple_name")
        return statement(text).simple_card(text)
    child_id = child["_id"]
    side = session.attributes[SESSION_SIDE]
    length = session.attributes[SESSION_LENGTH]
    date = aniso8601.parse_date(session.attributes[SESSION_DATE])
    time = aniso8601.parse_time(session.attributes[SESSION_TIME])
    dt = datetime.datime.combine(date, time)
    r = requests.post(BASE+endpoint,
                      headers={'Authorization': 'Basic %s' % b64encode(bytes(user_token+":"))},
                      data={'child_id': child_id, 'side': side, 'datetime': to_rfc822(dt), 'duration': length})
    if r.status_code != 200:
        return statement(render_template("failed_request"))  # TODO handle 400
    return statement("Feeding added.").simple_card("Feeding added")


@ask.intent("GetRecentDiaperIntent", mapping={'name': 'Name'})
@login_required
def get_recent_diaper(name):
    if name is None:
        return question(render_template("child_name")).reprompt(render_template("child_name_reprompt"))
    user_token = session.user.accessToken
    endpoint = "/api/diaper/recent"
    child = name_to_id(name, user_token)
    if "children" in child:
        text = render_template("multiple_name")
        return statement(text).simple_card(text)
    child_id = child["_id"]
    r = requests.get(BASE+endpoint,
                     headers={'Authorization': 'Basic %s' % b64encode(bytes(user_token+":"))},
                     data={'child_id': child_id})
    if r.status_code != 200:
        return statement(render_template("failed_request"))
    # change date to text
    dt = datetime.datetime.strptime(r.json()['datetime'], "%Y-%m-%dT%H:%M:%S.%fZ")
    text = datetime_to_text(dt)
    resp = f"The most recent diaper was {text} and was a {r.json()['kind']}."
    return statement(resp).simple_card(resp)


@ask.intent("GetRecentFeedingIntent", mapping={'name': 'Name'})
@login_required
def get_recent_feeding(name):
    if name is None:
        return question(render_template("child_name")).reprompt(render_template("child_name_reprompt"))
    user_token = session.user.accessToken
    endpoint = "/api/feeding/recent"
    child = name_to_id(name, user_token)
    if "children" in child:
        text = render_template("multiple_name")
        return statement(text).simple_card(text)
    child_id = child["_id"]
    r = requests.get(BASE+endpoint,
                     headers={'Authorization': 'Basic %s' % b64encode(bytes(user_token+":"))},
                     data={'child_id': child_id})
    if r.status_code != 200:
        return statement(render_template("failed_request"))
    # change date to text
    dt = datetime.datetime.strptime(r.json()['datetime'], "%Y-%m-%dT%H:%M:%S.%fZ")
    text = datetime_to_text(dt)
    resp = f"The most recent feeding was {text} and was on the {r.json()['side']} for {r.json()['duration']} minutes."
    return statement(resp).simple_card(resp)


# --------------
# intent helpers
# --------------
def _gather(template_name):
    text = render_template(template_name)
    return question(text).reprompt(text)


def _save_and_prompt(template_name, **kwargs):
    session.encoder = encoder
    for k in kwargs:
        session.attributes[k] = kwargs[k]
    return _gather(template_name)

