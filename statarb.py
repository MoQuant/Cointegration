def stock_data(ticker):
    key = ''
    url = f'https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?from=01-01-2024&apikey={key}'
    return url

import numpy as np
import pandas as pd
import requests
import json 
import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams['figure.autolayout'] = True

def StatSpread(x, y):
    diff = y - x
    mu = np.mean(diff)
    sd = np.std(diff)
    z = (diff - mu)/sd
    return z

def Backtest(ax, x, y, tA, tB, window=50, balance=10000):
    positionA = 'neutral'
    positionB = 'neutral'
    leverage_rate = 0.02
    transaction_fee = 0.005
    longX = 0
    longY = 0
    shortX = 0
    shortY = 0
    xmoney = []
    ymoney = []
    oldbalance = 0
    prod_return = 1
    for i in range(window, len(x)):
        
        hold_x = x[i-window:i]
        hold_y = y[i-window:i]
        xspread = StatSpread(hold_x, hold_y)
        spread = xspread[-1]

        if spread > 2.33 and positionA == 'short' and positionB == 'long':
            oldbalance = balance
            balance = balance + longY*(1 - transaction_fee) - shortX*(1 + transaction_fee)*(1 - leverage_rate)
            positionA = 'neutral'
            positionB = 'neutral'
            prod_return *= (balance/oldbalance)
            xmoney.append(i)
            ymoney.append(prod_return - 1.0)

        if spread < 2.33 and positionA == 'long' and positionB == 'short':
            oldbalance = balance
            balance = balance - shortY*(1 + transaction_fee)*(1 - leverage_rate) + longX*(1 - transaction_fee)
            positionA = 'neutral'
            positionB = 'neutral'
            prod_return *= (balance/oldbalance)
            xmoney.append(i)
            ymoney.append(prod_return - 1.0)

        if spread < 2.33 and positionA == 'neutral' and positionB == 'neutral':
            # Go Long in Y
            # Go Short in X
            longY = 0.5*balance/y[i]
            shortX = 0.5*balance/x[i]
            balance = balance - longY*(1 + transaction_fee) + shortX*(1 - transaction_fee)
            positionA = 'short'
            positionB = 'long'

        if spread > 2.33 and positionA == 'neutral' and positionB == 'neutral':
            # Go Short in Y
            # Go Long in X
            longX = 0.5*balance/x[i]
            shortY = 0.5*balance/y[i]
            balance = balance + shortY*(1 - transaction_fee) - longX*(1 + transaction_fee)
            positionA = 'long'
            positionB = 'short'

        message = f'Stock A Price: {x[i]} | Stock B Price: {y[i]} | {positionA} | {positionB} | Balance = {balance}'
        print(message)

    ax.plot(xmoney, ymoney, color='green')
    ax.set_title(f"Pairs: [{tA} with {tB}]")
    ax.set_xlabel("Time")
    ax.set_ylabel("Price")
    

TICKERS = (("VIG","DBA"),("NVDA","IAU"),("MSFT","DBA"),("MSFT","NVDA"))

#tickerA = "VIG"
#tickerB = "DBA"
fig = plt.figure(figsize=(7, 7))
ax = [fig.add_subplot(u) for u in (221, 222, 223, 224)]

for ii, (tickerA, tickerB) in enumerate(TICKERS):

    session = requests.Session()

    etfA = session.get(stock_data(tickerA)).json()
    etfB = session.get(stock_data(tickerB)).json()

    stockA = pd.DataFrame(etfA['historical'])['adjClose'].values[::-1]
    stockB = pd.DataFrame(etfB['historical'])['adjClose'].values[::-1]

    Backtest(ax[ii], stockA, stockB, tickerA, tickerB)

plt.show()
