import requests
from bs4 import BeautifulSoup
import lxml

from dateutil import parser

def newsdata_handler(event, context):
    # Scraping Bloomberg
    tickerDictionary = dict()
    page = requests.get("https://www.bloomberg.com/feeds/sitemap_news.xml")
    soup = BeautifulSoup(page.content, 'xml')
    soupHeadlines = soup.find_all('title')
    soupTickers = soup.find_all('stock_tickers')
    soupDates = soup.find_all('news:publication_date')

    bloomHeadlines = []
    bloomStockTickers = []
    bloomSoupDates = []

    for i in range(len(soupHeadlines)):
        bloomHeadlines.append(soupHeadlines[i].get_text())
        bloomStockTickers.append(soupTickers[i].get_text())
        timestamp = parser.parse(soupDates[i].get_text())
        timestamp = int(timestamp.timestamp() * 1000)
        bloomSoupDates.append(timestamp)

    for i in range(len(bloomStockTickers)):
        if bloomStockTickers[i] != '<news:stock_tickers/>' or bloomStockTickers[i] == '':
            tickerCount = bloomStockTickers[i].count(',')
            if tickerCount > 0:
                tickers = bloomStockTickers[i].split(',')
                for t in range(len(tickers)):
                    tickers[t] = tickers[t][tickers[t].find(':') + 1:]
                    if tickers[t] != '' and not tickers[t].isnumeric():
                        if tickers[t] in tickerDictionary:
                            tickerDictionary[tickers[t]].append(
                                (bloomHeadlines[i], bloomSoupDates[i]))
                        else:
                            tickerDictionary[tickers[t]] = [
                                (bloomHeadlines[i], bloomSoupDates[i])]
            else:
                tickers = bloomStockTickers[i]
                for t in range(len(tickers)):
                    tickers = tickers[tickers.find(':') + 1:]
                if tickers != '' and not tickers.isnumeric():
                    if tickers in tickerDictionary:
                        tickerDictionary[tickers].append(
                            (bloomHeadlines[i], bloomSoupDates[i]))
                    else:
                        tickerDictionary[tickers] = [
                            (bloomHeadlines[i], bloomSoupDates[i])]

    return tickerDictionary

'''
# Nasdaq, not working smoothly yet

import requests
from bs4 import BeautifulSoup

tickerDictionary = dict()
headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:82.0) Gecko/20100101 Firefox/82.0' }
page = requests.get('https://www.nasdaq.com/feed/rssoutbound?category=Stocks', headers = headers)

soup = BeautifulSoup(page.content, 'xml')
soupItems = soup.find_all('item')
nasHeadlines = []
nasStockTickers = []
nasSoupDates = []

for i in range(len(soupItems)):
    soupDetail = BeautifulSoup(str(soupItems[i]), 'xml')
    title = soupDetail.find_all('title')
    ticker = soupDetail.find_all('tickers')
    date = soupDetail.find_all('pubDate')
    if len(title) == 1 and len(ticker) == 1 and len(date) == 1:
        nasHeadlines.append(title[0].get_text())
        nasStockTickers.append(ticker[0].get_text())
        nasSoupDates.append(date[0].get_text())
            
for i in range(len(nasStockTickers)):
    tickerCount = nasStockTickers[i].count(',')
    if tickerCount > 0:
        tickers = nasStockTickers[i].split(',')
        for t in range(len(tickers)):
            tickers[t] = tickers[t][tickers[t].find(':')+1:]
            if tickers[t] != '' and tickers[t].isnumeric() == False:
            if tickers[t] in tickerDictionary:
                tickerDictionary[tickers[t]].append((nasHeadlines[i],nasSoupDates[i]))
            else:
                tickerDictionary[tickers[t]] = [(nasHeadlines[i],nasSoupDates[i])]
    else:
        tickers = nasStockTickers[i]
        for t in range(len(tickers)):
            tickers = tickers[tickers.find(':')+1:]
        if tickers != '' and tickers.isnumeric() == False:
            if tickers in tickerDictionary:
                tickerDictionary[tickers].append((nasHeadlines[i],nasSoupDates[i]))
            else:
                tickerDictionary[tickers] = [(nasHeadlines[i],nasSoupDates[i])]
                
print(tickerDictionary)
'''