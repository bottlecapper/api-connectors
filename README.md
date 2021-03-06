BitMEX Market Bot for Intertemporal Arbitrage
=============================================

This is a trading bot for use with [BitMEX](https://www.bitmex.com).

It makes profits by trading between XBTUSD and XBTZ17: dynamically putting orders by learning the historical data curve, open long for the lower price market and short for the higher price market. 

The copyright belongs to the authors. You can modify and test with your own strategies. 


Getting Started
---------------
Refer to the [BitMEX Official Api-connectors](https://github.com/BitMEX/api-connectors).

Install the relative python packages.

Set your own API Key and Secret

Run it: `python bitmexTrade.py`

Operation Overview
------------------

This market maker works on the following principles:

* The bot tracks the last 16 mins data from `bidPrice` and `askPrice` of the XBTUSD and XBTZ17 markets to calculate the gap. 
* Based on parameters set by the user, the bot decides the amount for each order. 
* The user can specify an initial gap (through the BIAS variable) according to his/her experience. It means when the gap equals BIAS, there will be no order to put. New orders are generated when the gap becomes higher or lower. Positions will be closed when the gap converges to the BIAS. 
* To minimize the risks, the bot avoids trading when wild fluctuation happens. It keep tracking the historical data (e.g. 15 mins, which can be specified by the user) and calculates some statistical indicators. When the price curve returns flat, it starts trading again. 
* In the end of each interaton, the bot prints details of time, market gap, contracts traded, relative profit, etc.

Simplified Output
-----------------

The following is some of what you can expect when running this bot:

```
Time: 12:37:06; OrderNum: 157 To 162; diff1: 133.500000; diff2: 133.700000; Up: 136.250000; Down: 116.250000; std_1: 0.000000; std_2: 0.000000; long_std: 0.000000; ProfitExp: 521.961547
Time: 12:37:06; OrderNum: 157 To 162; diff1: 133.500000; diff2: 133.700000; Up: 136.250000; Down: 116.250000; std_1: 0.000000; std_2: 0.000000; long_std: 0.000000; ProfitExp: 521.961547
Time: 12:37:06; OrderNum: 157 To 162; diff1: 133.500000; diff2: 133.700000; Up: 136.250000; Down: 116.250000; std_1: 0.000000; std_2: 0.000000; long_std: 0.000000; ProfitExp: 521.961547
Time: 12:37:06; OrderNum: 157 To 162; diff1: 133.500000; diff2: 133.700000; Up: 136.250000; Down: 116.250000; std_1: 0.000000; std_2: 0.000000; long_std: 0.000000; ProfitExp: 521.961547
Time: 12:37:06; OrderNum: 157 To 162; diff1: 133.500000; diff2: 133.700000; Up: 136.250000; Down: 116.250000; std_1: 0.000000; std_2: 0.000000; long_std: 0.000000; ProfitExp: 521.961547

```

Compatibility
-------------

This module is compatible with only Python 2.

The user can modify to make it working on Python 3. 

Some helpful tips on Py2/3 compatibility: http://python-future.org/compatible_idioms.html
