import requests
from bs4 import BeautifulSoup

def newsdata_handler(event, context):
    map_headlines = dict() # ticker -> list of associated headlines

    page = requests.get("https://www.bloomberg.com/feeds/sitemap_news.xml") # bloomberg daily main feed
    soup = BeautifulSoup(page.content, 'xml')

    # find all relevant headlines and tickers on bloomberg main feed
    headlines = soup.find_all('title')
    tickers = soup.find_all('stock_tickers')

    # extract from <element> </element>
    headlines = [headline.get_text() for headline in headlines]
    tickers = [ticker.get_text() for ticker in tickers]

    for i in range(len(headlines)):
        if tickers[i] == '': continue

        subtickers = tickers[i].split(', ')
        for subticker in subtickers:
            ticker_full = subticker.split(':')
            exchange = ticker_full[0]
            ticker = ticker_full[1]
            if exchange != 'NYSE' and exchange != 'NASDAQ': continue
            if ticker in map_headlines:
                map_headlines[ticker].append(headlines[i])
            else:
                map_headlines[ticker] = [headlines[i]]

    return map_headlines
