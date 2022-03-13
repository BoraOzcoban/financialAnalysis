from yahooquery import Ticker
import yfinance as yfin
import pandas as pd
import pandas_datareader.data as web
import numpy as np
yfin.pdr_override()

start = pd.to_datetime("2018-01-01")
end = pd.to_datetime("2022-01-01")

# Importing required dataframes
ticker = "TSLA"
t = Ticker(ticker)
df = t.income_statement(frequency='q')
dt = t.cash_flow(frequency="q")
db = t.balance_sheet(frequency="q")
ds = t.valuation_measures
da = t.key_stats
dl = t.financial_data
do = t.summary_detail

# Getting required variables from the dataframes
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

# Using try-except when getting some variables because they are not available at the yahoo finance pages of some stocks
try:
    ebitda = df[['asOfDate', 'EBITDA']]
except:
    # Getting required variables for EBITDA calculation
    netIncome = df[['asOfDate', 'NetIncomeContinuousOperations']]
    interestExpense = df[['asOfDate', 'InterestExpense']]
    depreciationAmortization = dt[['asOfDate', 'DepreciationAndAmortization']]
    # Calculating EBITDA as Net Income + Tax Provision + Interest Expense + Depreciation and Amortization
    ebitda = netIncome["NetIncomeContinuousOperations"] + tax["TaxProvision"]\
        + interestExpense["InterestExpense"] + depreciationAmortization["DepreciationAndAmortization"]
try:
    ev = ds[['asOfDate', 'EnterpriseValue']]
except:
    # Calculating Enterprise Value as Market Cap + Total Debt - Cash and Cash Equivalents
    ev = marketCap["MarketCap"] + debt["TotalDebt"] - cash["CashAndCashEquivalents"]
try:
    evEbitda = ds[['asOfDate', 'EnterprisesValueEBITDARatio']]
except:
    evEbitda = ev / ebitda
try:
    evSales = ds[['asOfDate', 'EnterprisesValueRevenueRatio']]
except:
    # Getting the value of revenue in order to calculate EV/ Sales ratio
    revenue = df[['asOfDate', 'TotalRevenue']]
    evSales = ev / revenue["TotalRevenue"][-1]

########################################################################################################################
# Created a while loop, that repeats the code 5 times, in order to calculate the data from the last 5 Fiscal Reports
# Apart from deciding on when the loop will end,
# the index number also is used to compute the reports in an order from the latest to the earliest.
indexNumber = -1
while indexNumber >= -5:
    # Discounted Cash Flow Calculation
    try:
        # Unlevered Free Cash Flow = EBITDA - Tax Provision - Capital Expenditure - Change In Working Capital
        unleveredFcf = ebitda["EBITDA"][indexNumber] - tax["TaxProvision"][indexNumber] -\
                       capex["CapitalExpenditure"][indexNumber] - change_nwc["ChangeInWorkingCapital"][indexNumber]
        # Assigned the multiplier 1 for the calculation of Transaction Cash Flow.
        # Even though this calculation may seem unnecessary, the multiplier may change in the further updates.
        transactionCf = unleveredFcf * 1

        # Intrinsic Value = Enterprise Value + Cash and Cash Equivalents - Total Debt
        intrinsicValue = ev['EnterpriseValue'][indexNumber] + cash['CashAndCashEquivalents'][indexNumber] - debt['TotalDebt'][indexNumber]

        # Market Value = Market Cap + Total Debt - Cash and Cash Equivalents
        enterpriseValue = marketCap["MarketCap"][indexNumber] + debt["TotalDebt"][indexNumber] - cash["CashAndCashEquivalents"][indexNumber]

        # WACC Calculations
        # Debt/Cap Ratio = Total Debt / Total Capitalization
        debtToCap = debt["TotalDebt"][indexNumber] / totcap["TotalCapitalization"][indexNumber]
        # Equity/Cap Ratio = Total Equity Gross Minority Interest / Total Capitalization
        equityToCap = equity["TotalEquityGrossMinorityInterest"][indexNumber] / totcap["TotalCapitalization"][indexNumber]
        # Debt/Equity Ratio = Total Debt / Total Equity Gross Minority Interest
        debtToEquity = debtToCap = debt["TotalDebt"][indexNumber] / equity["TotalEquityGrossMinorityInterest"][indexNumber]

    # Same calculations, to be executed in case the data source lacked EBITDA and Enterprise Value information.
    # Thus, they had to be calculated through our code
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
    # If the data source has EV/Sales and EV/EBITDA data, use them. Else, use the values calculated through our code
    try:
        print(f"EV/Sales: {evSales['EnterprisesValueRevenueRatio'][indexNumber]}")
        print(f"EV/EBITDA: {evEbitda['EnterprisesValueEBITDARatio'][indexNumber]}")
    except:
        print(f"EV/Sales: {evSales[indexNumber]}")
        print(f"EV/EBITDA: {evEbitda[indexNumber]}")
    # Index number is decreased by 1 in order to ensure the loop ends in the right time,
    # meanwhile enabling a loop that computes reports from the latest to the earliest
    indexNumber = indexNumber - 1

# Discount Rate Calculation
# n serves the purpose of an index number and when it reaches to all the Cash Flow values, it breaks the loop
n = 0
totalCF = 0
while n < cashFlow["FreeCashFlow"].size - 1:
    # Adds all the Free Cash Flow values to the Total Cash Flow
    totalCF = totalCF + cashFlow["FreeCashFlow"][n]
    n = n + 1
# Discount Rate = (Total Cash Flow / Transaction Cash Flow) - 1
discountRate = (totalCF / transactionCf) - 1

# Terminal Value Calculation
# o serves the purpose of an index number and when it reaches to all the Cash Flow values, it breaks the loop
o = 0
perpetualGrowth = 0
while o < cashFlow["FreeCashFlow"].size - 1:
    # Adds " Free Cash Flow / ((1 + Discount Rate)^(index number + 1)) " to the perpetual growth on each iteration
    perpetualGrowth = perpetualGrowth + (cashFlow["FreeCashFlow"][o] / ((1 + discountRate) ** (o + 1)))
    o = o + 1
    try:
        # Terminal Value = (Perpetual Growth + Enterprise Value / EBITDA) / 2
        terminalValue = (perpetualGrowth + evEbitda["EnterprisesValueEBITDARatio"][-1]) / 2
    except:
        # Same calculations to be executed in case the data source lacked Enterprise Value / EBITDA ratio information.
        terminalValue = (perpetualGrowth + evEbitda[-1]) / 2
print(f"Terminal Value: {terminalValue}")

# Volatility
stock_df = web.DataReader(ticker, start, end)
stock_df["Normed Return"] = stock_df["Close"] / stock_df.iloc[0]["Close"]
#  Calculating the Standard Deviation of the stock's price using the Standard Deviation of the normalized return rates.
daily_std = np.std(stock_df["Normed Return"])
stock_df["Std"] = daily_std * 252 ** 0.5
# Getting the current price, 52 week low and high
close = do.get(ticker, {}).get("previousClose")
fiftyTwoWeekLow = do.get(ticker, {}).get("fiftyTwoWeekLow")
fiftyTwoWeekHigh = do.get(ticker, {}).get("fiftyTwoWeekHigh")

print(f"Beta(5Y Monthly): {beta}")
print(f"Volatility Score: {stock_df['Std'][0]}")
print(f"Previous Close: {close}")
print(f"52 Week Low: {fiftyTwoWeekLow}")
print(f"52 Week High: {fiftyTwoWeekHigh}")



