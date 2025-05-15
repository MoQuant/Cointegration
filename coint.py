# Fetch the data from Financial Modeling Prep's API
def stock_data(ticker):
    key = ''
    url = f'https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?from=01-01-2024&apikey={key}'
    return url

# Set ETF tickers with several stocks
etf_tickers = [
    "SPY",  # SPDR S&P 500 ETF Trust
    "EEM",  # iShares MSCI Emerging Markets ETF
    "VTI",  # Vanguard Total Stock Market ETF
    "EFA",  # iShares MSCI EAFE ETF
    "BND",  # Vanguard Total Bond Market ETF
    "LQD",  # iShares iBoxx $ Investment Grade Corporate Bond ETF
    "VIG",   # Vanguard Dividend Appreciation ETF
    "IAU",  # iShares Gold Trust
    "VNQ",  # Vanguard Real Estate ETF
    "DBA",  # Invesco DB Agriculture Fund
    "BLK",
    "MSFT",
    "NVDA"
]

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller
import requests
import json
from scipy.stats import norm

# This allows the entire pandas dataframe to print
pd.set_option('display.max_colwidth', None)
pd.set_option('display.width', None)

# This function calculates the residuals of x and y
def Residuals(x, y):
    # Calculate mean of x and y
    mu_x = np.mean(x)
    mu_y = np.mean(y)

    # Calculate covariance and variance to compute beta
    cov = np.sum([(i - mu_x)*(j - mu_y) for i, j in zip(x, y)])
    vr = np.sum([pow(i - mu_x, 2) for i in x])
    beta = cov/vr
    
    # Compute alpha and calculate residuals
    alpha = mu_y - beta*mu_x
    return y - (alpha + beta*x)

# Generate Correlation Matrix based on returns
def Correlation(x):
    m, n = x.shape
    mu = (1/m)*np.ones(m).dot(x)
    
    # Calculate covariance matrix
    cov = (1/(m-1))*(x - mu).T.dot(x - mu)
    
    # Calculate correlation matrix
    sd = np.array([[i] for i in np.sqrt(np.diag(cov))])
    correl = cov / (sd.dot(sd.T))
    correl = correl.tolist()

    # Loop through correlation matrix and replace the diagonal correlations with an '-'
    for i in range(n):
        for j in range(n):
            if i == j:
                correl[i][j] = '-'
            else:
                # Compute the test statistic for significance for each correlation
                tstat = (correl[i][j]*np.sqrt(m - 2))/np.sqrt(1.0 - correl[i][j]**2)
                pvalue = 1.0 - norm.cdf(abs(tstat))

                # Add a star depending on the pvalue of the correlations alpha
                if pvalue <= 0.01:
                    asterik = "**"
                elif pvalue <= 0.05:
                    asterik = "*"
                else:
                    asterik = ""
                correl[i][j] = str(round(correl[i][j], 4)) + asterik

    # Return pandas dataframe with the correlation matrix in it
    return pd.DataFrame(correl, index=etf_tickers, columns=etf_tickers)

# Define a session for Requests to speed them up
session = requests.Session()

# Collect the stock and ETF price data from Financial Modeling Prep
close = []
for tick in etf_tickers:
    address = stock_data(tick)
    resp = session.get(address).json()
    stock_prices = pd.DataFrame(resp['historical'])['adjClose'].values[::-1].tolist()
    close.append(stock_prices)

N = len(etf_tickers)
close = np.array(close).T

# Calculate the returns for the stocks and ETF's
ror = close[1:]/close[:-1] - 1.0

# Generate and print the correlation matrix pandas dataframe
corr = Correlation(ror)
print("Correlation Matrix")
print(corr)

# Declare a new transpose close prices to compute residuals
closeT = close.T

matrix = []
for i in range(N):
    temp = []
    for j in range(N):
        if i == j:
            # Same stock so just put a '-'
            temp.append('-')
        else:
            # Compute residuals and pass them to the Augmented Dickey Fuller test in order to test if the pairs are cointegrated
            residuals = Residuals(closeT[i], closeT[j])
            result = adfuller(residuals)
            pvalue = result[1]

            # Instead of numerical values I just put Yes or No on whether the pairs are cointegrated and I add a star based on their alpha from the pvalue
            if pvalue <= 0.01:
                asterik = "**"
            elif pvalue <= 0.05:
                asterik = "*"
            else:
                asterik = ""
            if asterik == "":
                temp.append("No")
            else:
                temp.append("Yes" + asterik)
    matrix.append(temp)

# Build cointegration matrix
coint = pd.DataFrame(matrix, index=etf_tickers, columns=etf_tickers)

# Print cointegration matrix
print("\n")
print("Cointegration Matrix")
print(coint)
