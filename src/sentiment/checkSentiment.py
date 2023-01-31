import boto3
from decimal import Decimal

from happytransformer import HappyTextClassification
from sklearn.linear_model import LinearRegression

import numpy as np
from datetime import date
import yfinance as yf

def sentiment_handler(event, context):
    model = HappyTextClassification(
        model_type="DISTILBERT", model_name="distilbert-base-uncased-finetuned-sst-2-english", num_labels=2)

    sentiment = {}
    scores = []

    headlines = event

    for ticker in headlines:
        sentiment[ticker] = []
        for headline in headlines[ticker]:
            title = headline[0]
            timestamp = headline[1]
            result = model.classify_text(title)
            intensity = result.score
            sentiment[ticker].append((title, timestamp, intensity))
            scores.append(intensity)

    factors_combined = [] # number of headlines * sentiment score

    for ticker in sentiment:
        s_scores = [sentiment[ticker][i][2] for i in range(len(sentiment[ticker]))]
        s_scores = np.array(s_scores)
        s_mean = np.mean(s_scores)
        x_val = len(sentiment[ticker]) * s_mean
        factors_combined.append(x_val)
        sentiment[ticker].append(x_val)

    '''
    # backtests
    today = date.today()
    today = str(today)

    x = []
    y = []

    for ticker in sentiment:
        num_headlines = len(ticker)
        sentiments = [sentiment[ticker][i][2] for i in range(len(sentiment[ticker]))]
        sentiments = np.array(sentiments)
        mean = np.mean(sentiments)
        try:
            price = yf.download(ticker, start=today, end=today)
            price = pd.DataFrame(price)
            per_change = (price['Close'][0] - price['Open'][0]) / price['Open'][0]
            x.append([num_headlines, mean])
            y.append(per_change)
        except:
            continue

    x = [p[0] * p[1] for p in x]
    y = [abs(v) for v in y]

    x2 = []
    y2 = []

    for i in range(len(x)):
        x2.append(x[i])
        y2.append(y[i])
        # print(x2)
        # print(y2)
        plt.xlabel('num headlines * average sentiment')
        plt.ylabel('daily percent change of stock')
        plt.scatter(x2, y2)
        plt.show()
    '''

    factors_combined = np.array(factors_combined)
    cut = np.mean(factors_combined)

    for ticker in sentiment:
        for i in range(len(sentiment[ticker]) - 1):
            title = sentiment[ticker][i][0]
            timestamp = sentiment[ticker][i][1]
            intensity = sentiment[ticker][i][2]
            if sentiment[ticker][-1] > cut:
                write_sentiment(ticker, title, True, Decimal(intensity), timestamp)
            else:
                write_sentiment(ticker, title, False, Decimal(intensity), timestamp)

    return headlines

# Helper function to write to the SentimentData table with the company, and the corresponding sentiment
# for that article
def write_sentiment(company: str, article: str, isExtreme: bool, sentiment: Decimal, time: int):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(
        'TradingBotStack-SentimentData66B14031-1HRN5XCCEOVXH')

    table.put_item(
        Item={
            'company': company,
            'article': article,
            'isExtreme': isExtreme,
            'sentiment': sentiment,
            'timeStamp': time
        }
    )
