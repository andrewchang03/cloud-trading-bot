import time
import boto3
from boto3.dynamodb.conditions import Key, Attr
import yfinance as yf
import uuid
from datetime import date

import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def calc_profit_handler(event, context):
    logger.info('Starting calc_profit lambda')
    dynamodb = boto3.resource('dynamodb')
    # TODO: after we calculate profit for all 11/18 contracts, we will need to change the table name
    # TODO: change the table name in strategy_lambda
    table = dynamodb.Table(
        'TradingBotStack-CurrentOptions572C21D7-F409JF5TX5JA')
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    logger.info('Date Today: ' + today_str)

    # response = table.query(
    #     # Add the name of the index you want to use in your query.
    #     IndexName="expiry_index",
    #     KeyConditionExpression=Key('expiry').eq(today_str),
    # )

    # TODO: we will comment this out and uncomment line 24 after we calculate 11/18 profits
    response = table.scan(
        FilterExpression=Attr('expiry').eq('2022-11-18')
    )
    items = response['Items']

    for entry in items:
        logger.info('Calculating profit for ' + entry['stockName'])
        ticker = yf.Ticker(entry['stockName'])
        stock_info = ticker.info
        close_price = stock_info['regularMarketPrice']
        call_type = entry["putOrCall"]

        # if profit is negative, just add an item with earnings = 0
        # if profit is positive,e add an item with earnings = profit
        earnings = 0

        if call_type == "PUT" and close_price < entry["strikePrice"]:
            earnings = entry["strikePrice"] - close_price
        elif call_type == "CALL" and close_price > entry["strikePrice"]:
            earnings = close_price - entry["strikePrice"]

        earnings = 100 * earnings  # to account for each option being 100 shares

        earnings_table = dynamodb.Table(
            'TradingBotStack-DailyEarnings0DE49EE4-1J2QJVZ5RRHW7')

        earnings_table.put_item(
            Item={
                'activityId': str(uuid.uuid4()),
                'activityType': "profit",
                'activityAmount': earnings,
                'contractId': entry["contractID"],
                # might also want to add a column for ticker and whether profit was from PUT or CALL
                'time': entry["expiry"],
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
                'amount': money_item["amount"] + earnings
            }
        )
