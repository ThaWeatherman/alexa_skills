'''
Prints out all US airport codes on separate lines to stdout
'''
from bs4 import BeautifulSoup
import requests


URL = 'http://www.tsa.gov/data/apcp.xml'


def main():
    r = requests.get(URL)
    soup = BeautifulSoup(r.content, 'lxml')
    airports = soup.airports
    codes = '\n'.join(set([child.shortcode.text for child in airports.children]))
    print(codes)


if __name__ == '__main__':
    main()

