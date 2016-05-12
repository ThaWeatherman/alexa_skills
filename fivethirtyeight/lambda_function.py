from datetime import datetime
import re

from bs4 import BeautifulSoup
import requests


def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])


def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "SignificantDigits":
        return get_significant_digits(intent, session)
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here

# --------------- Functions that control the skill's behavior ------------------


def build_digits_content(link):
    r = requests.get(link)
    soup = BeautifulSoup(r.content, 'html.parser')
    article = soup.article
    entry = article.select('div.entry-content')[0]
    regex = re.compile('\[.*\]', re.IGNORECASE)
    ret = ''
    for child in entry.children:
        if any(child.name == tag for tag in ['hr', 'div']):
            continue
        if child.name == 'h2':
            ret += child.text + ': '
        elif child.name == 'p':
            if child.find('i') or child.has_attr('class'):
                continue
            else:
                ret += regex.sub('', child.text)
    return ret


def get_significant_digits(intent, session):
    card_title = intent['name']
    session_attributes = {}
    should_end_session = True

    top_url = 'http://fivethirtyeight.com/tag/significant-digits/'
    r = requests.get(top_url)
    soup = BeautifulSoup(r.content, 'html.parser')
    posts = soup.select('div.post-info')
    most_recent = posts[0]
    d = datetime.strptime(most_recent.span.text, '%B %d, %Y')
    link = most_recent.h2.a.attrs['href']
    digits_text = build_digits_content(link)
    speech_output = ''
    if d.date() == datetime.today().date():
        speech_output = 'Here are today\'s significant digits from Five Thirty Eight. '
        speech_output += digits_text
    else:
        speech_output = 'Today\'s significant digits aren\'t posted yet, so here they are from {}. '.format(most_recent.span.text)
        speech_output += digits_text
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, '', should_end_session))


# --------------- Helpers that build all of the responses ----------------------


def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': 'SessionSpeechlet - ' + title,
            'content': 'SessionSpeechlet - ' + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }
