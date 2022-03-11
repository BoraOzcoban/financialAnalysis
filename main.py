from yahooquery import Ticker
import yfinance as yfin
import pandas as pd
import pandas_datareader.data as web
import numpy as np
yfin.pdr_override()

start = pd.to_datetime("2017-01-01")
end = pd.to_datetime("2021-01-01")

# Data Extraction
ticker = "TSLA"
t = Ticker(ticker)
df = t.income_statement(frequency='q')
dt = t.cash_flow(frequency="q")
db = t.balance_sheet(frequency="q")
ds = t.valuation_measures
da = t.key_stats
dl = t.financial_data
do = t.summary_detail

shares = da.get(ticker, {}).get("sharesOutstanding")
sharesF = da.get(ticker, {}).get("floatShares")
tax = df[['asOfDate', 'TaxProvision']]
capex = dt[['asOfDate', 'CapitalExpenditure']]
change_nwc = dt[['asOfDate', 'ChangeInWorkingCapital']]
cash = db[['asOfDate', 'CashAndCashEquivalents']]
debt = db[['asOfDate', 'TotalDebt']]
marketCap = ds[['asOfDate', 'MarketCap']]
cashFlow = dt[['asOfDate', 'FreeCashFlow']]
pe = ds[['asOfDate', 'PeRatio']]
debt = db[['asOfDate', 'TotalDebt']]
equity = db[['asOfDate', 'TotalEquityGrossMinorityInterest']]
totcap = db[['asOfDate', 'TotalCapitalization']]
taxRate = df[['asOfDate', 'TaxRateForCalcs']]
roe = dl.get(ticker, {}).get("returnOnEquity")
beta = do.get(ticker, {}).get("beta")


try:
    ebitda = df[['asOfDate', 'EBITDA']]
except:
    netIncome = df[['asOfDate', 'NetIncomeContinuousOperations']]
    interestExpense = df[['asOfDate', 'InterestExpense']]
    depreciationAmortization = dt[['asOfDate', 'DepreciationAndAmortization']]
    ebitda = netIncome["NetIncomeContinuousOperations"] + tax["TaxProvision"] + interestExpense["InterestExpense"] + depreciationAmortization["DepreciationAndAmortization"]
try:
    ev = ds[['asOfDate', 'EnterpriseValue']]
except:
    ev = marketCap["MarketCap"] + debt["TotalDebt"] - cash["CashAndCashEquivalents"]
try:
    evEbitda = ds[['asOfDate', 'EnterprisesValueEBITDARatio']]
except:
    evEbitda = ev / ebitda
try:
    evSales = ds[['asOfDate', 'EnterprisesValueRevenueRatio']]
except:
    revenue = df[['asOfDate', 'TotalRevenue']]
    evSales = ev / revenue["TotalRevenue"][-1]

########################################################################################################################
indexNumber = -1
while indexNumber >= -5:
    # Discounted Cash Flow Calculation
    try:
        unleveredFcf = ebitda["EBITDA"][indexNumber] - tax["TaxProvision"][indexNumber] -\
                       capex["CapitalExpenditure"][indexNumber] - change_nwc["ChangeInWorkingCapital"][indexNumber]
        transactionCf = unleveredFcf * 1

        # Intrinsic Value Calculation
        intrinsicValue = ev['EnterpriseValue'][indexNumber] + cash['CashAndCashEquivalents'][indexNumber] - debt['TotalDebt'][indexNumber]

        # Market Value Calculation
        enterpriseValue = marketCap["MarketCap"][indexNumber] + debt["TotalDebt"][indexNumber] - cash["CashAndCashEquivalents"][indexNumber]

        # WACC Calculations
        debtToCap = debt["TotalDebt"][indexNumber] / totcap["TotalCapitalization"][indexNumber]
        equityToCap = equity["TotalEquityGrossMinorityInterest"][indexNumber] / totcap["TotalCapitalization"][indexNumber]
        debtToEquity = debtToCap = debt["TotalDebt"][indexNumber] / equity["TotalEquityGrossMinorityInterest"][indexNumber]
    except:
        unleveredFcf = ebitda[indexNumber] - tax["TaxProvision"][indexNumber] -\
                       capex["CapitalExpenditure"][indexNumber] - change_nwc["ChangeInWorkingCapital"][indexNumber]
        transactionCf = unleveredFcf * 1

        # Intrinsic Value Calculation
        intrinsicValue = ev[indexNumber] + cash['CashAndCashEquivalents'][indexNumber] - debt['TotalDebt'][indexNumber]

        # Market Value Calculation
        enterpriseValue = marketCap["MarketCap"][indexNumber] + debt["TotalDebt"][indexNumber] - cash["CashAndCashEquivalents"][indexNumber]

        # WACC Calculations
        debtToCap = debt["TotalDebt"][indexNumber] / totcap["TotalCapitalization"][indexNumber]
        equityToCap = equity["TotalEquityGrossMinorityInterest"][indexNumber] / totcap["TotalCapitalization"][indexNumber]
        debtToEquity = debtToCap = debt["TotalDebt"][indexNumber] / equity["TotalEquityGrossMinorityInterest"][indexNumber]


    # Output
    print("------------------------")
    print(f"Intrinsic Value EV/Share: {intrinsicValue / shares}")
    print(f"Market Value EV/Share: {enterpriseValue / sharesF}")
    print(f"Upside: {intrinsicValue / shares - enterpriseValue / sharesF}")
    print(f"P/E: {pe['PeRatio'][indexNumber]}")
    try:
        print(f"EV/Sales: {evSales['EnterprisesValueRevenueRatio'][indexNumber]}")
        print(f"EV/EBITDA: {evEbitda['EnterprisesValueEBITDARatio'][indexNumber]}")
    except:
        print(f"EV/Sales: {evSales[indexNumber]}")
        print(f"EV/EBITDA: {evEbitda[indexNumber]}")
    indexNumber = indexNumber - 1

# Discount Rate Calculation
n = 0
while n < cashFlow["FreeCashFlow"].size - 1:
    totalCF = cashFlow["FreeCashFlow"][n]
    n = n + 1
discountRate = (totalCF / transactionCf) - 1

# Terminal Value Calculation
o = 0
perpetualGrowth = 0
while o < cashFlow["FreeCashFlow"].size - 1:
    perpetualGrowth = perpetualGrowth + (cashFlow["FreeCashFlow"][o] / ((1 + discountRate) ** (o + 1)))
    o = o + 1
    try:
        terminalValue = (perpetualGrowth + evEbitda["EnterprisesValueEBITDARatio"][-1]) / 2
    except:
        terminalValue = (perpetualGrowth + evEbitda[-1]) / 2
print(f"Terminal Value: {terminalValue}")

# Volatility
stock_df = web.DataReader(ticker, start, end)
stock_df["Normed Return"] = stock_df["Close"] / stock_df.iloc[0]["Close"]
daily_std = np.std(stock_df["Normed Return"])
stock_df["Std"] = daily_std * 252 ** 0.5
close = do.get(ticker, {}).get("previousClose")
fiftyTwoWeekLow = do.get(ticker, {}).get("fiftyTwoWeekLow")
fiftyTwoWeekHigh = do.get(ticker, {}).get("fiftyTwoWeekHigh")

print(f"Beta(5Y Monthly): {beta}")
print(f"Volatility Score: {stock_df['Std'][0]}")
print(f"Previous Close: {close}")
print(f"52 Week Low: {fiftyTwoWeekLow}")
print(f"52 Week High: {fiftyTwoWeekHigh}")



