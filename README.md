# Options Trading Bot with Cloud-Based Infrastructure

## Strategy
We develop a long straddle strategy. When long straddling options,
you purchase both long calls and long puts. This creates a V-shaped
payoff diagram that caps the loss at the premium one bought the options for.
No matter in which direction the underlying stock moves, up or down,
as long as there is enough swings in the stock price, we breakeven and profit.
We attempt to capture market reaction and potential volatility via sentiment
analysis of news headlines. At expiration, we exercise either the call or the
put depending on which one is in the money.

## Cloud
The strategy will be supported by a cloud-based infrastructure. The backend 
will be supported in the AWS Cloud. There are a few DynamoDB No-SQL databases 
that will store our positions in the market and previous data on options we plan
to buy and exercise. In order to handle live data, we periodically invoke
Lambda functions that process the data into the DynamoDB tables.

![image](https://user-images.githubusercontent.com/47924207/215703387-ce1d7334-100f-4011-9c22-d235042d8b6f.png)
