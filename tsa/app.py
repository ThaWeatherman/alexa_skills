from collections import defaultdict
import datetime

from flask import Flask
from flask_ask import Ask, statement
import requests


app = Flask(__name__)
ask = Ask(app, '/')


@ask.intent('TSAWaitTime')
def wait_time(airport, mapping={'airport': 'Airport'}):
    try:
        wait_time_values = ["No Wait", "1-10 minutes", "11-20 minutes", "21-30 minutes", "31+ minutes"]
        checkpoints = defaultdict(list)
        r = requests.get('http://apps.tsa.dhs.gov/MyTSAWebService/GetWaitTimes.ashx?ap={}&output=json'.format(airport))
        data = r.json()
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
    except requests.exceptions.HTTPError as e:
        speech_output = "I'm sorry, I was unable to get information about the airport {}. Are you sure that is a valid airport code?".format(airport)
    return statement(speech_output).simple_card('TSA', speech_output)


if __name__ == '__main__':
    app.run(port=4346)

