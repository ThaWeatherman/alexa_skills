import datetime
import re

from bs4 import BeautifulSoup
from flask import Flask
from flask_ask import Ask, statement
import requests


app = Flask(__name__)
ask = Ask(app, '/')


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


@ask.intent('SignificantDigits')
def get_significant_digits():
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
    return statement(speech_output).simple_card('538', speech_output)


if __name__ == '__main__':
    app.run()

