# AWS Options Trading Bot

We employ long straddling options. We buy both long calls and puts
when the underlying stock's sentiment based on latest news headlines is intense
(as this could imply volatility from market reaction) and exercise 
one of the two at expiration.

The trading simulation will be supported by a cloud-based infrastructure.
The backend will be supported in the AWS Cloud. 
There are a few DynamoDB No-SQL databases that will store our positions 
in the market and previous data on options we plan to buy and exercise. 
In order to handle live data, we periodically invoke
Lambda functions that process the data into the DynamoDB tables.

![image](https://user-images.githubusercontent.com/47924207/215703387-ce1d7334-100f-4011-9c22-d235042d8b6f.png)
