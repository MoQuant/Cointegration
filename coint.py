def stock_data(ticker):
    key = ''
    url = f'https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?from=01-01-2024&apikey={key}'
    return url

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

pd.set_option('display.max_colwidth', None)
pd.set_option('display.width', None)

def Residuals(x, y):
    mu_x = np.mean(x)
    mu_y = np.mean(y)
    cov = np.sum([(i - mu_x)*(j - mu_y) for i, j in zip(x, y)])
    vr = np.sum([pow(i - mu_x, 2) for i in x])
    beta = cov/vr
    alpha = mu_y - beta*mu_x
    return y - (alpha + beta*x)


def Correlation(x):
    m, n = x.shape
    mu = (1/m)*np.ones(m).dot(x)
    cov = (1/(m-1))*(x - mu).T.dot(x - mu)
    sd = np.array([[i] for i in np.sqrt(np.diag(cov))])
    correl = cov / (sd.dot(sd.T))
    correl = correl.tolist()
    for i in range(n):
        for j in range(n):
            if i == j:
                correl[i][j] = '-'
            else:
                tstat = (correl[i][j]*np.sqrt(m - 2))/np.sqrt(1.0 - correl[i][j]**2)
                pvalue = 1.0 - norm.cdf(abs(tstat))
                if pvalue <= 0.01:
                    asterik = "**"
                elif pvalue <= 0.05:
                    asterik = "*"
                else:
                    asterik = ""
                correl[i][j] = str(round(correl[i][j], 4)) + asterik
    return pd.DataFrame(correl, index=etf_tickers, columns=etf_tickers)

session = requests.Session()

close = []
for tick in etf_tickers:
    address = stock_data(tick)
    resp = session.get(address).json()
    stock_prices = pd.DataFrame(resp['historical'])['adjClose'].values[::-1].tolist()
    close.append(stock_prices)

N = len(etf_tickers)
close = np.array(close).T

ror = close[1:]/close[:-1] - 1.0

corr = Correlation(ror)
print("Correlation Matrix")
print(corr)

closeT = close.T

matrix = []
for i in range(N):
    temp = []
    for j in range(N):
        if i == j:
            temp.append('-')
        else:
            residuals = Residuals(closeT[i], closeT[j])
            result = adfuller(residuals)
            pvalue = result[1]
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

coint = pd.DataFrame(matrix, index=etf_tickers, columns=etf_tickers)

print("\n")
print("Cointegration Matrix")
print(coint)
