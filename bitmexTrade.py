#
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.append('official-http/python-swaggerpy')
from bravado.client import SwaggerClient
from bravado.requests_client import RequestsClient
from BitMEXAPIKeyAuthenticator import APIKeyAuthenticator
import json

sys.path.append('official-ws/python')
from bitmex_websocket import BitMEXWebsocket

import time
import json
import hashlib
import zlib
import base64
import threading

from random import *
import numpy as np
import logging



# My functions

def bit_compute(amount_usd, depth):
    if amount_usd > 0:
        tradeType = 'Buy'   # open long -- buy
        price = depth[-1]['askPrice']
        for i in range(len(depth)):
            if float(depth[i]['askSize'])>amount_usd:
                price = float(depth[i]['askPrice'])
                break
            else:
                amount_usd = amount_usd - depth[i]['askSize']
    else:
        tradeType = 'Sell'  # open short -- sell
        price = depth[-1]['bidPrice']
        for i in range(len(depth)):
            if depth[i]['bidSize']>-amount_usd:
                price = float(depth[i]['bidPrice'])
                break
            else:
                amount_usd = amount_usd + depth[i]['bidSize']

    return [float(price), tradeType]



# Settings for Bitmex

# For real:
HOST = "https://www.bitmex.com"
URL = "https://www.bitmex.com/api/v1"
API_KEY = 'XXX'
API_SECRET = 'XXX'

# #For test:
# HOST = "https://testnet.bitmex.com"
# URL = "https://testnet.bitmex.com/api/v1"
# API_KEY = 'XXX'
# API_SECRET = 'XXX'

SPEC_URI = HOST + "/api/explorer/swagger.json"


config = {
  'use_models': False,
  'validate_responses': False,
  'also_return_response': True,
}

bitMEX = SwaggerClient.from_url(
  SPEC_URI,
  config=config)

request_client = RequestsClient()
request_client.authenticator = APIKeyAuthenticator(HOST, API_KEY, API_SECRET)

bitMEXAuthenticated = SwaggerClient.from_url(
  SPEC_URI,
  config=config,
  http_client=request_client)


# BitMEX REST API
wsUSD = BitMEXWebsocket(endpoint=URL, symbol="XBTUSD", api_key=API_KEY, api_secret=API_SECRET)
wsZ17 = BitMEXWebsocket(endpoint=URL, symbol="XBTZ17", api_key=API_KEY, api_secret=API_SECRET)


# My Settings

amount_usd = 100            # positive
cont = int(amount_usd/100)
TradeMargin = 100

InitOrderNum = 153.0
OrderNum = InitOrderNum
GAP = 20.0                 # should larger than 10.0 -- cover the fee
BIAS = -70
FACTOR = 16
STD = 0.1

Nbuffer = 10000
Nlong = 1000
Ntrade = 10000


# Initialization

iter = 0
bit_stop = 0

Z17_buffer2 = np.zeros(Nbuffer)
Z17_buffer1 = np.zeros(Nbuffer)
diff_buffer1 = np.zeros(Nbuffer)
diff_buffer2 = np.zeros(Nbuffer)
long_buffer1 = np.zeros(Nlong)
long_buffer2 = np.zeros(Nlong)
trade_buffer_Z17 = np.zeros(Ntrade)
trade_buffer_XBT = np.zeros(Ntrade)

long_std = 0.0

logging.basicConfig(filename='myTrade.log', level=logging.INFO)
logging.info("############ Date ############: %s" % time.strftime("%Y:%m:%d:%H:%M:%S"))


# realtime market info.
depth25USD = wsUSD.market_depth()
depth25Z17 = wsZ17.market_depth()


# Begin Trading

