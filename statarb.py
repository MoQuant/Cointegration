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

# Computes the ZScore off of the spread between two stocks to be used as a signal in the Statistical Arbitrage test
def StatSpread(x, y):
    diff = y - x
    mu = np.mean(diff)
    sd = np.std(diff)
    z = (diff - mu)/sd
    return z

# This function conducts a statistical arbitrage backtest based on the cointegrated and correlated pairs
def Backtest(ax, x, y, tA, tB, window=50, balance=10000):
    # Define positions and metrics in order to simultaneously go long and short
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

    # Runs the simulated backtest
    for i in range(window, len(x)):
        # Store x and y rolling windows
        hold_x = x[i-window:i]
        hold_y = y[i-window:i]

        # Fetches latest ZScore for spread to be traded on
        xspread = StatSpread(hold_x, hold_y)
        spread = xspread[-1]

        # If Stock pair A is short and pair B is long, and the spread z-score is greater than 2.33, this closes the position
        if spread > 2.33 and positionA == 'short' and positionB == 'long':
            oldbalance = balance
            
            # Updates the balance
            balance = balance + longY*(1 - transaction_fee) - shortX*(1 + transaction_fee)*(1 - leverage_rate)

            # Resets positions
            positionA = 'neutral'
            positionB = 'neutral'

            # Computes cumulative return for the simulation
            prod_return *= (balance/oldbalance)
            xmoney.append(i)
            ymoney.append(prod_return - 1.0)

        # This was originally an error, 2.33 was the original value but it is supposed to be -2.33 but this closes the position
        # if the zscore < -2.33 and stock pair A = long and pair B = short
        if spread < -2.33 and positionA == 'long' and positionB == 'short':
            oldbalance = balance

            # updates the balance
            balance = balance - shortY*(1 + transaction_fee)*(1 - leverage_rate) + longX*(1 - transaction_fee)

            # Resets positions
            positionA = 'neutral'
            positionB = 'neutral'

            # Computes the cumulative return for the simulation
            prod_return *= (balance/oldbalance)
            xmoney.append(i)
            ymoney.append(prod_return - 1.0)

        # Error fixed, spread is now less than -2.33 instead of the original being 2.33
        if spread < -2.33 and positionA == 'neutral' and positionB == 'neutral':
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

    # Plots the cumulative rate of return
    ax.plot(xmoney, ymoney, color='green')
    ax.set_title(f"Pairs: [{tA} with {tB}]")
    ax.set_xlabel("Time")
    ax.set_ylabel("Price")
    
# Picks the pairs with the most cointegration and correlation
TICKERS = (("VIG","DBA"),("NVDA","IAU"),("MSFT","DBA"),("MSFT","NVDA"))

#tickerA = "VIG"
#tickerB = "DBA"

# Generate four 2D plots to graph the returns
fig = plt.figure(figsize=(7, 7))
ax = [fig.add_subplot(u) for u in (221, 222, 223, 224)]

# Runs the backtest for import inputted stocks
for ii, (tickerA, tickerB) in enumerate(TICKERS):
    # Declare a request session for faster GET requests
    session = requests.Session()

    # Pull the stock/etf pairs
    etfA = session.get(stock_data(tickerA)).json()
    etfB = session.get(stock_data(tickerB)).json()

    # Extract close values
    stockA = pd.DataFrame(etfA['historical'])['adjClose'].values[::-1]
    stockB = pd.DataFrame(etfB['historical'])['adjClose'].values[::-1]

    # Run the backtest and plot the results
    Backtest(ax[ii], stockA, stockB, tickerA, tickerB)

plt.show()
