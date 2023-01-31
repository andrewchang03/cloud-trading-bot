import boto3
from boto3.dynamodb.conditions import Key, Attr

import pandas as pd
import pandas as pd
import yfinance as yf
import uuid
from decimal import Decimal

import time
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def strategy_handler(event, context):
    
    company_data = get_stock_sentiment()
    for company in company_data:
        if not company_data[company][0] > 0:
            continue

        logger.info(f'Getting options for company {company}')
        options = getOptions(company)
        if not options.empty:
            logger.info('Found options for the company')
            # smallest difference in last price
            min_diff = abs(options["lastPrice_x"] - options["lastPrice_y"]).min()
            bought = options.loc[abs(
                options["lastPrice_x"] - options["lastPrice_y"]) == min_diff]
            if bought.empty:
                continue
            bought = bought.drop(columns=['bid_x', 'ask_x', 'change_x', 'percentChange_x',
                                        'volume_x', 'openInterest_x',
                                        'inTheMoney_x', 'contractSize_x', 'currency_x',
                                        'lastTradeDate_x', 'impliedVolatility_x',
                                        'bid_y', 'ask_y', 'change_y', 'percentChange_y',
                                        'volume_y', 'openInterest_y',
                                        'inTheMoney_y', 'contractSize_y', 'currency_y',
                                        'lastTradeDate_y', 'impliedVolatility_y'])

            company = company.split('/')
            company = '.'.join(company)
            currentTimeInMillis = (int)(time.time()) * 1000

            call_uuid = str(uuid.uuid4())
            put_uuid = str(uuid.uuid4())

            write_option(call_uuid, currentTimeInMillis,
                        bought['contractSymbol_x'].iloc[0],
                        Decimal(str(bought['strike'].iloc[0])),
                        bought['ExpirationDate'].iloc[0],
                        'CALL',
                        Decimal(str(bought['lastPrice_x'].iloc[0])))
            write_option(put_uuid, currentTimeInMillis,
                        bought['contractSymbol_y'].iloc[0],
                        Decimal(str(bought['strike'].iloc[0])),
                        bought['ExpirationDate'].iloc[0],
                        'PUT',
                        Decimal(str(bought['lastPrice_y'].iloc[0])))
        else:
            logger.info('Could not find options for the company')

''' 
Takes in a ticker as a string and 
returns a pandas dataframe of options 
with matching calls and puts in each row 
'''

def getOptions(ticker):
    tick = yf.Ticker(ticker)
    try:
        expirations = tick.options
    except Exception as e:
        logger.info('Issue fetching options. No option or not an American ticker. Skipping...')
        return pd.DataFrame()
    
    if len(expirations) == 0:
        # no options error also
        return pd.DataFrame()

    puts = pd.DataFrame()
    for date in expirations[:1]:  # take only earliest expiration
        opt = tick.option_chain(date)
        opt = pd.DataFrame().append(opt.puts)
        opt["ExpirationDate"] = date
        puts = puts.append(opt)

    calls = pd.DataFrame()
    for date in expirations[:1]:  # take only earliest expiration
        opt = tick.option_chain(date)
        opt = pd.DataFrame().append(opt.calls)
        opt["ExpirationDate"] = date
        calls = calls.append(opt)

    options_full = calls.merge(puts, on=["strike", "ExpirationDate"])
    return options_full

# Helper function to write to the CurrentOptions table with necessary attributes
def write_option(contractID: str, time: int, stock: str, strike: int, expiry: int, contractType: str, premium: int):
    dynamodb = boto3.resource('dynamodb')
    options_table = dynamodb.Table(
        'TradingBotStack-CurrentOptions572C21D7-F409JF5TX5JA')
    # Add attribute for strike price
    # ASK ABOUT CONTRACT ID

    options_table.put_item(
        Item={
            'contract_id': contractID,
            'timeStamp': time,
            'stockName': stock,
            'expiryDate': expiry,
            'strikePrice': strike,
            'putOrCall': contractType,
            'premiumFee': premium
        }
    )

    # add the option as a transaction to daily earnings
    earnings_table = dynamodb.Table(
        'TradingBotStack-DailyEarnings0DE49EE4-1J2QJVZ5RRHW7')

    earnings_table.put_item(
        Item={
            'activityId': str(uuid.uuid4()),
            'activityType': contractType,
            'activityAmount': premium,
            'contractId': contractID,
            'time': expiry,
        }
    )

    money_resp = earnings_table.get_item(
        Key={
            "activityId": "money"
        }
    )

    money_item = money_resp['Item']

    earnings_table.put_item(
        Item={
            'activityId': 'money',
            'amount': money_item["amount"] - premium
        }
    )

# Helper function to obtain volatility of last 24 hours for each corresponding stock
def get_stock_sentiment():
    logger.info('Getting latest headline sentiments')
    currentTimeInMillis = (int)(time.time()) * 1000
    logger.info(f'Curr Time: {currentTimeInMillis}')
    lowerTimeLimit = currentTimeInMillis - (86400000)
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(
        'TradingBotStack-SentimentData66B14031-1HRN5XCCEOVXH')
    response = table.scan(
        FilterExpression=Attr('timeStamp').gt(lowerTimeLimit)
    )
    items = response['Items']
    logger.info(f'Found these extreme companies: {items}')
    company_data = {}
    for i in items:
        company = i['company']
        isExtreme = i['isExtreme']
        extreme, neutral = company_data.get(company, (0, 0))
        if isExtreme:
            extreme += 1
        else:
            neutral += 1
        company_data[company] = (extreme, neutral)
    return company_data