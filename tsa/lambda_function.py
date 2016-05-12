"""
This sample demonstrates a simple skill built with the Amazon Alexa Skills Kit.
The Intent Schema, Custom Slots, and Sample Utterances for this skill, as well
as testing instructions are located at http://amzn.to/1LzFrj6

For additional samples, visit the Alexa Skills Kit Getting Started guide at
http://amzn.to/1LGWsLG
"""

from __future__ import print_function
from collections import defaultdict
from datetime import datetime
import json
import urllib2


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
    if intent_name == "TSAWaitTime":
        return get_wait_time(intent, session)
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


def get_wait_time(intent, session):
    """ Gets the current wait time at the specified airport
    """

    card_title = intent['name']
    session_attributes = {}
    should_end_session = True

    if 'Airport' in intent['slots']:
        airport = intent['slots']['Airport']['value']
        try:
            wait_time_values = ["No Wait", "1-10 minutes", "11-20 minutes", "21-30 minutes", "31+ minutes"]
            checkpoints = defaultdict(list)
            resp = urllib2.urlopen('http://apps.tsa.dhs.gov/MyTSAWebService/GetWaitTimes.ashx?ap={}&output=json'.format(airport))
            data = json.load(resp)
            for entry in data['WaitTimes']:
                d = datetime.strptime(entry['Created_Datetime'], '%m/%d/%Y %I:%M:%S %p')
                checkpoints[entry['CheckpointIndex']].append({ 'datetime': d, 'waittime': wait_time_values[int(entry['WaitTimeIndex'])-1] })
            speech_output = 'TSA provided the following wait times for {}: '.format(airport)
            for checkpoint in checkpoints:
                m = max(checkpoints[checkpoint], key=lambda x: x['datetime'])
                if m['datetime'].date() == datetime.today().date():
                    speech_output += 'Checkpoint {}: as of {} the wait time is {}. '.format(checkpoint, m.time().strftime('%I:%M %p'), entry['waittime'])
                else:
                    speech_output += 'Checkpoint {}: there have been no recorded wait times today. '.format(checkpoint)
        except urllib2.HTTPError as e:
            speech_output = "I'm sorry, I was unable to get information about the airport {}. Are you sure that is a valid airport code?".format(airport)
    else:
        speech_output = "I'm sorry, I didn't understand that. You did not include an airport code."
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
