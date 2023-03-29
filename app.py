from flask import Flask, render_template, request
import os
from dotenv import dotenv_values
import openai
import requests
from time import sleep

app = Flask(__name__)


def chat(msgs):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=msgs
    )
    message = response['choices'][0]['message']
    return message


def fetch_news(symbol, key):
    records = []
    headers = {
        'x-api-key': key,
    }
    params = {
        'q': symbol,
        'topic': 'finance',
        'countries': 'US',
        'lang': 'en',
        'from_rank': 0,
        'to_rank': 100,
        'sort_by': 'date',
        'page_size': 5,
        # 'to': '1 day ago'
    }

    r = requests.get('https://api.newscatcherapi.com/v2/search', params=params, headers=headers)
    data = r.json()
    if 'articles' in data:
        articles = data['articles']
        for article in articles:
            records.append({'title': article['title'], 'summary': article['summary']})

    return {'symbol': symbol, 'articles': records}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def search():
    # OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    # NEWSCATCHER_API = os.environ.get('NEWSCATCHER_API')
    symbol = request.form['symbol'].upper()
    message_history = []
    sentiments = []
    openai.api_key = OPENAI_API_KEY
    system_message = 'You will work as a Sentiment Analysis for Financial news. I will share news headline and summary. You will only answer as:\n\n BEARISH,BULLISH,NEUTRAL. No further explanation. \n Got it?'
    message_history.append({'content': system_message, 'role': 'user'})
    response = chat(message_history)
    articles = fetch_news(symbol, NEWSCATCHER_API)['articles']
    for article in articles:
        user_message = '{}\n{}'.format(article['title'], article['summary'])
        message_history.append({'content': user_message, 'role': 'user'})
        response = chat(message_history)
        sentiments.append(
            {'title': article['title'], 'summary': article['summary'], 'signal': response['content'].replace('.', '')})
        message_history.pop()
        sleep(1)
    # Render the HTML template with the search results
    return render_template('index.html', data=sentiments, query=symbol)


if __name__ == '__main__':
    config = dotenv_values(".env")
    NEWSCATCHER_API = config['NEWSCATCHER_API']
    OPENAI_API_KEY = config['OPENAI_API_KEY']
    app.run(debug=True)