while(1):
    iter = iter + 1
    
    [Z17_price1, Z17_tradeType1] = bit_compute(amount_usd, depth25Z17)                      # buy Z17
    Z17_buffer1[iter % Nbuffer] = Z17_price1
    std1 = np.std(Z17_buffer1)    
    [Z17_price2, Z17_tradeType2] = bit_compute(-amount_usd, depth25Z17)                     # sell Z17
    Z17_buffer2[iter % Nbuffer] = Z17_price2
    std2 = np.std(Z17_buffer2)
    
    [USD_price1, USD_tradeType1] = bit_compute(amount_usd, depth25USD)                      # buy USD
    [USD_price2, USD_tradeType2] = bit_compute(-amount_usd, depth25USD)                     # sell USD
    
    difference1 = float(Z17_price2) - USD_price1                                            # 1: buy USD, sell Z17
    diff_buffer1[iter % Nbuffer] = difference1
    difference2 = float(Z17_price1) - USD_price2                                            # 2: buy Z17, sell USD
    diff_buffer2[iter % Nbuffer] = difference2

    if iter < Nbuffer:
        continue

    room1 = (np.mean(diff_buffer1) - BIAS) / GAP
    room2 = (np.mean(diff_buffer2) - BIAS) / GAP
    OrderExp = (np.mean([diff_buffer1, diff_buffer2]) - BIAS) / GAP * FACTOR


    # Statistic

    if int(round(time.time() * 10)) % 10 == 0:  # record every 0.1 second, total 16.7 mins
        long_buffer1[iter % Nlong] = difference1
        long_buffer2[iter % Nlong] = difference2
        long_std1 = np.std(long_buffer1)
        long_std2 = np.std(long_buffer2)
        long_std = (long_std1 + long_std2)*0.5


    if long_std > STD:
        if int(round(time.time() * 1000000)) % 1000 == 0:
            print("Time: %s; OrderNum: %d TO %d; diff1: %f; diff2: %f; std_1: %f; std_2: %f; long_std: %f;"
            % (time.strftime("%H:%M:%S"), OrderNum, OrderExp, np.mean(diff_buffer1), np.mean(diff_buffer2), std1, std2, long_std))
        continue


    # when bit is decreasing faster OR increasing slower THAN Z17, buy bit (it will converge to Z17) and sell Z17 (it will converge to bit)
    if room1 - 0.5 >= OrderNum / FACTOR and std1 < 1/60.0 and std2 < 1/60.0 and np.mean(np.diff(Z17_buffer2)) >= 0:

        resUSD, USD_response = bitMEXAuthenticated.Order.Order_new(symbol='XBTUSD', side=USD_tradeType1, orderQty=abs(amount_usd), price=str(float(USD_price1)+TradeMargin)).result()
        resZ17, Z17_response = bitMEXAuthenticated.Order.Order_new(symbol='XBTZ17', side=Z17_tradeType2, orderQty=abs(amount_usd), price=str(float(Z17_price2)-TradeMargin)).result()
        OrderNum = OrderNum + 1

        trade_buffer_XBT[iter % Ntrade] = -resUSD['avgPx'] - 0.00075 * resUSD['avgPx']
        trade_buffer_Z17[iter % Ntrade] = resZ17['avgPx'] - 0.00075 * resZ17['avgPx']

        logging.info("Time: %s; XBT: %f; Z17: %f; diff: %f; profitExp: %f" % (time.strftime("%H:%M:%S"), -resUSD['avgPx'], resZ17['avgPx'], resZ17['avgPx'] - resUSD['avgPx'],
                                                                   np.sum(trade_buffer_XBT) + np.sum(trade_buffer_Z17)))

        
     # when bit is decreasing slower OR increasing faster THAN Z17, sell bit (it will converge to Z17) and buy Z17 (it will converge to bit)
    if room2 + 0.5 <= OrderNum / FACTOR and std1 < 1/60.0 and std2 < 1/60.0 and np.mean(np.diff(Z17_buffer1)) <= 0:
        
        resUSD, USD_response = bitMEXAuthenticated.Order.Order_new(symbol='XBTUSD', side=USD_tradeType2, orderQty=abs(amount_usd), price=str(float(USD_price2) - TradeMargin)).result()
        resZ17, Z17_response = bitMEXAuthenticated.Order.Order_new(symbol='XBTZ17', side=Z17_tradeType1, orderQty=abs(amount_usd), price=str(float(Z17_price1)+TradeMargin)).result()
        OrderNum = OrderNum - 1

        trade_buffer_XBT[iter % Ntrade] = resUSD['avgPx'] - 0.00075 * resUSD['avgPx']
        trade_buffer_Z17[iter % Ntrade] = -resZ17['avgPx'] - 0.00075 * resZ17['avgPx']

        logging.info("Time: %s; XBT: %f; Z17: %f; diff: %f; profitExp: %f" % (time.strftime("%H:%M:%S"), resUSD['avgPx'], -resZ17['avgPx'], resZ17['avgPx'] - resUSD['avgPx'],
                                                                   np.sum(trade_buffer_XBT) + np.sum(trade_buffer_Z17)))


    # Tracking the profit
    
    diffUP = (OrderNum/FACTOR + 0.5)*GAP + BIAS
    diffDown = (OrderNum/FACTOR - 0.5)*GAP + BIAS
    profitExp = np.sum(trade_buffer_XBT) + np.sum(trade_buffer_Z17) #*amount_usd*FACTOR/Z17_price2


    # Display

    if int(round(time.time() * 10)) % 10 == 0 and int(round(time.time() * 1000000)) % 10 == 0:
        print("Time: %s; OrderNum: %d To %d; diff1: %f; diff2: %f; Up: %f; Down: %f; std_1: %f; std_2: %f; long_std: %f; ProfitExp: %f"
              % (time.strftime("%H:%M:%S"), OrderNum, OrderExp, np.mean(diff_buffer1), np.mean(diff_buffer2), diffUP, diffDown, std1, std2, long_std, profitExp))





